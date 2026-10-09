"""Comprehensive test suite for Achievement Badges, Milestone Rules, and Certificate Generation."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.certificates.models import Certificate
from apps.certificates.services import AchievementService, CertificateService
from apps.certificates.tasks import _generate_certificate_pdf_worker
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.notifications.models import Notification
from apps.students.models import StudentProfile

User = get_user_model()


class CertificatesAndAchievementsApiTests(APITestCase):
    """Test suite covering badges, milestone evaluation, certificate issuance, async PDF generation, and verification."""

    def setUp(self):
        cache.clear()

        # Admin User
        self.admin_user = User.objects.create_superuser(
            email="admin.cert@gqt.local", password="AdminPassword123!"
        )

        # Student A
        self.user_a = User.objects.create_user(
            email="alice.cert@gqt.local",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
        )
        self.student_a = StudentProfile.objects.create(
            user=self.user_a,
            student_id_number="GQT-STU-CERT-1",
            full_name="Alice Architect",
            batch_code="BATCH-2026-CERT",
            total_points=Decimal("150.00"),
            current_streak_days=5,
            highest_streak_days=5,
        )

        # Student B
        self.user_b = User.objects.create_user(
            email="bob.cert@gqt.local",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
        )
        self.student_b = StudentProfile.objects.create(
            user=self.user_b,
            student_id_number="GQT-STU-CERT-2",
            full_name="Bob Beginner",
            batch_code="BATCH-2026-CERT",
            total_points=Decimal("10.00"),
            current_streak_days=1,
            highest_streak_days=1,
        )

        # Course with 2 sequential modules
        self.course = Course.objects.create(
            title="Mastering Django & System Design",
            slug="mastering-django-sys-design",
            description="Deep dive course",
            is_published=True,
        )
        self.mod1 = Module.objects.create(
            course=self.course,
            title="Architecture Fundamentals",
            slug="arch-fundamentals",
            order_index=1,
            is_published=True,
        )
        self.mod2 = Module.objects.create(
            course=self.course,
            title="Production Deployment",
            slug="prod-deployment",
            order_index=2,
            is_published=True,
        )

        self.enrollment_a = CourseEnrollment.objects.create(
            student=self.student_a,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )

    def test_milestone_evaluation_and_badge_unlocking(self):
        """Milestone rules evaluate student telemetry and unlock badges idempotently."""
        # Complete 1 module for Student A
        StudentModuleProgress.objects.create(
            student=self.student_a,
            module=self.mod1,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
            completed_at=timezone.now(),
        )

        # Evaluate achievements
        unlocked = AchievementService.evaluate_achievements(self.student_a)
        unlocked_slugs = [sb.badge.slug for sb in unlocked]

        # Student A has completed 1 module, points=150, streak=5
        # Expected unlocked badges: 'first-step' (mod=1), 'century-scorer' (pts=100), 'streak-starter' (streak=3)
        self.assertIn("first-step", unlocked_slugs)
        self.assertIn("century-scorer", unlocked_slugs)
        self.assertIn("streak-starter", unlocked_slugs)

        # Verify in-app notifications generated
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user_a,
                notification_type=Notification.NotificationType.ACHIEVEMENT,
                title__contains="Achievement Unlocked",
            ).exists()
        )

        # Idempotent re-evaluation: Should not award duplicates
        re_unlocked = AchievementService.evaluate_achievements(self.student_a)
        self.assertEqual(len(re_unlocked), 0)

    def test_student_badges_list_api(self):
        """Student retrieves all badges with unlock status and progress percentages."""
        self.client.force_authenticate(user=self.user_a)
        res = self.client.get("/api/v1/students/achievements/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        badges = res.json()["data"]["badges"]
        self.assertTrue(len(badges) >= 5)

        first_step = next(b for b in badges if b["slug"] == "first-step")
        self.assertEqual(first_step["criteria_type"], "MODULE_COMPLETION")
        self.assertIn("progress_percentage", first_step)

    def test_certificate_issuance_upon_course_completion(self):
        """Complete course curriculum generates a verified certificate; duplicates are prevented."""
        # Complete both modules in the course for Student A
        StudentModuleProgress.objects.create(
            student=self.student_a,
            module=self.mod1,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
        )
        StudentModuleProgress.objects.create(
            student=self.student_a,
            module=self.mod2,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
        )

        # 1. Issue certificate
        cert1 = CertificateService.issue_certificate_if_eligible(
            self.student_a, self.course
        )
        self.assertIsNotNone(cert1.certificate_id)
        self.assertTrue(cert1.certificate_id.startswith("GQT-CERT-"))
        self.assertEqual(cert1.student_name, self.student_a.full_name)
        self.assertEqual(cert1.course_title, self.course.title)

        # 2. Repeated trigger returns same certificate (duplicate prevention)
        cert2 = CertificateService.issue_certificate_if_eligible(
            self.student_a, self.course
        )
        self.assertEqual(cert1.id, cert2.id)
        self.assertEqual(
            Certificate.objects.filter(
                student=self.student_a, course=self.course
            ).count(),
            1,
        )

    def test_ineligible_student_certificate_issuance_blocked(self):
        """Student who has not completed all modules cannot receive a certificate."""
        # Student B has completed 0 modules
        with self.assertRaises(DjangoValidationError):
            CertificateService.issue_certificate_if_eligible(
                self.student_b, self.course
            )

    def test_async_pdf_document_generation(self):
        """Async worker generates a valid PDF document with reportlab."""
        cert = Certificate.objects.create(
            certificate_id="GQT-CERT-2026-TESTPDF",
            student=self.student_a,
            course=self.course,
            student_name=self.student_a.full_name,
            course_title=self.course.title,
            verification_hash="hash1234567890abcdef",
        )

        success = _generate_certificate_pdf_worker(str(cert.id))
        self.assertTrue(success)

        cert.refresh_from_db()
        self.assertTrue(bool(cert.pdf_file))
        self.assertTrue(cert.pdf_file.name.endswith(".pdf"))

    def test_student_certificate_list_and_download_authorization(self):
        """Owner student and admin can download certificate; unrelated student is denied."""
        cert = Certificate.objects.create(
            certificate_id="GQT-CERT-2026-AUTHCHECK",
            student=self.student_a,
            course=self.course,
            student_name=self.student_a.full_name,
            course_title=self.course.title,
            verification_hash="hash9876543210fedcba",
        )

        # 1. Student A lists their certificates
        self.client.force_authenticate(user=self.user_a)
        list_res = self.client.get("/api/v1/students/certificates/")
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.json()["data"]["certificates"]), 1)

        # 2. Student A downloads their certificate
        down_a = self.client.get(f"/api/v1/students/certificates/{cert.id}/download/")
        self.assertEqual(down_a.status_code, status.HTTP_200_OK)
        self.assertEqual(down_a["Content-Type"], "application/pdf")

        # 3. Admin can download
        self.client.force_authenticate(user=self.admin_user)
        down_admin = self.client.get(
            f"/api/v1/students/certificates/{cert.id}/download/"
        )
        self.assertEqual(down_admin.status_code, status.HTTP_200_OK)

        # 4. Student B is denied
        self.client.force_authenticate(user=self.user_b)
        down_b = self.client.get(f"/api/v1/students/certificates/{cert.id}/download/")
        self.assertEqual(down_b.status_code, status.HTTP_403_FORBIDDEN)

    def test_public_certificate_verification(self):
        """Public verification endpoint verifies valid certificate and flags revoked ones."""
        cert = Certificate.objects.create(
            certificate_id="GQT-CERT-2026-PUBLIC-VERIFY",
            student=self.student_a,
            course=self.course,
            student_name=self.student_a.full_name,
            course_title=self.course.title,
            verification_hash="abc123verificationhash456789",
        )

        # 1. Public verification by certificate_id (No auth required)
        self.client.logout()
        res = self.client.get(f"/api/v1/students/verify/{cert.certificate_id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()["data"]
        self.assertTrue(data["is_valid"])
        self.assertEqual(data["student_name"], self.student_a.full_name)
        self.assertEqual(data["course_title"], self.course.title)

        # 2. Public verification by hash
        res_hash = self.client.get(f"/api/v1/students/verify/{cert.verification_hash}/")
        self.assertEqual(res_hash.status_code, status.HTTP_200_OK)
        self.assertTrue(res_hash.json()["data"]["is_valid"])

        # 3. Invalid identifier gives 404
        res_invalid = self.client.get("/api/v1/students/verify/INVALID-IDENTIFIER/")
        self.assertEqual(res_invalid.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_certificate_management_and_revocation(self):
        """Admin can list all certificates and revoke fraudulent ones."""
        cert = Certificate.objects.create(
            certificate_id="GQT-CERT-2026-REVOKETEST",
            student=self.student_a,
            course=self.course,
            student_name=self.student_a.full_name,
            course_title=self.course.title,
            verification_hash="revokablehash123",
        )

        self.client.force_authenticate(user=self.admin_user)

        # 1. Admin lists certificates
        list_res = self.client.get("/api/v1/admin/certificates/")
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(list_res.json()["data"]["certificates"]) >= 1)

        # 2. Admin revokes certificate
        revoke_res = self.client.post(
            f"/api/v1/admin/certificates/{cert.id}/revoke/",
            {"reason": "Academic integrity review"},
            format="json",
        )
        self.assertEqual(revoke_res.status_code, status.HTTP_200_OK)
        self.assertTrue(revoke_res.json()["data"]["is_revoked"])

        # 3. Public verification now reflects revoked status
        self.client.logout()
        verify_res = self.client.get(f"/api/v1/students/verify/{cert.certificate_id}/")
        self.assertEqual(verify_res.status_code, status.HTTP_400_BAD_REQUEST)
        err_data = verify_res.json()["error"]
        self.assertEqual(err_data["code"], "CERTIFICATE_REVOKED")
        self.assertFalse(err_data["details"]["is_valid"])
        self.assertEqual(err_data["details"]["status"], "REVOKED")
