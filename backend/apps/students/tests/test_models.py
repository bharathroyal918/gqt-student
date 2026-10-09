from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.students.models import StudentProfile

User = get_user_model()


class StudentProfileModelTests(TestCase):
    """Test suite for StudentProfile model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="stu.prof@gqt.local", password="Password123!"
        )

    def test_student_profile_creation(self):
        profile = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-010",
            full_name="Student Profile User",
            batch_code="BATCH-2026-B",
            current_streak_days=3,
            highest_streak_days=5,
            total_points=Decimal("250.00"),
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.batch_code, "BATCH-2026-B")
        self.assertEqual(str(profile), "Student Profile User (GQT-STU-010)")

    def test_unique_student_id_number(self):
        StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-010",
            full_name="First Student",
            batch_code="BATCH-2026-B",
        )
        other_user = User.objects.create_user(
            email="other.stu@gqt.local", password="Password123!"
        )
        with self.assertRaises(IntegrityError):
            StudentProfile.objects.create(
                user=other_user,
                student_id_number="GQT-STU-010",
                full_name="Duplicate ID Student",
                batch_code="BATCH-2026-B",
            )

    def test_streak_auto_update_on_clean(self):
        profile = StudentProfile(
            user=self.user,
            student_id_number="GQT-STU-011",
            full_name="Streak Student",
            batch_code="BATCH-2026-B",
            current_streak_days=10,
            highest_streak_days=4,
        )
        profile.clean()
        self.assertEqual(profile.highest_streak_days, 10)
