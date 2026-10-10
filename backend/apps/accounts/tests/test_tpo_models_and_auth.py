"""Unit tests for TPO identity, role model, and authentication services."""

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import TPOProfile, User
from apps.accounts.services import AuthService
from apps.common.exceptions import DomainException
from apps.students.models import College


class TPOModelAndAuthTests(TestCase):
    """Test suite covering TPO identity models, college assignments, and authentication."""

    def setUp(self):
        self.college = College.objects.create(
            name="Bangalore Institute of Technology",
            code="BIT",
            city="Bangalore",
            state="Karnataka",
            is_active=True,
        )
        self.admin_user = User.objects.create_user(
            email="admin.tpo@gqt.edu",
            password="SecureAdminPassword123!",
            role=User.RoleChoices.ADMIN,
            is_staff=True,
        )
        self.tpo_user = User.objects.create_user(
            email="tpo.bit@gqt.edu",
            password="SecureTPOPassword123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        self.tpo_profile = TPOProfile.objects.create(
            user=self.tpo_user,
            college=self.college,
            full_name="Dr. Suresh Kumar",
            designation="Head of Training & Placement",
            department="Placement Cell",
            phone_number="+91 9876543210",
            assigned_by=self.admin_user,
            assigned_at=timezone.now(),
            is_active=True,
        )

    def test_tpo_profile_creation_and_relationship(self):
        """TPOProfile must link 1:1 to User and ForeignKey to College."""
        self.assertEqual(self.tpo_user.role, User.RoleChoices.TPO)
        self.assertEqual(self.tpo_user.tpo_profile.full_name, "Dr. Suresh Kumar")
        self.assertEqual(self.tpo_user.tpo_profile.college, self.college)
        self.assertTrue(self.tpo_user.tpo_profile.is_active)
        self.assertEqual(self.tpo_user.tpo_profile.assigned_by, self.admin_user)

    def test_tpo_login_success(self):
        """TPO user with active assignment must authenticate successfully."""
        user, access, refresh, user_data = AuthService.login_as_tpo(
            email="tpo.bit@gqt.edu",
            password="SecureTPOPassword123!",
        )
        self.assertEqual(user, self.tpo_user)
        self.assertIsNotNone(access)
        self.assertIsNotNone(refresh)
        self.assertEqual(user_data["role"], "TPO")
        self.assertIn("tpo_profile", user_data)
        self.assertEqual(user_data["tpo_profile"]["college"]["code"], "BIT")

    def test_tpo_login_rejected_for_student(self):
        """Student credentials must be rejected by login_as_tpo."""
        student_user = User.objects.create_user(
            email="student1@gqt.edu",
            password="SecureStudentPassword123!",
            role=User.RoleChoices.STUDENT,
        )
        with self.assertRaises(DomainException) as cm:
            AuthService.login_as_tpo(
                email="student1@gqt.edu",
                password="SecureStudentPassword123!",
            )
        self.assertEqual(cm.exception.status_code, 403)
        self.assertEqual(getattr(cm.exception.detail, "code", None), "FORBIDDEN_ROLE")

    def test_tpo_login_rejected_when_tpo_profile_inactive(self):
        """Deactivated TPO profile must be blocked from login."""
        self.tpo_profile.is_active = False
        self.tpo_profile.save(update_fields=["is_active"])

        with self.assertRaises(DomainException) as cm:
            AuthService.login_as_tpo(
                email="tpo.bit@gqt.edu",
                password="SecureTPOPassword123!",
            )
        self.assertEqual(cm.exception.status_code, 403)
        self.assertEqual(getattr(cm.exception.detail, "code", None), "TPO_INACTIVE")

    def test_tpo_login_rejected_when_college_inactive(self):
        """TPO whose assigned college is inactive must be blocked."""
        self.college.is_active = False
        self.college.save(update_fields=["is_active"])

        with self.assertRaises(DomainException) as cm:
            AuthService.login_as_tpo(
                email="tpo.bit@gqt.edu",
                password="SecureTPOPassword123!",
            )
        self.assertEqual(cm.exception.status_code, 403)
        self.assertEqual(getattr(cm.exception.detail, "code", None), "TPO_NO_COLLEGE_ASSIGNED")

    def test_get_tpo_assigned_college_utility(self):
        """get_tpo_assigned_college must resolve the authoritative college."""
        resolved_college = AuthService.get_tpo_assigned_college(self.tpo_user)
        self.assertEqual(resolved_college, self.college)

    def test_get_tpo_assigned_college_fails_for_non_tpo(self):
        """Utility fails closed for admin or student users."""
        with self.assertRaises(DomainException):
            AuthService.get_tpo_assigned_college(self.admin_user)
