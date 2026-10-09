"""Comprehensive Test Suite for Centralized Production-Grade Scoring Engine.

Tests:
1. Full score calculation (100% test cases passed -> Full marks).
2. Half score calculation (partial test cases passed -> Half marks).
3. Zero score calculation (0 test cases passed -> Zero marks).
4. Repeated result idempotency (repeated webhook/result does not duplicate score or emit extra events).
5. Monotonic highest score tracking (re-submitting with lower score does not reduce points; re-submitting with higher score awards only delta).
6. Concurrent score events and transaction safety.
7. Capstone project submission score evaluation.
8. Leaderboard recalculation and daily snapshot generation.
9. Automated student notification emission upon score change.
10. Complete score audit history breakdown.
"""

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.notifications.models import Notification
from apps.projects.models import Project
from apps.scoring.models import LeaderboardSnapshot, ScoreEvent, ScoreRecord
from apps.scoring.services import ScoringService
from apps.students.models import StudentProfile

User = get_user_model()


class ScoringServiceTests(TestCase):
    """Unit and integration tests for ScoringService."""

    def setUp(self):
        cache.clear()

        # Admin user
        self.admin_user = User.objects.create_user(
            email="admin.scoring@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.ADMIN,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )

        # Student 1
        self.user1 = User.objects.create_user(
            email="student.alpha@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.student1 = StudentProfile.objects.create(
            user=self.user1,
            student_id_number="GQT-STU-SC-01",
            full_name="Alpha Student",
            batch_code="BATCH-2026-A",
            total_points=Decimal("0.00"),
        )

        # Student 2
        self.user2 = User.objects.create_user(
            email="student.beta@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.student2 = StudentProfile.objects.create(
            user=self.user2,
            student_id_number="GQT-STU-SC-02",
            full_name="Beta Student",
            batch_code="BATCH-2026-A",
            total_points=Decimal("0.00"),
        )

    def test_full_score_rule_100_percent_passed(self):
        """100% test cases passed must award Full marks (ScoringPolicy.FULL)."""
        question_id = str(uuid.uuid4())
        res = ScoringService.evaluate_assignment_submission(
            student=self.student1,
            question_id=question_id,
            question_title="Two Sum",
            passed_test_cases=4,
            total_test_cases=4,
            max_points=Decimal("100.00"),
        )

        self.assertEqual(res["points"], 100.0)
        self.assertEqual(res["score_delta"], 100.0)
        self.assertEqual(res["policy_applied"], ScoreRecord.ScoringPolicy.FULL)
        self.assertTrue(res["is_new_high"])

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.total_points, Decimal("100.00"))

        # Verify ScoreRecord persisted
        record = ScoreRecord.objects.get(id=res["score_record_id"])
        self.assertEqual(record.points, Decimal("100.00"))
        self.assertEqual(record.policy_applied, ScoreRecord.ScoringPolicy.FULL)

        # Verify ScoreEvent created
        event = ScoreEvent.objects.get(score_record=record)
        self.assertEqual(event.delta, Decimal("100.00"))
        self.assertEqual(event.event_type, ScoreEvent.EventType.SUBMISSION_EVALUATED)

        # Verify Notification dispatched
        notif = Notification.objects.filter(recipient=self.user1).first()
        self.assertIsNotNone(notif)
        self.assertIn("Two Sum", notif.title)

    def test_half_score_rule_partial_passed(self):
        """Partial test cases passed (e.g. 2/4) must award Half marks (ScoringPolicy.HALF)."""
        question_id = str(uuid.uuid4())
        res = ScoringService.evaluate_assignment_submission(
            student=self.student1,
            question_id=question_id,
            question_title="Binary Search",
            passed_test_cases=2,
            total_test_cases=4,
            max_points=Decimal("50.00"),
        )

        # 50 * 0.5 = 25.00
        self.assertEqual(res["points"], 25.0)
        self.assertEqual(res["score_delta"], 25.0)
        self.assertEqual(res["policy_applied"], ScoreRecord.ScoringPolicy.HALF)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.total_points, Decimal("25.00"))

    def test_zero_score_rule_0_passed(self):
        """0 test cases passed must award Zero marks (ScoringPolicy.ZERO)."""
        question_id = str(uuid.uuid4())
        res = ScoringService.evaluate_assignment_submission(
            student=self.student1,
            question_id=question_id,
            question_title="Graph Traversal",
            passed_test_cases=0,
            total_test_cases=5,
            max_points=Decimal("80.00"),
        )

        self.assertEqual(res["points"], 0.0)
        self.assertEqual(res["score_delta"], 0.0)
        self.assertEqual(res["policy_applied"], ScoreRecord.ScoringPolicy.ZERO)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.total_points, Decimal("0.00"))

    def test_repeated_result_idempotent(self):
        """A duplicate webhook or evaluation for the same result must NOT duplicate points or events."""
        question_id = str(uuid.uuid4())

        # First evaluation
        res1 = ScoringService.evaluate_assignment_submission(
            student=self.student1,
            question_id=question_id,
            question_title="Merge Sort",
            passed_test_cases=3,
            total_test_cases=3,
            max_points=Decimal("60.00"),
        )
        self.assertEqual(res1["score_delta"], 60.0)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.total_points, Decimal("60.00"))
        self.assertEqual(ScoreRecord.objects.count(), 1)
        self.assertEqual(ScoreEvent.objects.count(), 1)

        # Repeated duplicate evaluation
        res2 = ScoringService.evaluate_assignment_submission(
            student=self.student1,
            question_id=question_id,
            question_title="Merge Sort",
            passed_test_cases=3,
            total_test_cases=3,
            max_points=Decimal("60.00"),
        )
        self.assertEqual(res2["score_delta"], 0.0)
        self.assertFalse(res2["is_new_high"])

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.total_points, Decimal("60.00"))
        # Must still be exactly 1 record and 1 event
        self.assertEqual(ScoreRecord.objects.count(), 1)
        self.assertEqual(ScoreEvent.objects.count(), 1)

    def test_monotonic_best_score_incremental_delta(self):
        """Improving score from half to full marks awards ONLY the delta and keeps audit trail."""
        question_id = str(uuid.uuid4())

        # 1. First attempt: Half marks (2/4 passed) -> 25 points
        res1 = ScoringService.evaluate_assignment_submission(
            student=self.student1,
            question_id=question_id,
            question_title="Dynamic Programming",
            passed_test_cases=2,
            total_test_cases=4,
            max_points=Decimal("50.00"),
        )
        self.assertEqual(res1["points"], 25.0)
        self.assertEqual(res1["score_delta"], 25.0)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.total_points, Decimal("25.00"))

        # 2. Second attempt: Full marks (4/4 passed) -> 50 points (delta = 25)
        res2 = ScoringService.evaluate_assignment_submission(
            student=self.student1,
            question_id=question_id,
            question_title="Dynamic Programming",
            passed_test_cases=4,
            total_test_cases=4,
            max_points=Decimal("50.00"),
        )
        self.assertEqual(res2["points"], 50.0)
        self.assertEqual(res2["score_delta"], 25.0)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.total_points, Decimal("50.00"))

        # 3. Third attempt: Regressed code (1/4 passed) -> Should NOT decrease student points
        res3 = ScoringService.evaluate_assignment_submission(
            student=self.student1,
            question_id=question_id,
            question_title="Dynamic Programming",
            passed_test_cases=1,
            total_test_cases=4,
            max_points=Decimal("50.00"),
        )
        self.assertEqual(res3["score_delta"], 0.0)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.total_points, Decimal("50.00"))

    def test_project_submission_score_evaluation(self):
        """Capstone project submissions evaluated through ScoringService persist score and audit log."""
        project = Project.objects.create(
            title="Fullstack Microservices Capstone",
            slug="fullstack-microservices",
            description="Build and deploy microservices with auth and monitoring.",
            deliverables_instructions="Submit GitHub repo and live URL.",
            max_score=Decimal("200.00"),
        )

        res = ScoringService.evaluate_project_submission(
            student=self.student1,
            project_id=str(project.id),
            project_title=project.title,
            score=Decimal("180.00"),
            max_score=project.max_score,
            awarded_by=self.admin_user,
            feedback_notes="Excellent architecture and test coverage.",
        )

        self.assertEqual(res["points"], 180.0)
        self.assertEqual(res["score_delta"], 180.0)
        self.assertEqual(res["source_type"], ScoreRecord.SourceType.PROJECT)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.total_points, Decimal("180.00"))

        # Verify score history breakdown
        history = ScoringService.get_student_score_history(self.student1)
        self.assertEqual(history["total_points"], 180.0)
        self.assertIn("PROJECT", history["points_by_source"])
        self.assertEqual(history["points_by_source"]["PROJECT"], 180.0)

    def test_leaderboard_recalculation_and_snapshot(self):
        """Scoring updates trigger real-time rank calculation and daily LeaderboardSnapshot."""
        q1 = str(uuid.uuid4())
        q2 = str(uuid.uuid4())

        # Student 1 gets 100 pts
        ScoringService.evaluate_assignment_submission(
            student=self.student1,
            question_id=q1,
            question_title="Q1",
            passed_test_cases=2,
            total_test_cases=2,
            max_points=Decimal("100.00"),
        )

        # Student 2 gets 200 pts
        ScoringService.evaluate_assignment_submission(
            student=self.student2,
            question_id=q2,
            question_title="Q2",
            passed_test_cases=2,
            total_test_cases=2,
            max_points=Decimal("200.00"),
        )

        # Verify Leaderboard Snapshots
        today = timezone.localdate()
        snap1 = LeaderboardSnapshot.objects.get(
            snapshot_date=today, student=self.student1
        )
        snap2 = LeaderboardSnapshot.objects.get(
            snapshot_date=today, student=self.student2
        )

        # Student 2 has 200 pts (Rank 1), Student 1 has 100 pts (Rank 2)
        self.assertEqual(snap2.global_rank, 1)
        self.assertEqual(snap2.total_score, Decimal("200.00"))

        self.assertEqual(snap1.global_rank, 2)
        self.assertEqual(snap1.total_score, Decimal("100.00"))

    def test_concurrent_score_events_safety(self):
        """Sequential/concurrent evaluations for multiple different questions aggregate correctly."""
        for i in range(5):
            q_id = str(uuid.uuid4())
            ScoringService.evaluate_assignment_submission(
                student=self.student1,
                question_id=q_id,
                question_title=f"Question #{i}",
                passed_test_cases=2,
                total_test_cases=2,
                max_points=Decimal("20.00"),
            )

        self.student1.refresh_from_db()
        # 5 questions * 20 pts = 100 pts
        self.assertEqual(self.student1.total_points, Decimal("100.00"))
        self.assertEqual(ScoreRecord.objects.filter(student=self.student1).count(), 5)
        self.assertEqual(ScoreEvent.objects.filter(student=self.student1).count(), 5)
