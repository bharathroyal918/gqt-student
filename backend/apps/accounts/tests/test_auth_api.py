"""Comprehensive API test suite for authentication and authorization.

Tests:
- Valid login (email + password, mobile + OTP)
- Invalid password
- Expired OTP
- Reused OTP
- Excessive OTP attempts
- Inactive account
- Unapproved account
- Student accessing admin API
- Student accessing another student's resource
- Expired JWT
- Refresh token rotation
- Logout and token blacklisting
- Anti-enumeration protection
- Admin student provisioning and status management
"""

from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import (
    AuditLog,
    LoginActivity,
    OTPVerification,
    PasswordResetRequest,
)
from apps.accounts.services import AuthService
from apps.students.models import StudentProfile

User = get_user_model()


class AuthenticationApiTests(TestCase):
    """Test suite for authentication, authorization, and student lifecycle endpoints."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()

        # Create Admin User
        self.admin_user = User.objects.create_user(
            email="admin@gqt.edu",
            password="SecureAdminPassword123!",
            role=User.RoleChoices.ADMIN,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )

        # Create Approved Active Student A
        self.student_a = User.objects.create_user(
            email="student.a@gqt.edu",
            mobile_number="+919876543210",
            password="StudentPass123!",
            role=User.RoleChoices.STUDENT,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
        )
        self.profile_a = StudentProfile.objects.create(
            user=self.student_a,
            student_id_number="GQT-STU-001",
            full_name="Student Alpha",
            batch_code="PY-2026-B1",
        )

        # Create Approved Active Student B
        self.student_b = User.objects.create_user(
            email="student.b@gqt.edu",
            mobile_number="+919876543211",
            password="StudentPass456!",
            role=User.RoleChoices.STUDENT,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
        )
        self.profile_b = StudentProfile.objects.create(
            user=self.student_b,
            student_id_number="GQT-STU-002",
            full_name="Student Beta",
            batch_code="PY-2026-B1",
        )

        # Create Inactive Student
        self.inactive_student = User.objects.create_user(
            email="inactive@gqt.edu",
            mobile_number="+919876543212",
            password="StudentPass789!",
            role=User.RoleChoices.STUDENT,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=False,
        )

        # Create Unapproved Student (Pending Activation)
        self.unapproved_student = User.objects.create_user(
            email="unapproved@gqt.edu",
            mobile_number="+919876543213",
            password="StudentPass999!",
            role=User.RoleChoices.STUDENT,
            onboarding_status=User.OnboardingStatusChoices.PENDING_ACTIVATION,
            is_active=True,
        )

    def _get_student_a_token(self):
        access, _ = AuthService.issue_tokens_for_user(self.student_a)
        return access

    def _get_admin_token(self):
        access, _ = AuthService.issue_tokens_for_user(self.admin_user)
        return access

    # ==========================================
    # 1. EMAIL & PASSWORD LOGIN
    # ==========================================

    def test_email_login_success(self):
        url = reverse("api_v1:auth:login_email")
        response = self.client.post(
            url,
            {"email": "student.a@gqt.edu", "password": "StudentPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["email"], "student.a@gqt.edu")
        self.assertEqual(
            response.data["data"]["user"]["student_profile"]["student_id_number"],
            "GQT-STU-001",
        )

        # Check LoginActivity logged
        login_log = LoginActivity.objects.filter(
            user=self.student_a,
            status=LoginActivity.LoginStatus.SUCCESS,
            login_type=LoginActivity.LoginType.EMAIL_PASSWORD,
        ).first()
        self.assertIsNotNone(login_log)

    def test_email_login_invalid_password(self):
        url = reverse("api_v1:auth:login_email")
        response = self.client.post(
            url,
            {"email": "student.a@gqt.edu", "password": "WrongPassword999!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "INVALID_CREDENTIALS")

        # Check LoginActivity logged failure
        login_log = LoginActivity.objects.filter(
            user=self.student_a,
            status=LoginActivity.LoginStatus.FAILED_CREDENTIALS,
        ).first()
        self.assertIsNotNone(login_log)

    def test_email_login_inactive_account(self):
        url = reverse("api_v1:auth:login_email")
        response = self.client.post(
            url,
            {"email": "inactive@gqt.edu", "password": "StudentPass789!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "ACCOUNT_INACTIVE")

        # Verify activity logged
        login_log = LoginActivity.objects.filter(
            user=self.inactive_student,
            status=LoginActivity.LoginStatus.LOCKED,
        ).first()
        self.assertIsNotNone(login_log)

    def test_email_login_unapproved_student(self):
        url = reverse("api_v1:auth:login_email")
        response = self.client.post(
            url,
            {"email": "unapproved@gqt.edu", "password": "StudentPass999!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["error"]["code"], "ACCOUNT_UNAPPROVED")

    # ==========================================
    # 2. OTP AUTHENTICATION & SECURITY
    # ==========================================

    @patch("apps.accounts.services.generate_secure_numeric_code", return_value="654321")
    def test_otp_request_and_verify_success(self, mock_otp):
        # 1. Request OTP
        req_url = reverse("api_v1:auth:otp_request")
        req_resp = self.client.post(
            req_url, {"mobile_number": "+919876543210"}, format="json"
        )
        self.assertEqual(req_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(req_resp.data["success"])

        # Check database record
        otp_record = OTPVerification.objects.filter(
            mobile_number="+919876543210", is_used=False
        ).first()
        self.assertIsNotNone(otp_record)
        self.assertFalse(otp_record.is_used)

        # 2. Verify OTP
        verify_url = reverse("api_v1:auth:otp_verify")
        verify_resp = self.client.post(
            verify_url,
            {"mobile_number": "+919876543210", "otp": "654321"},
            format="json",
        )
        self.assertEqual(verify_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_resp.data["success"])
        self.assertIn("access", verify_resp.data["data"])
        self.assertIn("refresh", verify_resp.data["data"])

        # Check OTP is now invalidated (single use)
        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_used)

        # Check LoginActivity
        activity = LoginActivity.objects.filter(
            user=self.student_a,
            status=LoginActivity.LoginStatus.SUCCESS,
            login_type=LoginActivity.LoginType.MOBILE_OTP,
        ).first()
        self.assertIsNotNone(activity)

    @patch("apps.accounts.services.generate_secure_numeric_code", return_value="654321")
    def test_otp_reused_fails(self, mock_otp):
        req_url = reverse("api_v1:auth:otp_request")
        self.client.post(req_url, {"mobile_number": "+919876543210"}, format="json")

        verify_url = reverse("api_v1:auth:otp_verify")
        # First verification succeeds
        first_resp = self.client.post(
            verify_url,
            {"mobile_number": "+919876543210", "otp": "654321"},
            format="json",
        )
        self.assertEqual(first_resp.status_code, status.HTTP_200_OK)

        # Second verification with same OTP must fail
        second_resp = self.client.post(
            verify_url,
            {"mobile_number": "+919876543210", "otp": "654321"},
            format="json",
        )
        self.assertEqual(second_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(second_resp.data["error"]["code"], "INVALID_OTP")

    def test_otp_expired_fails(self):
        # Create an expired OTP verification in database
        hashed = AuthService._hash_otp("+919876543210", "888888")
        past_time = timezone.now() - timedelta(minutes=10)
        OTPVerification.objects.create(
            user=self.student_a,
            mobile_number="+919876543210",
            otp_hash=hashed,
            purpose=OTPVerification.PurposeChoices.LOGIN,
            is_used=False,
            expires_at=past_time,
        )

        verify_url = reverse("api_v1:auth:otp_verify")
        response = self.client.post(
            verify_url,
            {"mobile_number": "+919876543210", "otp": "888888"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "INVALID_OTP")

    @patch("apps.accounts.services.generate_secure_numeric_code", return_value="123456")
    def test_otp_excessive_attempts_lockout(self, mock_otp):
        req_url = reverse("api_v1:auth:otp_request")
        self.client.post(req_url, {"mobile_number": "+919876543210"}, format="json")

        verify_url = reverse("api_v1:auth:otp_verify")
        # 5 wrong attempts
        for _ in range(5):
            resp = self.client.post(
                verify_url,
                {"mobile_number": "+919876543210", "otp": "000000"},
                format="json",
            )
            self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 6th attempt should be blocked as exceeded
        resp_6 = self.client.post(
            verify_url,
            {
                "mobile_number": "+919876543210",
                "otp": "123456",
            },  # Even with right OTP now
            format="json",
        )
        self.assertEqual(resp_6.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp_6.data["error"]["code"], "OTP_MAX_ATTEMPTS_EXCEEDED")

    @patch("apps.accounts.services.generate_secure_numeric_code", return_value="123456")
    def test_otp_cooldown_enforced(self, mock_otp):
        req_url = reverse("api_v1:auth:otp_request")
        # First request succeeds
        resp1 = self.client.post(
            req_url, {"mobile_number": "+919876543210"}, format="json"
        )
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)

        # Immediate second request triggers cooldown
        resp2 = self.client.post(
            req_url, {"mobile_number": "+919876543210"}, format="json"
        )
        self.assertEqual(resp2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(resp2.data["error"]["code"], "OTP_COOLDOWN")

    def test_otp_request_anti_enumeration(self):
        """Unregistered or unapproved mobile numbers return generic success without leaking status."""
        req_url = reverse("api_v1:auth:otp_request")
        # Non-existent mobile
        resp = self.client.post(
            req_url, {"mobile_number": "+910000000000"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertIn("If this mobile number is registered", resp.data["message"])

        # Unapproved student mobile
        resp2 = self.client.post(
            req_url, {"mobile_number": "+919876543213"}, format="json"
        )
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertTrue(resp2.data["success"])

    # ==========================================
    # 3. JWT TOKEN LIFECYCLE & ROTATION & LOGOUT
    # ==========================================

    def test_refresh_token_rotation_and_blacklisting(self):
        _, refresh_str = AuthService.issue_tokens_for_user(self.student_a)

        refresh_url = reverse("api_v1:auth:token_refresh")
        response = self.client.post(
            refresh_url, {"refresh": refresh_str}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        new_access = response.data["data"]["access"]
        new_refresh = response.data["data"]["refresh"]
        self.assertIsNotNone(new_access)
        self.assertIsNotNone(new_refresh)
        self.assertNotEqual(refresh_str, new_refresh)

        # Old refresh token is blacklisted, attempting to use it again fails
        second_response = self.client.post(
            refresh_url, {"refresh": refresh_str}, format="json"
        )
        self.assertEqual(second_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(second_response.data["error"]["code"], "TOKEN_INVALID")

    def test_logout_revokes_refresh_token(self):
        access_str, refresh_str = AuthService.issue_tokens_for_user(self.student_a)

        logout_url = reverse("api_v1:auth:logout")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_str}")
        logout_resp = self.client.post(
            logout_url, {"refresh": refresh_str}, format="json"
        )
        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

        # Now attempting to use the blacklisted refresh token fails
        refresh_url = reverse("api_v1:auth:token_refresh")
        refresh_resp = self.client.post(
            refresh_url, {"refresh": refresh_str}, format="json"
        )
        self.assertEqual(refresh_resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(refresh_resp.data["error"]["code"], "TOKEN_INVALID")

    def test_expired_jwt_access_token_rejected(self):
        token = AccessToken.for_user(self.student_a)
        # Force expiration timestamp into the past
        token.set_exp(lifetime=-timedelta(minutes=5))
        expired_token_str = str(token)

        me_url = reverse("api_v1:auth:me")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {expired_token_str}")
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==========================================
    # 4. CURRENT USER ME & PROFILE
    # ==========================================

    def test_auth_me_authenticated_student(self):
        access_token = self._get_student_a_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        me_url = reverse("api_v1:auth:me")
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data["data"]["user"]
        self.assertEqual(user_data["email"], "student.a@gqt.edu")
        self.assertEqual(user_data["role"], User.RoleChoices.STUDENT)
        self.assertEqual(
            user_data["student_profile"]["student_id_number"], "GQT-STU-001"
        )

    def test_auth_me_unauthenticated_fails(self):
        me_url = reverse("api_v1:auth:me")
        response = self.client.get(me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==========================================
    # 5. PASSWORD FORGOT & RESET LIFECYCLE
    # ==========================================

    def test_forgot_password_anti_enumeration(self):
        url = reverse("api_v1:auth:password_forgot")
        response = self.client.post(
            url, {"email": "nonexistent@gqt.edu"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn(
            "password reset instructions have been sent", response.data["message"]
        )

    def test_password_reset_flow_success(self):
        # Initiate reset
        AuthService.request_password_reset("student.a@gqt.edu")
        reset_record = PasswordResetRequest.objects.filter(
            user=self.student_a, is_used=False
        ).first()
        self.assertIsNotNone(reset_record)

        # Manually set known token hash
        raw_token = "valid-reset-token-123456789012345"
        reset_record.token_hash = AuthService._hash_token(raw_token)
        reset_record.save()

        # Submit new password
        reset_url = reverse("api_v1:auth:password_reset")
        response = self.client.post(
            reset_url,
            {"token": raw_token, "new_password": "BrandNewPassword123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Token is now used
        reset_record.refresh_from_db()
        self.assertTrue(reset_record.is_used)

        # AuditLog recorded
        audit = AuditLog.objects.filter(
            actor=self.student_a,
            action="PASSWORD_RESET_COMPLETED",
        ).first()
        self.assertIsNotNone(audit)

        # Can now login with new password
        self.student_a.refresh_from_db()
        self.assertTrue(self.student_a.check_password("BrandNewPassword123!"))

    # ==========================================
    # 6. AUTHORIZATION & RBAC & OBJECT PERMISSIONS
    # ==========================================

    def test_student_cannot_access_admin_provision_api(self):
        """Student receives 403 Forbidden when attempting to access admin provisioning."""
        token = self._get_student_a_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        url = reverse("api_v1:admin_students:provision")
        response = self.client.post(
            url,
            {
                "full_name": "Intruder Student",
                "student_id_number": "HACK-001",
                "batch_code": "PY-2026-B1",
                "email": "intruder@gqt.edu",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_provision_student(self):
        admin_token = self._get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")

        url = reverse("api_v1:admin_students:provision")
        response = self.client.post(
            url,
            {
                "full_name": "Carol Danvers",
                "student_id_number": "GQT-STU-003",
                "batch_code": "PY-2026-B1",
                "email": "carol@gqt.edu",
                "mobile_number": "+919876543299",
                "password": "CarolPassword123!",
                "college_name": "Bangalore Institute of Tech",
                "graduation_year": 2026,
                "onboarding_status": "ACTIVE",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["email"], "carol@gqt.edu")

        # Verify AuditLog created
        audit = AuditLog.objects.filter(
            actor=self.admin_user, action="STUDENT_PROVISIONED"
        ).first()
        self.assertIsNotNone(audit)

    def test_admin_can_update_student_status(self):
        admin_token = self._get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")

        url = reverse("api_v1:admin_students:status", kwargs={"pk": self.profile_a.id})
        response = self.client.patch(
            url,
            {
                "is_active": False,
                "onboarding_status": User.OnboardingStatusChoices.SUSPENDED,
                "reason": "Administrative suspension",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.student_a.refresh_from_db()
        self.assertFalse(self.student_a.is_active)
        self.assertEqual(
            self.student_a.onboarding_status, User.OnboardingStatusChoices.SUSPENDED
        )

    def test_student_cannot_access_another_students_resource(self):
        """Student A must NEVER be able to access Student B's profile (IsOwnerOrAdmin)."""
        student_a_token = self._get_student_a_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {student_a_token}")

        url = reverse(
            "api_v1:students:student_profile_detail", kwargs={"pk": self.profile_b.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_access_own_resource(self):
        student_a_token = self._get_student_a_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {student_a_token}")

        url = reverse(
            "api_v1:students:student_profile_detail", kwargs={"pk": self.profile_a.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["student_id_number"], "GQT-STU-001")

    def test_admin_can_access_any_students_resource(self):
        admin_token = self._get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")

        url = reverse(
            "api_v1:students:student_profile_detail", kwargs={"pk": self.profile_b.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["student_id_number"], "GQT-STU-002")
