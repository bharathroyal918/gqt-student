"""Tests for SEC-07: Placement student eligibility and IsApprovedStudent enforcement."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.placements.models import PlacementDrive
from apps.students.models import StudentProfile

User = get_user_model()


class PlacementStudentEligibilityTests(TestCase):
    """SEC-07: Verify IsApprovedStudent is enforced on all student placement endpoints."""

    def setUp(self):
        self.client = APIClient()

        # Approved Student
        self.approved_user = User.objects.create_user(
            email="approved.student@gqt.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.approved_profile = StudentProfile.objects.create(
            user=self.approved_user,
            student_id_number="GQT-STU-APP",
            full_name="Approved Student",
        )

        # Pending Activation Student
        self.pending_user = User.objects.create_user(
            email="pending.student@gqt.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.PENDING_ACTIVATION,
        )
        self.pending_profile = StudentProfile.objects.create(
            user=self.pending_user,
            student_id_number="GQT-STU-PEN",
            full_name="Pending Student",
        )

        # Suspended Student
        self.suspended_user = User.objects.create_user(
            email="suspended.student@gqt.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.SUSPENDED,
        )
        self.suspended_profile = StudentProfile.objects.create(
            user=self.suspended_user,
            student_id_number="GQT-STU-SUS",
            full_name="Suspended Student",
        )

        # Inactive Student
        self.inactive_user = User.objects.create_user(
            email="inactive.student@gqt.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=False,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.inactive_profile = StudentProfile.objects.create(
            user=self.inactive_user,
            student_id_number="GQT-STU-INA",
            full_name="Inactive Student",
        )

        # Placement Drive
        self.drive = PlacementDrive.objects.create(
            company_name="MegaCorp",
            role="Software Engineer",
            skills="Django, React",
            location="Bengaluru",
            stipend_or_ctc="10 LPA",
            job_description="Top engineering role",
            status=PlacementDrive.DriveStatus.ONGOING,
            application_deadline=timezone.now() + timezone.timedelta(days=30),
        )

        # URLs
        self.list_url = reverse("api_v1:student_placement_drives_list")
        self.detail_url = reverse(
            "api_v1:student_placement_drive_detail", kwargs={"drive_id": self.drive.id}
        )
        self.apply_url = reverse(
            "api_v1:student_placement_apply", kwargs={"drive_id": self.drive.id}
        )
        self.my_apps_url = reverse("api_v1:student_my_placement_applications")

    def test_anonymous_access_denied_on_all_endpoints(self):
        """Anonymous callers must be rejected with HTTP 401."""
        for url in [self.list_url, self.detail_url, self.my_apps_url]:
            res = self.client.get(url)
            assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_approved_student_allowed_on_listing_and_detail(self):
        """Approved student with ACTIVE onboarding_status can access drives."""
        self.client.force_authenticate(user=self.approved_user)
        list_res = self.client.get(self.list_url)
        assert list_res.status_code == status.HTTP_200_OK

        detail_res = self.client.get(self.detail_url)
        assert detail_res.status_code == status.HTTP_200_OK

        my_res = self.client.get(self.my_apps_url)
        assert my_res.status_code == status.HTTP_200_OK

    def test_pending_student_rejected_on_all_placement_endpoints(self):
        """Pending student must be rejected with HTTP 403 Forbidden."""
        self.client.force_authenticate(user=self.pending_user)
        for url in [self.list_url, self.detail_url, self.my_apps_url]:
            res = self.client.get(url)
            assert res.status_code == status.HTTP_403_FORBIDDEN

        apply_res = self.client.post(self.apply_url, {"resume_url": "https://drive.google.com/test"})
        assert apply_res.status_code == status.HTTP_403_FORBIDDEN

    def test_suspended_student_rejected_on_all_placement_endpoints(self):
        """Suspended student must be rejected with HTTP 403 Forbidden."""
        self.client.force_authenticate(user=self.suspended_user)
        for url in [self.list_url, self.detail_url, self.my_apps_url]:
            res = self.client.get(url)
            assert res.status_code == status.HTTP_403_FORBIDDEN

        apply_res = self.client.post(self.apply_url, {"resume_url": "https://drive.google.com/test"})
        assert apply_res.status_code == status.HTTP_403_FORBIDDEN

    def test_inactive_student_rejected_on_all_placement_endpoints(self):
        """Deactivated student must be rejected."""
        self.client.force_authenticate(user=self.inactive_user)
        for url in [self.list_url, self.detail_url, self.my_apps_url]:
            res = self.client.get(url)
            assert res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
