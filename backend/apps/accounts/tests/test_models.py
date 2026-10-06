from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import AdminProfile, AuditLog, Role

User = get_user_model()


class UserModelTests(TestCase):
    """Test suite for custom User model and related accounts models."""

    def test_create_user_with_email(self):
        user = User.objects.create_user(
            email="student@gqt.local",
            password="SecurePassword123!",
            role="STUDENT",
        )
        self.assertEqual(user.email, "student@gqt.local")
        self.assertEqual(user.role, "STUDENT")
        self.assertTrue(user.check_password("SecurePassword123!"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_with_mobile(self):
        user = User.objects.create_user(
            mobile_number="+919876543210",
            role="STUDENT",
        )
        self.assertEqual(user.mobile_number, "+919876543210")
        self.assertFalse(user.has_usable_password())

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            email="admin@gqt.local",
            password="AdminPassword123!",
        )
        self.assertEqual(admin_user.role, "ADMIN")
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_role_and_admin_profile(self):
        role = Role.objects.create(name="Instructor", description="Course Instructor")
        self.assertEqual(str(role), "Instructor")
        admin_user = User.objects.create_superuser(
            email="manager@gqt.local",
            password="ManagerPassword123!",
        )
        profile = AdminProfile.objects.create(
            user=admin_user,
            department="Computer Science",
            can_review_projects=True,
            can_manage_curriculum=True,
        )
        self.assertEqual(profile.user, admin_user)
        self.assertEqual(str(profile), f"AdminProfile: {profile.full_name or admin_user}")

    def test_audit_log(self):
        user = User.objects.create_user(email="actor@gqt.local")
        log = AuditLog.objects.create(
            actor=user,
            action="STUDENT_ONBOARDED",
            target_model="User",
            target_id=str(user.id),
            payload={"student_id": "GQT-001"},
        )
        self.assertIsNotNone(log.id)
        self.assertEqual(log.action, "STUDENT_ONBOARDED")
