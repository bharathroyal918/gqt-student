from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.analytics.models import ActivityEvent, DailyStudentAnalytics
from apps.students.models import StudentProfile

User = get_user_model()


class AnalyticsModelTests(TestCase):
    """Test suite for ActivityEvent and DailyStudentAnalytics models."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="analytics.user@gqt.local", password="Password123!"
        )
        self.student = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-009",
            full_name="Analytics Student",
            batch_code="BATCH-2026-A",
        )

    def test_activity_event_logging(self):
        event = ActivityEvent.objects.create(
            user=self.user,
            event_name="code_submission_attempt",
            entity_type="CodingQuestion",
            entity_id="q-101",
            properties={"language": "python", "status": "ACCEPTED"},
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.properties["language"], "python")

    def test_daily_student_analytics_uniqueness(self):
        today = date.today()
        DailyStudentAnalytics.objects.create(
            student=self.student,
            date=today,
            submissions_count=5,
            questions_solved_count=3,
            time_spent_minutes=45,
            score_earned=Decimal("150.00"),
        )
        with self.assertRaises(IntegrityError):
            DailyStudentAnalytics.objects.create(
                student=self.student,
                date=today,
                submissions_count=2,
            )
