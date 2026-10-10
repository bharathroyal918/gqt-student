"""Integration and authorization tests for Phase 2 TPO foundation APIs."""

import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import TPOProfile, User
from apps.students.models import College, StudentProfile


class TPOFoundationAPITests(APITestCase):
    """Test suite verifying TPO API contracts, role boundaries, and permissions."""

    def setUp(self):
        # 1. Create two separate colleges
        self.college_a = College.objects.create(
            name="Bangalore Institute of Technology",
            code="BIT",
            city="Bangalore",
            state="Karnataka",
            is_active=True,
        )
        self.college_b = College.objects.create(
            name="BMS College of Engineering",
            code="BMSCE",
            city="Bangalore",
            state="Karnataka",
            is_active=True,
        )

        # 2. Create Admin user
        self.admin_user = User.objects.create_user(
            email="admin.main@gqt.edu",
            password="AdminPassword123!",
            role=User.RoleChoices.ADMIN,
            is_staff=True,
        )

        # 3. Create TPO user assigned to College A
        self.tpo_user = User.objects.create_user(
            email="tpo.bit@gqt.edu",
            password="TPOPassword123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        self.tpo_profile = TPOProfile.objects.create(
            user=self.tpo_user,
            college=self.college_a,
            full_name="Prof. Rajesh Sharma",
            designation="Training & Placement Officer",
            department="Placement Cell",
            phone_number="+91 9123456780",
            bio="Leading placements at BIT since 2018.",
            is_active=True,
        )

        # 4. Create Student user
        self.student_user = User.objects.create_user(
            email="student.bit@gqt.edu",
            password="StudentPassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id_number="GQT2600001",
            full_name="Rohan Gupta",
            batch_code="BATCH-2026-A",
            college=self.college_a,
            college_name=self.college_a.name,
        )

        # JWT Tokens
        self.tpo_token = str(RefreshToken.for_user(self.tpo_user).access_token)
        self.student_token = str(RefreshToken.for_user(self.student_user).access_token)
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)

    def test_tpo_get_me_success(self):
        """Authenticated TPO can retrieve their profile and assigned college."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(reverse("api_v1:tpo:profile_me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.json()["data"]
        self.assertEqual(res_data["full_name"], "Prof. Rajesh Sharma")
        self.assertEqual(res_data["email"], "tpo.bit@gqt.edu")
        self.assertEqual(res_data["college"]["code"], "BIT")
        self.assertEqual(res_data["role"], "TPO")

    def test_tpo_patch_me_allowed_fields(self):
        """TPO can update allowed personal fields."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        payload = {
            "full_name": "Prof. Rajesh K. Sharma",
            "designation": "Director of Corporate Relations & TPO",
            "bio": "Updated biography narrative.",
            "phone_number": "+91 9999888877",
        }
        response = self.client.patch(reverse("api_v1:tpo:profile_me"), data=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.json()["data"]
        self.assertEqual(res_data["full_name"], "Prof. Rajesh K. Sharma")
        self.assertEqual(res_data["designation"], "Director of Corporate Relations & TPO")
        self.assertEqual(res_data["bio"], "Updated biography narrative.")

        # Verify in DB
        self.tpo_profile.refresh_from_db()
        self.assertEqual(self.tpo_profile.full_name, "Prof. Rajesh K. Sharma")

    def test_tpo_patch_me_cannot_change_role_or_college(self):
        """Attempting to alter role, college, or is_active is ignored/prevented."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        payload = {
            "role": "ADMIN",
            "college": str(self.college_b.id),
            "college_id": str(self.college_b.id),
            "is_active": False,
            "email": "hacked@admin.com",
        }
        response = self.client.patch(reverse("api_v1:tpo:profile_me"), data=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify DB is unchanged for protected attributes
        self.tpo_user.refresh_from_db()
        self.tpo_profile.refresh_from_db()
        self.assertEqual(self.tpo_user.role, User.RoleChoices.TPO)
        self.assertEqual(self.tpo_user.email, "tpo.bit@gqt.edu")
        self.assertEqual(self.tpo_profile.college, self.college_a)
        self.assertTrue(self.tpo_profile.is_active)

    def test_tpo_get_college_detail(self):
        """TPO gets the authorized college's details."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(reverse("api_v1:tpo:college_detail"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        college_data = response.json()["data"]
        self.assertEqual(college_data["name"], "Bangalore Institute of Technology")
        self.assertEqual(college_data["code"], "BIT")

    def test_tpo_get_college_detail_tampering_ignored(self):
        """Query params attempting to switch college ID are completely ignored."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(
            f"{reverse('api_v1:tpo:college_detail')}?college_id={self.college_b.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        college_data = response.json()["data"]
        # Must still return College A
        self.assertEqual(college_data["code"], "BIT")

    def test_anonymous_cannot_access_tpo_endpoints(self):
        """Unauthenticated requests to TPO endpoints receive 401."""
        response = self.client.get(reverse("api_v1:tpo:profile_me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_student_cannot_access_tpo_endpoints(self):
        """Student token receives 403 when accessing TPO endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        response = self.client.get(reverse("api_v1:tpo:profile_me"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tpo_cannot_access_admin_endpoints(self):
        """TPO token receives 403 when accessing Admin-only endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(reverse("api_v1:admin_students:list_create"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
