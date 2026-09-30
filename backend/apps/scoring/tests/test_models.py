import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.scoring.models import LeaderboardSnapshot, ScoreEvent, ScoreRecord
from apps.students.models import StudentProfile

User = get_user_model()


class ScoringModelTests(TestCase):
    """Test suite for ScoreRecord, ScoreEvent, and LeaderboardSnapshot."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="scoring.student@gqt.local", password="Password123!"
        )
        self.student = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-004",
            full_name="Scoring Student",
            batch_code="BATCH-2026-A",
        )
        self.submission_id = uuid.uuid4()

    def test_score_record_creation_and_uniqueness(self):
        record = ScoreRecord.objects.create(
            student=self.student,
            source_type=ScoreRecord.SourceType.ASSIGNMENT,
            source_id=self.submission_id,
            points=Decimal("100.00"),
            policy_applied=ScoreRecord.ScoringPolicy.FULL,
        )
        self.assertEqual(record.points, Decimal("100.00"))

        # Cannot award duplicate score for the exact same source
        with self.assertRaises(IntegrityError):
            ScoreRecord.objects.create(
                student=self.student,
                source_type=ScoreRecord.SourceType.ASSIGNMENT,
                source_id=self.submission_id,
                points=Decimal("50.00"),
            )

    def test_score_event_audit(self):
        record = ScoreRecord.objects.create(
            student=self.student,
            source_type=ScoreRecord.SourceType.STREAK_BONUS,
            source_id=uuid.uuid4(),
            points=Decimal("25.00"),
        )
        event = ScoreEvent.objects.create(
            student=self.student,
            score_record=record,
            event_type=ScoreEvent.EventType.STREAK_BONUS_ADDED,
            delta=Decimal("25.00"),
            reason="7-day coding streak achieved",
        )
        self.assertEqual(event.student, self.student)
        self.assertEqual(event.delta, Decimal("25.00"))

    def test_leaderboard_snapshot_uniqueness(self):
        today = date.today()
        LeaderboardSnapshot.objects.create(
            snapshot_date=today,
            student=self.student,
            batch_code="BATCH-2026-A",
            total_score=Decimal("450.00"),
            global_rank=1,
            batch_rank=1,
            streak_days=5,
        )
        with self.assertRaises(IntegrityError):
            LeaderboardSnapshot.objects.create(
                snapshot_date=today,
                student=self.student,
                batch_code="BATCH-2026-A",
                total_score=Decimal("450.00"),
                global_rank=1,
                batch_rank=1,
            )
