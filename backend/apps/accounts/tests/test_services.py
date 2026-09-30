from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import LoginActivity, OTPVerification
from apps.accounts.services import AuthService
from apps.common.exceptions import DomainException

User = get_user_model()


class AuthServiceTests(TestCase):
    """Test suite for AuthService domain operations."""

    def setUp(self):
        cache.clear()
        self.mobile = "+919182583234"
        self.user = User.objects.create_user(
            mobile_number=self.mobile,
            role=User.RoleChoices.STUDENT,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
        )

    @patch("apps.accounts.services.generate_secure_numeric_code", return_value="123456")
    def test_request_otp_success(self, mock_otp):
        result = AuthService.request_otp(self.mobile)
        self.assertTrue(result)

        # Check DB record
        record = OTPVerification.objects.filter(mobile_number=self.mobile, is_used=False).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.user, self.user)
        self.assertEqual(record.otp_hash, AuthService._hash_otp(self.mobile, "123456"))

        # Check cooldown is active in cache
        self.assertTrue(cache.get(f"otp_cooldown:{self.mobile}"))

    @patch("apps.accounts.services.generate_secure_numeric_code", return_value="123456")
    def test_verify_otp_and_login_success(self, mock_otp):
        AuthService.request_otp(self.mobile)

        user, access_token, refresh_token, user_data = AuthService.verify_otp_and_login(
            self.mobile, "123456", ip_address="127.0.0.1"
        )
        self.assertEqual(user, self.user)
        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)
        self.assertEqual(user_data["id"], str(self.user.id))

        # Check that OTP record was marked as used (single use)
        record = OTPVerification.objects.filter(mobile_number=self.mobile).first()
        self.assertTrue(record.is_used)

        # Check LoginActivity logged
        activity = LoginActivity.objects.filter(
            user=self.user, status=LoginActivity.LoginStatus.SUCCESS
        ).first()
        self.assertIsNotNone(activity)

        # Verify decoded token claims
        token_payload = AccessToken(access_token)
        self.assertEqual(token_payload["role"], User.RoleChoices.STUDENT)
        self.assertEqual(token_payload["user_id"], str(self.user.id))

    @patch("apps.accounts.services.generate_secure_numeric_code", return_value="123456")
    def test_verify_otp_invalid(self, mock_otp):
        AuthService.request_otp(self.mobile)
        with self.assertRaises(DomainException) as ctx:
            AuthService.verify_otp_and_login(self.mobile, "000000")

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Invalid or expired OTP", str(ctx.exception.detail))

    @patch("apps.accounts.services.generate_secure_numeric_code", return_value="123456")
    def test_verify_otp_max_attempts_exceeded(self, mock_otp):
        AuthService.request_otp(self.mobile)

        # Attempt 5 wrong times
        for _ in range(5):
            try:
                AuthService.verify_otp_and_login(self.mobile, "111111")
            except DomainException:
                pass

        # 6th attempt should trigger max attempts exceeded
        with self.assertRaises(DomainException) as ctx:
            AuthService.verify_otp_and_login(self.mobile, "111111")

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Maximum OTP verification attempts exceeded", str(ctx.exception.detail))

    def test_issue_tokens_for_user(self):
        access_token, refresh_token = AuthService.issue_tokens_for_user(self.user)
        token_payload = AccessToken(access_token)
        self.assertEqual(token_payload["role"], User.RoleChoices.STUDENT)
        self.assertEqual(token_payload["user_id"], str(self.user.id))
