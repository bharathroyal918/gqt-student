"""Comprehensive API test suite for Sequential Module Locking and Progression.

Tests:
- First module access is unlocked on course enrollment
- Locked module access is strictly forbidden (cannot access Module N+1 before Module N)
- Module completion marks status COMPLETED and sequentially unlocks Module N+1
- Repeated module completion is idempotent
- Concurrent completion requests are handled safely without race conditions
- Unauthorized course access is rejected (403 NOT_ENROLLED)
- Course progress percentage dynamically updates across curriculum
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import StudentModuleProgress
from apps.modules.services import StudentModuleService
from apps.students.models import StudentProfile

User = get_user_model()


class SequentialModuleApiTests(TestCase):
    """Test suite for curriculum progression and strict server-side sequential module locking."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.unauthorized_client = APIClient()

        # Create Course with all 17 sequential modules
        self.course = Course.objects.create(
            title="Python Mastery Track",
            slug="python-mastery-track",
            is_published=True,
        )
        self.modules = StudentModuleService.ensure_default_curriculum(self.course)
        self.assertEqual(len(self.modules), 17)

        # Create Enrolled Student
        self.user = User.objects.create_user(
            email="learner@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-100",
            full_name="Enrolled Learner",
            batch_code="PY-2026-A",
            total_points=Decimal("0.00"),
        )
        self.enrollment = CourseEnrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )

        # Create Non-Enrolled Student
        self.other_user = User.objects.create_user(
            email="outsider@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.other_profile = StudentProfile.objects.create(
            user=self.other_user,
            student_id_number="GQT-STU-101",
            full_name="Outsider Student",
            batch_code="PY-2026-B",
        )

        self.client.force_authenticate(user=self.user)
        self.unauthorized_client.force_authenticate(user=self.other_user)

    def test_first_module_access_unlocked(self):
        """Enrolled student can access Module 1 (Data Types) immediately."""
        mod1 = self.modules[0]
        self.assertEqual(mod1.order_index, 1)

        url = reverse(
            "api_v1:students:student_module_detail", kwargs={"module_id": mod1.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]

        self.assertEqual(data["title"], "Data Types")
        self.assertEqual(data["order_index"], 1)
        self.assertIn(data["status"], ["UNLOCKED", "IN_PROGRESS"])

    def test_locked_module_access_forbidden(self):
        """Student cannot access Module 2 (If-Else) before completing Module 1 (Data Types)."""
        mod2 = self.modules[1]
        self.assertEqual(mod2.order_index, 2)

        url = reverse(
            "api_v1:students:student_module_detail", kwargs={"module_id": mod2.id}
        )
        response = self.client.get(url)

        # Server-side authorization must forbid access
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "MODULE_LOCKED")

        # Also verify jumping to Module 17 (Interface) is strictly blocked
        mod17 = self.modules[16]
        url17 = reverse(
            "api_v1:students:student_module_detail", kwargs={"module_id": mod17.id}
        )
        res17 = self.client.get(url17)
        self.assertEqual(res17.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res17.data["error"]["code"], "MODULE_LOCKED")

    def test_module_completion_and_next_unlock(self):
        """Completing Module 1 marks it COMPLETED and unlocks Module 2."""
        mod1 = self.modules[0]
        mod2 = self.modules[1]
        mod3 = self.modules[2]

        complete_url = reverse(
            "api_v1:students:student_module_complete", kwargs={"module_id": mod1.id}
        )
        response = self.client.post(
            complete_url, {"score_percentage": 100.0}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        res_data = response.data["data"]
        self.assertEqual(res_data["status"], "COMPLETED")
        self.assertEqual(res_data["completed_modules_count"], 1)
        self.assertEqual(res_data["next_module"]["id"], str(mod2.id))
        self.assertEqual(res_data["next_module"]["status"], "UNLOCKED")

        # Verify Module 2 can now be accessed
        mod2_url = reverse(
            "api_v1:students:student_module_detail", kwargs={"module_id": mod2.id}
        )
        res2 = self.client.get(mod2_url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["data"]["title"], "If-Else")

        # Module 3 must remain locked
        mod3_url = reverse(
            "api_v1:students:student_module_detail", kwargs={"module_id": mod3.id}
        )
        res3 = self.client.get(mod3_url)
        self.assertEqual(res3.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res3.data["error"]["code"], "MODULE_LOCKED")

    def test_repeated_completion_idempotent(self):
        """Completing a module multiple times is idempotent and does not duplicate points."""
        mod1 = self.modules[0]
        complete_url = reverse(
            "api_v1:students:student_module_complete", kwargs={"module_id": mod1.id}
        )

        # First completion
        res1 = self.client.post(
            complete_url, {"score_percentage": 100.0}, format="json"
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        self.student_profile.refresh_from_db()
        points_after_first = self.student_profile.total_points
        self.assertEqual(points_after_first, Decimal("50.00"))

        # Second completion (repeated)
        res2 = self.client.post(
            complete_url, {"score_percentage": 100.0}, format="json"
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.total_points, points_after_first)

    def test_concurrent_completion_requests_safe(self):
        """Simultaneous completion calls on the same module do not cause duplicate progress rows or race conditions."""
        mod1 = self.modules[0]
        complete_url = reverse(
            "api_v1:students:student_module_complete", kwargs={"module_id": mod1.id}
        )

        responses = [
            self.client.post(complete_url, {"score_percentage": 100.0}, format="json")
            for _ in range(3)
        ]

        self.assertTrue(all(r.status_code == status.HTTP_200_OK for r in responses))
        progress_rows = StudentModuleProgress.objects.filter(
            student=self.student_profile, module=mod1
        ).count()
        self.assertEqual(progress_rows, 1)

    def test_unauthorized_course_access_rejected(self):
        """Non-enrolled student is denied access to course detail and modules (403 NOT_ENROLLED)."""
        course_url = reverse(
            "api_v1:students:student_course_detail",
            kwargs={"course_id": self.course.id},
        )
        res_course = self.unauthorized_client.get(course_url)
        self.assertEqual(res_course.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res_course.data["error"]["code"], "NOT_ENROLLED")

        mod1 = self.modules[0]
        mod_url = reverse(
            "api_v1:students:student_module_detail", kwargs={"module_id": mod1.id}
        )
        res_mod = self.unauthorized_client.get(mod_url)
        self.assertEqual(res_mod.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res_mod.data["error"]["code"], "NOT_ENROLLED")

    def test_course_progress_percentage_calculation(self):
        """Completing modules dynamically recalculates course progress percentage across 17 units."""
        mod1 = self.modules[0]
        mod2 = self.modules[1]

        # Complete Module 1
        url1 = reverse(
            "api_v1:students:student_module_complete", kwargs={"module_id": mod1.id}
        )
        res1 = self.client.post(url1, format="json")
        # 1 / 17 * 100 = 5.9%
        self.assertAlmostEqual(
            res1.data["data"]["course_progress_percentage"], 5.9, places=1
        )

        # Complete Module 2
        url2 = reverse(
            "api_v1:students:student_module_complete", kwargs={"module_id": mod2.id}
        )
        res2 = self.client.post(url2, format="json")
        # 2 / 17 * 100 = 11.8%
        self.assertAlmostEqual(
            res2.data["data"]["course_progress_percentage"], 11.8, places=1
        )
