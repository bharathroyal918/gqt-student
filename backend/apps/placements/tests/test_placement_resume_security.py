"""Tests for SEC-01: Placement resume download IDOR and authorization controls."""

import tempfile
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import TPOProfile
from apps.placements.models import PlacementApplication, PlacementDrive
from apps.students.models import College, StudentProfile

User = get_user_model()


class PlacementResumeDownloadSecurityTests(TestCase):
    """Test suite verifying authorization controls on PlacementResumeDownloadView."""

    def setUp(self):
        self.client = APIClient()

        # Colleges
        self.college_a = College.objects.create(
            name="Alpha Engineering College",
            code="ALPHA",
            city="Bengaluru",
            state="Karnataka",
            is_active=True,
        )
        self.college_b = College.objects.create(
            name="Beta Institute of Technology",
            code="BETA",
            city="Mysuru",
            state="Karnataka",
            is_active=True,
        )

        # Drive
        self.drive = PlacementDrive.objects.create(
            company_name="Tech Corp",
            role="Full Stack Developer",
            skills="Python, React",
            location="Bengaluru",
            stipend_or_ctc="8 LPA",
            job_description="Great role",
            status=PlacementDrive.DriveStatus.ONGOING,
            application_deadline=timezone.now() + timezone.timedelta(days=30),
        )

        # Student A (College A)
        self.user_student_a = User.objects.create_user(
            email="student_a@alpha.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.profile_student_a = StudentProfile.objects.create(
            user=self.user_student_a,
            student_id_number="GQT-STU-001",
            full_name="Student Alpha",
            college=self.college_a,
            college_name=self.college_a.name,
        )

        # Student B (College B)
        self.user_student_b = User.objects.create_user(
            email="student_b@beta.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.profile_student_b = StudentProfile.objects.create(
            user=self.user_student_b,
            student_id_number="GQT-STU-002",
            full_name="Student Beta",
            college=self.college_b,
            college_name=self.college_b.name,
        )

        # Admin
        self.user_admin = User.objects.create_user(
            email="admin@gqt.edu",
            password="Password123!",
            role=User.RoleChoices.ADMIN,
            is_staff=True,
            is_active=True,
        )

        # TPO Alpha (College A)
        self.user_tpo_alpha = User.objects.create_user(
            email="tpo@alpha.edu",
            password="Password123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        self.tpo_profile_alpha = TPOProfile.objects.create(
            user=self.user_tpo_alpha,
            college=self.college_a,
            full_name="TPO Alpha",
            is_active=True,
        )

        # TPO Beta (College B)
        self.user_tpo_beta = User.objects.create_user(
            email="tpo@beta.edu",
            password="Password123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        self.tpo_profile_beta = TPOProfile.objects.create(
            user=self.user_tpo_beta,
            college=self.college_b,
            full_name="TPO Beta",
            is_active=True,
        )

        # Dummy resume file
        self.dummy_resume = SimpleUploadedFile(
            "student_a_resume.pdf",
            b"%PDF-1.4 test resume content",
            content_type="application/pdf",
        )

        # Application for Student A
        self.app_a = PlacementApplication.objects.create(
            drive=self.drive,
            student=self.profile_student_a,
            student_name="Student Alpha",
            student_id_number="GQT-STU-001",
            email=self.user_student_a.email,
            college_name=self.college_a.name,
            resume_file=self.dummy_resume,
            resume_filename="student_a_resume.pdf",
        )

        self.download_url = reverse(
            "api_v1:placement_resume_download", kwargs={"application_id": self.app_a.id}
        )

    def test_anonymous_access_is_rejected(self):
        """Anonymous callers must receive HTTP 401 Unauthorized."""
        response = self.client.get(self.download_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthorized_student_access_is_rejected(self):
        """Student B must not be able to download Student A's resume (HTTP 403)."""
        self.client.force_authenticate(user=self.user_student_b)
        response = self.client.get(self.download_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("error", {}).get("code") == "PERMISSION_DENIED"

    def test_owner_student_can_download_resume(self):
        """Student A can successfully download their own resume."""
        self.client.force_authenticate(user=self.user_student_a)
        response = self.client.get(self.download_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get("Content-Type") == "application/pdf"

    def test_admin_can_download_resume(self):
        """Admin can download any student application resume."""
        self.client.force_authenticate(user=self.user_admin)
        response = self.client.get(self.download_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get("Content-Type") == "application/pdf"

    def test_authorized_college_tpo_can_download_resume(self):
        """TPO assigned to the student's college can download the resume."""
        self.client.force_authenticate(user=self.user_tpo_alpha)
        response = self.client.get(self.download_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get("Content-Type") == "application/pdf"

    def test_cross_college_tpo_access_is_rejected(self):
        """TPO from College B must be rejected when accessing College A student resume."""
        self.client.force_authenticate(user=self.user_tpo_beta)
        response = self.client.get(self.download_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("error", {}).get("code") == "PERMISSION_DENIED"

    def test_inactive_tpo_access_is_rejected(self):
        """Inactive TPO must be rejected with HTTP 403 Forbidden."""
        self.tpo_profile_alpha.is_active = False
        self.tpo_profile_alpha.save()

        self.client.force_authenticate(user=self.user_tpo_alpha)
        response = self.client.get(self.download_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json().get("error", {}).get("code") == "PERMISSION_DENIED"
