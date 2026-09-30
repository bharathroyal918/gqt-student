from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.certificates.models import Badge, Certificate, StudentBadge
from apps.courses.models import Course
from apps.students.models import StudentProfile

User = get_user_model()


class CertificateModelTests(TestCase):
    """Test suite for Badges and Course Completion Certificates."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="cert.student@gqt.local", password="Password123!"
        )
        self.student = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-008",
            full_name="Certificate Student",
            batch_code="BATCH-2026-A",
        )
        self.course = Course.objects.create(title="Python Professional", slug="python-professional")
        self.badge = Badge.objects.create(
            slug="7-day-streak",
            name="Consistency Champion",
            description="Awarded for 7 consecutive days of coding",
            icon_url="https://cdn.gqt.local/badges/streak-7.svg",
            criteria_type=Badge.CriteriaType.STREAK_MILESTONE,
            criteria_threshold=7,
        )

    def test_student_badge_uniqueness(self):
        StudentBadge.objects.create(student=self.student, badge=self.badge)
        with self.assertRaises(IntegrityError):
            StudentBadge.objects.create(student=self.student, badge=self.badge)

    def test_certificate_issuance_and_uniqueness(self):
        cert = Certificate.objects.create(
            certificate_id="GQT-CERT-2026-0001",
            student=self.student,
            course=self.course,
            verification_hash="a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
        )
        self.assertEqual(cert.student, self.student)
        self.assertEqual(cert.course, self.course)

        # Unique student-course certificate constraint
        with self.assertRaises(IntegrityError):
            Certificate.objects.create(
                certificate_id="GQT-CERT-2026-0002",
                student=self.student,
                course=self.course,
                verification_hash="b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890a1",
            )
