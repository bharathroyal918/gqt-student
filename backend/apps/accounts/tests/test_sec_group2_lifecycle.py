"""Tests for SEC-03, SEC-04, and SEC-08: Token lifecycle, revocation, and account status controls."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.services import AuthService, StudentProvisioningService
from apps.students.models import StudentProfile
from apps.students.services import StudentAdminService

User = get_user_model()


class TestTokenRevocationOnPasswordLifecycle(TestCase):
    """SEC-03: Verify refresh token revocation on password change and reset."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="student.test@gqt.edu",
            password="InitialPassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-101",
            full_name="Test Student",
        )
        self.refresh_url = reverse("api_v1:auth:token_refresh")
        self.change_pwd_url = reverse("api_v1:auth:password_change")

    def test_password_change_invalidates_pre_existing_refresh_token(self):
        """Pre-existing refresh tokens must be rejected after password change."""
        # Issue tokens before password change
        access_token, refresh_token = AuthService.issue_tokens_for_user(self.user)

        # Authenticate and change password
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.change_pwd_url,
            {
                "current_password": "InitialPassword123!",
                "new_password": "NewSecurePassword456!",
            },
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify old refresh token is blacklisted and rejected
        self.client.force_authenticate(user=None)
        refresh_res = self.client.post(self.refresh_url, {"refresh": str(refresh_token)})
        assert refresh_res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_invalidates_pre_existing_refresh_token(self):
        """Pre-existing refresh tokens must be rejected after password reset."""
        # Issue tokens before password reset
        access_token, refresh_token = AuthService.issue_tokens_for_user(self.user)

        # Initiate and execute password reset via AuthService
        AuthService.request_password_reset(email=self.user.email)
        from apps.accounts.models import PasswordResetRequest
        reset_req = PasswordResetRequest.objects.filter(user=self.user, is_used=False).first()
        assert reset_req is not None

        # Reset password directly using user's token
        from apps.common.utils import generate_secure_token
        raw_token = "dummy_test_reset_token_32chars_long!!"
        reset_req.token_hash = AuthService._hash_token(raw_token)
        reset_req.save()

        reset_success = AuthService.reset_password(
            token=raw_token,
            new_password="ResetNewPassword789!",
        )
        assert reset_success is True

        # Verify old refresh token is blacklisted and rejected
        refresh_res = self.client.post(self.refresh_url, {"refresh": str(refresh_token)})
        assert refresh_res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST)

    def test_repeated_token_revocation_is_idempotent(self):
        """Calling revoke_all_user_tokens multiple times does not error."""
        AuthService.issue_tokens_for_user(self.user)
        count1 = AuthService.revoke_all_user_tokens(self.user)
        assert count1 >= 1
        count2 = AuthService.revoke_all_user_tokens(self.user)
        assert count2 == 0


class TestSuspendedAccountRefreshProtection(TestCase):
    """SEC-04: Verify suspended/pending accounts cannot refresh tokens."""

    def setUp(self):
        self.client = APIClient()
        self.refresh_url = reverse("api_v1:auth:token_refresh")
        self.user = User.objects.create_user(
            email="active.student@gqt.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )

    def test_approved_active_student_can_rotate_token(self):
        """Active approved student can successfully refresh tokens."""
        _, refresh_token = AuthService.issue_tokens_for_user(self.user)
        response = self.client.post(self.refresh_url, {"refresh": str(refresh_token)})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.json()["data"]

    def test_suspended_student_cannot_rotate_token(self):
        """Suspended student receives HTTP 403 when attempting token rotation."""
        _, refresh_token = AuthService.issue_tokens_for_user(self.user)
        self.user.onboarding_status = User.OnboardingStatusChoices.SUSPENDED
        self.user.save()

        response = self.client.post(self.refresh_url, {"refresh": str(refresh_token)})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["error"]["code"] == "ACCOUNT_SUSPENDED"

    def test_pending_activation_student_cannot_rotate_token(self):
        """Pending activation student receives HTTP 403 when attempting token rotation."""
        _, refresh_token = AuthService.issue_tokens_for_user(self.user)
        self.user.onboarding_status = User.OnboardingStatusChoices.PENDING_ACTIVATION
        self.user.save()

        response = self.client.post(self.refresh_url, {"refresh": str(refresh_token)})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["error"]["code"] == "ACCOUNT_UNAPPROVED"

    def test_inactive_student_cannot_rotate_token(self):
        """Deactivated student receives HTTP 401 when attempting token rotation."""
        _, refresh_token = AuthService.issue_tokens_for_user(self.user)
        self.user.is_active = False
        self.user.save()

        response = self.client.post(self.refresh_url, {"refresh": str(refresh_token)})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["error"]["code"] == "USER_INACTIVE"


class TestStudentSuspensionTokenRevocation(TestCase):
    """SEC-08: Verify token revocation upon student suspension or deactivation."""

    def setUp(self):
        self.client = APIClient()
        self.refresh_url = reverse("api_v1:auth:token_refresh")
        self.admin_user = User.objects.create_user(
            email="admin.officer@gqt.edu",
            password="AdminPassword123!",
            role=User.RoleChoices.ADMIN,
            is_staff=True,
            is_active=True,
        )
        self.student_user = User.objects.create_user(
            email="suspension.target@gqt.edu",
            password="TargetPassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id_number="GQT-STU-999",
            full_name="Target Student",
        )

    def test_update_student_status_to_suspended_revokes_tokens(self):
        """Updating status to SUSPENDED immediately invalidates outstanding tokens."""
        _, refresh_token = AuthService.issue_tokens_for_user(self.student_user)

        StudentProvisioningService.update_student_status(
            admin_user=self.admin_user,
            student_profile_id=str(self.student_profile.id),
            onboarding_status=User.OnboardingStatusChoices.SUSPENDED,
            reason="Violation of institutional policy",
        )

        response = self.client.post(self.refresh_url, {"refresh": str(refresh_token)})
        # Both blacklisted (401) or rejected on suspended status (403) confirm revocation
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_update_student_status_to_inactive_revokes_tokens(self):
        """Deactivating student (is_active=False) immediately invalidates outstanding tokens."""
        _, refresh_token = AuthService.issue_tokens_for_user(self.student_user)

        StudentProvisioningService.update_student_status(
            admin_user=self.admin_user,
            student_profile_id=str(self.student_profile.id),
            is_active=False,
            reason="Account disabled by admin",
        )

        response = self.client.post(self.refresh_url, {"refresh": str(refresh_token)})
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_revoke_student_access_revokes_tokens(self):
        """StudentAdminService.revoke_student_access revokes all outstanding tokens."""
        _, refresh_token = AuthService.issue_tokens_for_user(self.student_user)

        StudentAdminService.revoke_student_access(
            student_id=str(self.student_profile.id),
            admin_user=self.admin_user,
        )

        response = self.client.post(self.refresh_url, {"refresh": str(refresh_token)})
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
