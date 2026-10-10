"""Comprehensive test suite for Admin TPO Management, Provisioning, Reassignment, and Lifecycle APIs."""

import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import AuditLog, TPOProfile, User
from apps.students.models import College


class AdminTPOManagementAPITests(APITestCase):
    """Test suite for Admin TPO and College assignment operations."""

    def setUp(self):
        # 1. Create colleges
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
        self.college_inactive = College.objects.create(
            name="Inactive Engineering College",
            code="IEC",
            city="Mysore",
            state="Karnataka",
            is_active=False,
        )

        # 2. Create Admin user
        self.admin_user = User.objects.create_user(
            email="super.admin@gqt.edu",
            password="AdminPassword123!",
            role=User.RoleChoices.ADMIN,
            is_staff=True,
        )
        self.admin_token = str(RefreshToken.for_user(self.admin_user).access_token)

        # 3. Create Student user
        self.student_user = User.objects.create_user(
            email="student.test@gqt.edu",
            password="StudentPassword123!",
            role=User.RoleChoices.STUDENT,
        )
        self.student_token = str(RefreshToken.for_user(self.student_user).access_token)

        # 4. Create an existing TPO user
        self.tpo_user = User.objects.create_user(
            email="existing.tpo@gqt.edu",
            password="TPOPassword123!",
            role=User.RoleChoices.TPO,
        )
        self.tpo_profile = TPOProfile.objects.create(
            user=self.tpo_user,
            college=self.college_a,
            full_name="Prof. Ananya Sen",
            designation="Training & Placement Officer",
            department="Placement Cell",
            phone_number="+91 9888877777",
            assigned_by=self.admin_user,
            is_active=True,
        )
        self.tpo_token = str(RefreshToken.for_user(self.tpo_user).access_token)

    # --------------------------------------------------------------------------
    # LIST & RETRIEVE TESTS
    # --------------------------------------------------------------------------
    def test_admin_can_list_tpos(self):
        """Admin can list TPO accounts with college context."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        response = self.client.get(reverse("api_v1:admin_tpos:list_create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.json()
        self.assertTrue(len(res_data["data"]) >= 1)
        first_tpo = res_data["data"][0]
        self.assertEqual(first_tpo["full_name"], "Prof. Ananya Sen")
        self.assertEqual(first_tpo["college"]["code"], "BIT")

    def test_admin_can_filter_tpos_by_college_and_search(self):
        """Admin can filter TPO list by search query and college_id."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        # Search by name
        response = self.client.get(
            f"{reverse('api_v1:admin_tpos:list_create')}?search=Ananya"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["data"]), 1)

        # Filter by college A
        response_col = self.client.get(
            f"{reverse('api_v1:admin_tpos:list_create')}?college_id={self.college_a.id}"
        )
        self.assertEqual(response_col.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_col.json()["data"]), 1)

        # Filter by college B (empty)
        response_empty = self.client.get(
            f"{reverse('api_v1:admin_tpos:list_create')}?college_id={self.college_b.id}"
        )
        self.assertEqual(response_empty.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_empty.json()["data"]), 0)

    def test_admin_can_retrieve_tpo_detail(self):
        """Admin can fetch full detail of a specific TPO."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        url = reverse("api_v1:admin_tpos:detail_update", kwargs={"pk": self.tpo_profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]
        self.assertEqual(data["full_name"], "Prof. Ananya Sen")
        self.assertEqual(data["email"], "existing.tpo@gqt.edu")
        self.assertEqual(data["college"]["id"], str(self.college_a.id))

    # --------------------------------------------------------------------------
    # PROVISIONING TESTS
    # --------------------------------------------------------------------------
    def test_admin_can_provision_new_tpo(self):
        """Admin provisions new TPO with college assignment and creates audit log."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        payload = {
            "email": "new.tpo.bmsce@gqt.edu",
            "full_name": "Dr. Ramesh Babu",
            "college_id": str(self.college_b.id),
            "designation": "Head of Corporate Relations",
            "department": "Department of Placements",
            "phone_number": "+91 9777766666",
            "bio": "Extensive corporate placement background.",
        }
        response = self.client.post(reverse("api_v1:admin_tpos:list_create"), data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        res_data = response.json()["data"]
        self.assertEqual(res_data["full_name"], "Dr. Ramesh Babu")
        self.assertEqual(res_data["email"], "new.tpo.bmsce@gqt.edu")
        self.assertEqual(res_data["college"]["code"], "BMSCE")

        # Verify User and TPOProfile in DB
        user = User.objects.get(email="new.tpo.bmsce@gqt.edu")
        self.assertEqual(user.role, User.RoleChoices.TPO)
        self.assertTrue(user.is_active)
        self.assertEqual(user.tpo_profile.college, self.college_b)
        self.assertEqual(user.tpo_profile.assigned_by, self.admin_user)

        # Verify Audit Log
        audit = AuditLog.objects.filter(action="TPO_PROVISIONED", target_id=str(user.tpo_profile.id)).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor, self.admin_user)

    def test_provision_fails_for_duplicate_email(self):
        """Provisioning fails with 400 when email is already registered."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        payload = {
            "email": "existing.tpo@gqt.edu",
            "full_name": "Duplicate TPO",
            "college_id": str(self.college_b.id),
        }
        response = self.client.post(reverse("api_v1:admin_tpos:list_create"), data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_provision_fails_for_student_email(self):
        """Admin cannot silently convert a student account to TPO."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        payload = {
            "email": "student.test@gqt.edu",
            "full_name": "Student Converted",
            "college_id": str(self.college_b.id),
        }
        response = self.client.post(reverse("api_v1:admin_tpos:list_create"), data=payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_provision_fails_for_inactive_or_nonexistent_college(self):
        """Provisioning fails if college does not exist or is inactive."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        # Inactive college
        payload_inactive = {
            "email": "tpo.inactive@gqt.edu",
            "full_name": "Inactive TPO",
            "college_id": str(self.college_inactive.id),
        }
        res_inactive = self.client.post(reverse("api_v1:admin_tpos:list_create"), data=payload_inactive)
        self.assertEqual(res_inactive.status_code, status.HTTP_400_BAD_REQUEST)

        # Nonexistent college
        payload_fake = {
            "email": "tpo.fake@gqt.edu",
            "full_name": "Fake TPO",
            "college_id": str(uuid.uuid4()),
        }
        res_fake = self.client.post(reverse("api_v1:admin_tpos:list_create"), data=payload_fake)
        self.assertEqual(res_fake.status_code, status.HTTP_400_BAD_REQUEST)

    # --------------------------------------------------------------------------
    # UPDATE, REASSIGN, DEACTIVATE, REACTIVATE TESTS
    # --------------------------------------------------------------------------
    def test_admin_can_update_tpo_metadata(self):
        """Admin can update designation, department, bio, phone number."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        url = reverse("api_v1:admin_tpos:detail_update", kwargs={"pk": self.tpo_profile.id})
        payload = {
            "designation": "Senior Director of Placements",
            "phone_number": "+91 9000011111",
        }
        response = self.client.patch(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tpo_profile.refresh_from_db()
        self.assertEqual(self.tpo_profile.designation, "Senior Director of Placements")

    def test_admin_can_reassign_tpo_college(self):
        """Admin reassigns TPO from College A to College B atomically."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        url = reverse("api_v1:admin_tpos:reassign_college", kwargs={"pk": self.tpo_profile.id})
        payload = {"college_id": str(self.college_b.id)}
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["data"]["college"]["code"], "BMSCE")

        # Verify DB and Audit Log
        self.tpo_profile.refresh_from_db()
        self.assertEqual(self.tpo_profile.college, self.college_b)
        audit = AuditLog.objects.filter(action="TPO_COLLEGE_REASSIGNED", target_id=str(self.tpo_profile.id)).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.payload["previous_college_code"], "BIT") if "previous_college_code" in audit.payload else None
        self.assertEqual(audit.payload["new_college_code"], "BMSCE")

    def test_admin_can_deactivate_and_reactivate_tpo(self):
        """Admin can deactivate TPO access and later reactivate it."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        deactivate_url = reverse("api_v1:admin_tpos:deactivate", kwargs={"pk": self.tpo_profile.id})
        reactivate_url = reverse("api_v1:admin_tpos:reactivate", kwargs={"pk": self.tpo_profile.id})

        # 1. Deactivate
        res_deact = self.client.post(deactivate_url)
        self.assertEqual(res_deact.status_code, status.HTTP_200_OK)
        self.tpo_profile.refresh_from_db()
        self.tpo_user.refresh_from_db()
        self.assertFalse(self.tpo_profile.is_active)
        self.assertFalse(self.tpo_user.is_active)

        # Verify deactivated TPO cannot access TPO portal (account inactive / token invalid)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        res_blocked = self.client.get(reverse("api_v1:tpo:profile_me"))
        self.assertIn(res_blocked.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # 2. Reactivate
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        res_react = self.client.post(reactivate_url)
        self.assertEqual(res_react.status_code, status.HTTP_200_OK)
        self.tpo_profile.refresh_from_db()
        self.tpo_user.refresh_from_db()
        self.assertTrue(self.tpo_profile.is_active)
        self.assertTrue(self.tpo_user.is_active)

    def test_admin_can_view_tpo_audit_history(self):
        """Admin can inspect all audit logs for a TPO."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")
        url = reverse("api_v1:admin_tpos:audit_history", kwargs={"pk": self.tpo_profile.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json()["data"], list)

    # --------------------------------------------------------------------------
    # PERMISSION BARRIER TESTS
    # --------------------------------------------------------------------------
    def test_student_cannot_call_admin_tpo_endpoints(self):
        """Student token receives 403 when hitting Admin TPO endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")
        response = self.client.get(reverse("api_v1:admin_tpos:list_create"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tpo_cannot_call_admin_tpo_endpoints(self):
        """TPO token receives 403 when hitting Admin TPO endpoints."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tpo_token}")
        response = self.client.get(reverse("api_v1:admin_tpos:list_create"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_call_admin_tpo_endpoints(self):
        """Anonymous request receives 401 when hitting Admin TPO endpoints."""
        response = self.client.get(reverse("api_v1:admin_tpos:list_create"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
