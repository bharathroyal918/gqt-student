"""Centralized Production-Grade Scoring Engine for GQT Student Portal.

All score-changing events across coding assignments and project submissions
MUST pass through this service to guarantee data integrity, transaction safety,
idempotency, automated notifications, and real-time leaderboard recalculations.
"""

from decimal import Decimal
from typing import Any, Dict, Optional
from django.core.cache import cache
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import AuditLog, User
from apps.common.exceptions import DomainException
from apps.notifications.models import Notification
from apps.scoring.models import LeaderboardSnapshot, ScoreEvent, ScoreRecord
from apps.students.models import StudentProfile


class ScoringService:
    """Centralized authority for score calculation, event emission, points persistence, and ranking."""

    LEADERBOARD_CACHE_KEY_PREFIX = "student_leaderboard"

    @classmethod
    def calculate_assignment_marks(
        cls, passed_test_cases: int, total_test_cases: int, max_points: Decimal
    ) -> tuple[Decimal, str]:
        """Calculates assignment score strictly following institution policy:
        - 100% test cases passed: Full marks (ScoringPolicy.FULL)
        - Partial test cases passed: Half marks (ScoringPolicy.HALF)
        - 0 test cases passed: Zero marks (ScoringPolicy.ZERO)
        """
        if total_test_cases <= 0:
            return Decimal("0.00"), ScoreRecord.ScoringPolicy.ZERO

        if passed_test_cases == total_test_cases:
            return max_points, ScoreRecord.ScoringPolicy.FULL
        elif passed_test_cases > 0:
            half_pts = (max_points * Decimal("0.5")).quantize(Decimal("0.01"))
            return half_pts, ScoreRecord.ScoringPolicy.HALF
        else:
            return Decimal("0.00"), ScoreRecord.ScoringPolicy.ZERO

    @classmethod
    @transaction.atomic
    def process_score_change(
        cls,
        student: StudentProfile,
        source_type: str,
        source_id: str,
        new_points: Decimal,
        policy_applied: str,
        reason: str,
        awarded_by: Optional[User] = None,
        event_type: str = ScoreEvent.EventType.SUBMISSION_EVALUATED,
        notification_title: Optional[str] = None,
        notification_body: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Atomically processes any score-altering event across the portal.
        
        Guarantees:
        1. Row-level locks (select_for_update) to prevent concurrency races.
        2. Idempotency: Duplicate calls for the same score produce 0 delta.
        3. Monotonic highest-score policy: Keeps best score per source, awards delta only.
        4. Persistent ScoreRecord & ScoreEvent emission.
        5. Aggregate StudentProfile points update.
        6. Real-time leaderboard cache invalidation and recalculation.
        7. Student notification dispatch.
        """
        # Lock student profile for update
        locked_student = StudentProfile.objects.select_for_update().get(id=student.id)

        # Lock or fetch existing score record
        score_record = ScoreRecord.objects.select_for_update().filter(
            student=locked_student,
            source_type=source_type,
            source_id=source_id,
        ).first()

        prev_points = score_record.points if score_record else Decimal("0.00")
        score_delta = Decimal("0.00")
        is_new_high = False

        if not score_record:
            # First submission/evaluation for this source
            score_delta = new_points
            is_new_high = True
            score_record = ScoreRecord.objects.create(
                student=locked_student,
                source_type=source_type,
                source_id=source_id,
                points=new_points,
                policy_applied=policy_applied,
                awarded_by=awarded_by,
            )
        elif new_points > prev_points:
            # Score improved! Award delta
            score_delta = new_points - prev_points
            is_new_high = True
            score_record.points = new_points
            score_record.policy_applied = policy_applied
            score_record.awarded_by = awarded_by
            score_record.save(update_fields=["points", "policy_applied", "awarded_by", "updated_at"])
        else:
            # Idempotent or lower score -> do not decrement points or duplicate
            score_delta = Decimal("0.00")
            is_new_high = False

        # If points changed, update aggregate total and emit event
        if score_delta > Decimal("0.00"):
            locked_student.total_points += score_delta
            locked_student.save(update_fields=["total_points", "updated_at"])

            # Record Audit Event
            ScoreEvent.objects.create(
                student=locked_student,
                score_record=score_record,
                event_type=event_type,
                delta=score_delta,
                reason=reason,
                created_by=awarded_by,
            )

            # Recalculate Leaderboard & Update Snapshot
            cls._update_leaderboard(locked_student)

            # Dispatch Student Notification
            title = notification_title or f"Score Awarded: +{score_delta} Points!"
            body = notification_body or f"You earned {score_delta} points for {reason}. Total score is now {locked_student.total_points}."
            Notification.objects.create(
                recipient=locked_student.user,
                title=title,
                body=body,
                notification_type=Notification.NotificationType.SUBMISSION_GRADED,
            )

        return {
            "score_record_id": str(score_record.id),
            "source_type": source_type,
            "source_id": str(source_id),
            "points": float(score_record.points),
            "score_delta": float(score_delta),
            "is_new_high": is_new_high,
            "student_total_points": float(locked_student.total_points),
            "policy_applied": score_record.policy_applied,
        }

    @classmethod
    @transaction.atomic
    def evaluate_assignment_submission(
        cls,
        student: StudentProfile,
        question_id: str,
        question_title: str,
        passed_test_cases: int,
        total_test_cases: int,
        max_points: Decimal,
        awarded_by: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Calculates and applies marks for an algorithmic coding assignment submission."""
        awarded_score, policy = cls.calculate_assignment_marks(
            passed_test_cases=passed_test_cases,
            total_test_cases=total_test_cases,
            max_points=max_points,
        )

        reason = f"Coding Problem: {question_title} ({passed_test_cases}/{total_test_cases} tests passed - {policy})"
        return cls.process_score_change(
            student=student,
            source_type=ScoreRecord.SourceType.ASSIGNMENT,
            source_id=question_id,
            new_points=awarded_score,
            policy_applied=policy,
            reason=reason,
            awarded_by=awarded_by,
            event_type=ScoreEvent.EventType.SUBMISSION_EVALUATED,
            notification_title=f"Assessment Graded: {question_title}",
            notification_body=f"Your solution for '{question_title}' passed {passed_test_cases} of {total_test_cases} tests. Points awarded: {awarded_score}.",
        )

    @classmethod
    @transaction.atomic
    def evaluate_project_submission(
        cls,
        student: StudentProfile,
        project_id: str,
        project_title: str,
        score: Decimal,
        max_score: Decimal,
        awarded_by: Optional[User] = None,
        feedback_notes: str = "",
    ) -> Dict[str, Any]:
        """Evaluates and persists score for a capstone project submission."""
        if score > max_score:
            score = max_score
        elif score < Decimal("0.00"):
            score = Decimal("0.00")

        policy = ScoreRecord.ScoringPolicy.FULL if score == max_score else ScoreRecord.ScoringPolicy.MANUAL
        reason = f"Capstone Project: {project_title} ({score}/{max_score} pts)"

        return cls.process_score_change(
            student=student,
            source_type=ScoreRecord.SourceType.PROJECT,
            source_id=project_id,
            new_points=score,
            policy_applied=policy,
            reason=reason,
            awarded_by=awarded_by,
            event_type=ScoreEvent.EventType.SUBMISSION_EVALUATED,
            notification_title=f"Project Graded: {project_title}",
            notification_body=f"Your project '{project_title}' has been evaluated. Score: {score}/{max_score} points.",
        )

    @classmethod
    def _update_leaderboard(cls, student: StudentProfile) -> Dict[str, int]:
        """Calculates real-time global and batch rank for student, and refreshes daily leaderboard snapshots."""
        today = timezone.localdate()
        
        all_students = list(StudentProfile.objects.order_by("-total_points", "created_at"))
        student_ranks = {}
        
        for rank, s in enumerate(all_students, start=1):
            student_ranks[s.id] = rank
            b_rank = 1
            if s.batch_code:
                b_rank = sum(
                    1 for other in all_students
                    if other.batch_code == s.batch_code and other.total_points > s.total_points
                ) + 1

            LeaderboardSnapshot.objects.update_or_create(
                snapshot_date=today,
                student=s,
                defaults={
                    "batch_code": s.batch_code or "DEFAULT",
                    "total_score": s.total_points,
                    "global_rank": rank,
                    "batch_rank": b_rank,
                    "streak_days": s.current_streak_days,
                },
            )

        # Invalidate leaderboard caches via domain LeaderboardService
        from apps.leaderboard.services import LeaderboardService
        LeaderboardService.invalidate_cache()
        cache.delete(f"student_dashboard:{student.id}")

        return {
            "global_rank": student_ranks.get(student.id, 1),
            "batch_rank": 1,
        }

    @classmethod
    def get_student_score_history(cls, student: StudentProfile) -> Dict[str, Any]:
        """Returns student score breakdown, total points, and recent score events."""
        records = ScoreRecord.objects.filter(student=student).order_by("-awarded_at")
        events = ScoreEvent.objects.filter(student=student).order_by("-created_at")[:20]

        total_pts = student.total_points
        by_source = {}
        for r in records:
            src = r.source_type
            by_source[src] = by_source.get(src, Decimal("0.00")) + r.points

        return {
            "student_id": str(student.id),
            "total_points": float(total_pts),
            "points_by_source": {k: float(v) for k, v in by_source.items()},
            "records_count": records.count(),
            "recent_events": [
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "delta": float(e.delta),
                    "reason": e.reason,
                    "created_at": e.created_at.isoformat(),
                }
                for e in events
            ],
        }
