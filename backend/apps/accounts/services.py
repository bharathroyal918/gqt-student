import hashlib
import logging
from datetime import timedelta
from typing import Any, Dict, Optional, Tuple
from django.conf import settings
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounts.models import (
    AuditLog,
    LoginActivity,
    OTPVerification,
    PasswordResetRequest,
    User,
)
from apps.common.exceptions import DomainException
from apps.common.utils import generate_secure_numeric_code, generate_secure_token, mask_email, mask_phone
from apps.students.models import StudentProfile

logger = logging.getLogger(__name__)


class AuthService:
    """Production domain service handling authentication flows, OTP lifecycles, and JWT issuance."""

    OTP_TTL_SECONDS = 300  # 5 minutes
    OTP_COOLDOWN_SECONDS = 60  # 1 minute resend cooldown
    OTP_MAX_ATTEMPTS = 5
    PASSWORD_RESET_TTL_MINUTES = 60  # 1 hour

    @staticmethod
    def _hash_otp(mobile_number: str, otp: str) -> str:
        """Compute salted SHA-256 hash of the OTP."""
        return hashlib.sha256(f"{mobile_number}:{otp}".encode("utf-8")).hexdigest()

    @staticmethod
    def _hash_token(token: str) -> str:
        """Compute SHA-256 hash of the password reset token."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @classmethod
    @transaction.atomic
    def register_student(
        cls,
        full_name: str,
        email: str,
        mobile_number: str,
        password: str,
        student_id_number: str = "",
        college_name: str = "",
        batch_code: str = "BATCH-2026-A",
        graduation_year: Optional[int] = 2026,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> Tuple[User, str, str, Dict[str, Any]]:
        """Self-registration for new students, provisioning profile and issuing initial session tokens."""
        clean_email = email.strip().lower()
        clean_mobile = mobile_number.strip()

        if User.objects.filter(email=clean_email).exists():
            raise DomainException(
                detail="An account with this email address already exists. Please log in.",
                code="EMAIL_ALREADY_EXISTS",
                status_code=400,
            )

        if User.objects.filter(mobile_number=clean_mobile).exists():
            raise DomainException(
                detail="An account with this mobile number already exists. Please log in.",
                code="MOBILE_ALREADY_EXISTS",
                status_code=400,
            )

        # Generate student ID number if not specified
        clean_student_id = student_id_number.strip()
        if not clean_student_id:
            prefix = "GQT"
            year_part = timezone.now().strftime("%y")
            random_part = generate_secure_numeric_code(5)
            clean_student_id = f"{prefix}{year_part}{random_part}"
            while StudentProfile.objects.filter(student_id_number=clean_student_id).exists():
                random_part = generate_secure_numeric_code(5)
                clean_student_id = f"{prefix}{year_part}{random_part}"
        elif StudentProfile.objects.filter(student_id_number=clean_student_id).exists():
            raise DomainException(
                detail="A student with this Student ID / USN is already registered.",
                code="STUDENT_ID_EXISTS",
                status_code=400,
            )

        user = User.objects.create_user(
            email=clean_email,
            mobile_number=clean_mobile,
            password=password,
            role=User.RoleChoices.STUDENT,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
            last_login_ip=ip_address,
        )

        StudentProfile.objects.create(
            user=user,
            student_id_number=clean_student_id,
            full_name=full_name.strip(),
            batch_code=batch_code.strip() if batch_code else "BATCH-2026-A",
            college_name=college_name.strip() if college_name else "",
            graduation_year=graduation_year or 2026,
        )

        AuditLog.objects.create(
            actor=user,
            action="STUDENT_SELF_REGISTERED",
            target_model="User",
            target_id=str(user.id),
            ip_address=ip_address,
            payload={
                "email": clean_email,
                "mobile_number": clean_mobile,
                "student_id_number": clean_student_id,
            },
        )

        LoginActivity.objects.create(
            user=user,
            identifier=clean_email,
            login_type=LoginActivity.LoginType.EMAIL_PASSWORD,
            status=LoginActivity.LoginStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        access_token, refresh_token = cls.issue_tokens_for_user(user)
        user_data = cls.get_user_profile_data(user)
        return user, access_token, refresh_token, user_data

    @classmethod
    def login_as_student(
        cls,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> Tuple[User, str, str, Dict[str, Any]]:
        """Dedicated student authentication verifying role permissions."""
        user, access, refresh, user_data = cls.login_with_email(
            email=email, password=password, ip_address=ip_address, user_agent=user_agent
        )
        if user.role != User.RoleChoices.STUDENT:
            raise DomainException(
                detail="Access denied. Administrative staff must sign in via the Admin Login Portal.",
                code="FORBIDDEN_ROLE",
                status_code=403,
            )
        return user, access, refresh, user_data

    @classmethod
    def login_as_admin(
        cls,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> Tuple[User, str, str, Dict[str, Any]]:
        """Dedicated admin authentication verifying administrative privileges."""
        user, access, refresh, user_data = cls.login_with_email(
            email=email, password=password, ip_address=ip_address, user_agent=user_agent
        )
        if user.role != User.RoleChoices.ADMIN:
            raise DomainException(
                detail="Access denied. The Admin Portal is restricted to authorized administrators.",
                code="FORBIDDEN_ROLE",
                status_code=403,
            )
        return user, access, refresh, user_data

    @classmethod
    def login_with_email(
        cls,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> Tuple[User, str, str, Dict[str, Any]]:
        """Authenticate user via email and password."""
        user = authenticate(username=email, password=password)

        if not user:
            # Check if user exists to record detailed audit without revealing to client
            existing_user = User.objects.filter(email=email).first()
            if (
                existing_user
                and existing_user.check_password(password)
                and not existing_user.is_active
            ):
                LoginActivity.objects.create(
                    user=existing_user,
                    identifier=email,
                    login_type=LoginActivity.LoginType.EMAIL_PASSWORD,
                    status=LoginActivity.LoginStatus.LOCKED,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    failure_reason="Account is inactive",
                )
                raise DomainException(
                    detail="Invalid credentials or account unapproved.",
                    code="ACCOUNT_INACTIVE",
                    status_code=403,
                )

            LoginActivity.objects.create(
                user=existing_user,
                identifier=email,
                login_type=LoginActivity.LoginType.EMAIL_PASSWORD,
                status=LoginActivity.LoginStatus.FAILED_CREDENTIALS,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason="Invalid credentials",
            )
            raise DomainException(
                detail="Invalid credentials or account unapproved.",
                code="INVALID_CREDENTIALS",
                status_code=401,
            )

        # Enforce account active status
        if not user.is_active:
            LoginActivity.objects.create(
                user=user,
                identifier=email,
                login_type=LoginActivity.LoginType.EMAIL_PASSWORD,
                status=LoginActivity.LoginStatus.LOCKED,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason="Account is inactive",
            )
            raise DomainException(
                detail="Invalid credentials or account unapproved.",
                code="ACCOUNT_INACTIVE",
                status_code=403,
            )

        # Enforce student unapproved status
        if (
            user.role == User.RoleChoices.STUDENT
            and user.onboarding_status == User.OnboardingStatusChoices.PENDING_ACTIVATION
        ):
            LoginActivity.objects.create(
                user=user,
                identifier=email,
                login_type=LoginActivity.LoginType.EMAIL_PASSWORD,
                status=LoginActivity.LoginStatus.LOCKED,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason="Account unapproved",
            )
            raise DomainException(
                detail="Your student account registration is pending administrative approval.",
                code="ACCOUNT_UNAPPROVED",
                status_code=403,
            )

        # Enforce student suspended status
        if (
            user.role == User.RoleChoices.STUDENT
            and user.onboarding_status == User.OnboardingStatusChoices.SUSPENDED
        ):
            LoginActivity.objects.create(
                user=user,
                identifier=email,
                login_type=LoginActivity.LoginType.EMAIL_PASSWORD,
                status=LoginActivity.LoginStatus.LOCKED,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason="Account suspended",
            )
            raise DomainException(
                detail="Your student account has been suspended. Please contact institutional operations.",
                code="ACCOUNT_SUSPENDED",
                status_code=403,
            )

        # Successful Login
        user.last_login_ip = ip_address
        user.save(update_fields=["last_login_ip", "last_login"])

        LoginActivity.objects.create(
            user=user,
            identifier=email,
            login_type=LoginActivity.LoginType.EMAIL_PASSWORD,
            status=LoginActivity.LoginStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        access_token, refresh_token = cls.issue_tokens_for_user(user)
        user_data = cls.get_user_profile_data(user)
        return user, access_token, refresh_token, user_data

    @classmethod
    def request_otp(cls, mobile_number: str, ip_address: Optional[str] = None) -> bool:
        """Generate and dispatch an OTP with cooldown and rate-limit guardrails."""
        # 1. Enforce Resend Cooldown
        cooldown_key = f"otp_cooldown:{mobile_number}"
        if cache.get(cooldown_key):
            raise DomainException(
                detail="Please wait 60 seconds before requesting another OTP.",
                code="OTP_COOLDOWN",
                status_code=429,
            )

        # 2. Check Hourly Rate Limit
        rate_limit_key = f"otp_rate_limit:{mobile_number}"
        hourly_count = cache.get(rate_limit_key, 0)
        if hourly_count >= 5:
            raise DomainException(
                detail="Maximum OTP requests exceeded for this hour. Please try again later.",
                code="OTP_RATE_LIMIT_EXCEEDED",
                status_code=429,
            )

        # 3. Verify user existence, active status, and approval
        user = User.objects.filter(mobile_number=mobile_number).first()
        if (
            not user
            or not user.is_active
            or (
                user.role == User.RoleChoices.STUDENT
                and user.onboarding_status != User.OnboardingStatusChoices.ACTIVE
            )
        ):
            # Anti-Enumeration: Return generic success without dispatching SMS
            logger.info(f"OTP request for non-active or unapproved mobile: {mobile_number}")
            cache.set(cooldown_key, True, timeout=cls.OTP_COOLDOWN_SECONDS)
            cache.set(rate_limit_key, hourly_count + 1, timeout=3600)
            return True

        # 4. Generate Cryptographic 6-digit OTP
        otp = generate_secure_numeric_code(6)
        otp_hash = cls._hash_otp(mobile_number, otp)
        expires_at = timezone.now() + timedelta(seconds=cls.OTP_TTL_SECONDS)

        # 5. Persist OTP in database & cache
        with transaction.atomic():
            # Invalidate any prior unused OTPs for this mobile
            OTPVerification.objects.filter(mobile_number=mobile_number, is_used=False).update(
                is_used=True
            )

            OTPVerification.objects.create(
                user=user,
                mobile_number=mobile_number,
                otp_hash=otp_hash,
                purpose=OTPVerification.PurposeChoices.LOGIN,
                attempts=0,
                max_attempts=cls.OTP_MAX_ATTEMPTS,
                expires_at=expires_at,
            )

        # Store in Redis for rapid verification
        cache_key = f"otp_verification:{mobile_number}"
        cache.set(
            cache_key,
            {"otp_hash": otp_hash, "attempts": 0},
            timeout=cls.OTP_TTL_SECONDS,
        )

        # Set Cooldown & Increment rate limit
        cache.set(cooldown_key, True, timeout=cls.OTP_COOLDOWN_SECONDS)
        cache.set(rate_limit_key, hourly_count + 1, timeout=3600)

        logger.info(f"[SMS/OTP DISPATCH] Mobile: {mobile_number} | Code: {otp}")
        return True

    @classmethod
    def verify_otp_and_login(
        cls,
        mobile_number: str,
        otp: str,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> Tuple[User, str, str, Dict[str, Any]]:
        """Verify OTP against database record & Redis cache, issuing JWT on success."""
        now = timezone.now()

        # Find latest active OTP verification record
        otp_record = (
            OTPVerification.objects.filter(
                mobile_number=mobile_number,
                is_used=False,
                expires_at__gte=now,
            )
            .order_by("-created_at")
            .first()
        )

        if not otp_record:
            LoginActivity.objects.create(
                identifier=mobile_number,
                login_type=LoginActivity.LoginType.MOBILE_OTP,
                status=LoginActivity.LoginStatus.FAILED_OTP,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason="No active or unexpired OTP found",
            )
            raise DomainException(
                detail="Invalid or expired OTP.",
                code="INVALID_OTP",
                status_code=400,
            )

        # Check maximum attempt ceiling
        if otp_record.attempts >= otp_record.max_attempts:
            otp_record.is_used = True
            otp_record.save(update_fields=["is_used", "updated_at"])
            cache.delete(f"otp_verification:{mobile_number}")

            LoginActivity.objects.create(
                user=otp_record.user,
                identifier=mobile_number,
                login_type=LoginActivity.LoginType.MOBILE_OTP,
                status=LoginActivity.LoginStatus.LOCKED,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason="Max OTP verification attempts exceeded",
            )
            raise DomainException(
                detail="Maximum OTP verification attempts exceeded. Please request a new OTP.",
                code="OTP_MAX_ATTEMPTS_EXCEEDED",
                status_code=400,
            )

        # Compare Hashes
        provided_hash = cls._hash_otp(mobile_number, otp)
        if otp_record.otp_hash != provided_hash:
            otp_record.attempts += 1
            otp_record.save(update_fields=["attempts", "updated_at"])

            LoginActivity.objects.create(
                user=otp_record.user,
                identifier=mobile_number,
                login_type=LoginActivity.LoginType.MOBILE_OTP,
                status=LoginActivity.LoginStatus.FAILED_OTP,
                ip_address=ip_address,
                user_agent=user_agent,
                failure_reason=f"OTP mismatch (attempt {otp_record.attempts})",
            )
            raise DomainException(
                detail="Invalid or expired OTP.",
                code="INVALID_OTP",
                status_code=400,
            )

        # Successful Verification: Invalidate OTP immediately
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used", "updated_at"])
        cache.delete(f"otp_verification:{mobile_number}")

        user = otp_record.user
        if not user or not user.is_active:
            raise DomainException(
                detail="Invalid credentials or account unapproved.",
                code="ACCOUNT_INACTIVE",
                status_code=403,
            )

        if (
            user.role == User.RoleChoices.STUDENT
            and user.onboarding_status == User.OnboardingStatusChoices.SUSPENDED
        ):
            raise DomainException(
                detail="Your student account has been suspended. Please contact institutional operations.",
                code="ACCOUNT_SUSPENDED",
                status_code=403,
            )

        user.last_login_ip = ip_address
        user.save(update_fields=["last_login_ip", "last_login"])

        LoginActivity.objects.create(
            user=user,
            identifier=mobile_number,
            login_type=LoginActivity.LoginType.MOBILE_OTP,
            status=LoginActivity.LoginStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        access_token, refresh_token = cls.issue_tokens_for_user(user)
        user_data = cls.get_user_profile_data(user)
        return user, access_token, refresh_token, user_data

    @classmethod
    def rotate_token(cls, refresh_token_str: str) -> Tuple[str, str]:
        """Rotate JWT refresh token and issue new token pair."""
        try:
            old_refresh = RefreshToken(refresh_token_str)
            user_id = old_refresh.payload.get("user_id")
            user = User.objects.filter(id=user_id, is_active=True).first()

            if not user:
                raise DomainException(
                    "User is inactive or not found.", code="USER_INACTIVE", status_code=401
                )

            # Invalidate old refresh token (SimpleJWT blacklist)
            old_refresh.blacklist()

            # Issue fresh token pair
            new_refresh = RefreshToken.for_user(user)
            new_refresh["role"] = user.role
            return str(new_refresh.access_token), str(new_refresh)
        except TokenError as exc:
            raise DomainException(
                detail="Invalid or blacklisted refresh token.",
                code="TOKEN_INVALID",
                status_code=401,
            ) from exc

    @classmethod
    def logout(
        cls,
        refresh_token_str: str,
        user: Optional[User] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """Revoke and blacklist active refresh token and record audit trail."""
        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()

            if user and user.is_authenticated:
                AuditLog.objects.create(
                    actor=user,
                    action="USER_LOGOUT",
                    target_model="User",
                    target_id=str(user.id),
                    ip_address=ip_address,
                    payload={"email": user.email},
                )
            return True
        except TokenError as exc:
            raise DomainException(
                detail="Invalid or expired token.",
                code="TOKEN_INVALID",
                status_code=400,
            ) from exc

    @classmethod
    def request_password_reset_otp(
        cls, identifier: str, ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate and dispatch a 6-digit OTP for password recovery to email or mobile."""
        cleaned_id = identifier.strip().lower()

        # Enforce rate limiting & cooldown
        cooldown_key = f"pwd_reset_cooldown:{cleaned_id}"
        if cache.get(cooldown_key):
            raise DomainException(
                detail="Please wait 60 seconds before requesting another reset OTP.",
                code="OTP_COOLDOWN",
                status_code=429,
            )

        rate_limit_key = f"pwd_reset_rate_limit:{cleaned_id}"
        hourly_count = cache.get(rate_limit_key, 0)
        if hourly_count >= 5:
            raise DomainException(
                detail="Maximum reset requests exceeded for this hour. Please try again later.",
                code="OTP_RATE_LIMIT_EXCEEDED",
                status_code=429,
            )

        # Look up user by email or mobile number
        user = (
            User.objects.filter(
                models.Q(email=cleaned_id) | models.Q(mobile_number=identifier.strip())
            )
            .filter(is_active=True)
            .first()
        )

        # Generate 6-digit numeric OTP
        otp = generate_secure_numeric_code(6)
        otp_hash = cls._hash_otp(cleaned_id, otp)
        expires_at = timezone.now() + timedelta(seconds=cls.OTP_TTL_SECONDS)

        if user:
            with transaction.atomic():
                OTPVerification.objects.filter(
                    mobile_number=cleaned_id,
                    purpose=OTPVerification.PurposeChoices.PASSWORD_RESET,
                    is_used=False,
                ).update(is_used=True)

                OTPVerification.objects.create(
                    user=user,
                    mobile_number=cleaned_id,
                    otp_hash=otp_hash,
                    purpose=OTPVerification.PurposeChoices.PASSWORD_RESET,
                    attempts=0,
                    max_attempts=cls.OTP_MAX_ATTEMPTS,
                    expires_at=expires_at,
                )

            # Email dispatch if user has email
            if user.email:
                try:
                    send_mail(
                        subject="GQT Portal — Password Reset One-Time Password (OTP)",
                        message=(
                            f"Hello,\n\n"
                            f"You have requested to reset your password for the GQT Student Portal.\n\n"
                            f"Your One-Time Password (OTP) is: {otp}\n\n"
                            f"This OTP is valid for 5 minutes.\n"
                            f"If you did not request this change, please ignore this message.\n\n"
                            f"Regards,\n"
                            f"GQT Academic & Administrative Operations"
                        ),
                        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@gqt.edu"),
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                except Exception as mail_exc:
                    logger.warning(
                        f"Failed to dispatch password reset email to {user.email}: {mail_exc}"
                    )

            logger.info(f"[PASSWORD RESET OTP] Target: {cleaned_id} | Code: {otp}")

        cache.set(
            f"pwd_reset_otp:{cleaned_id}",
            {"otp_hash": otp_hash, "attempts": 0},
            timeout=cls.OTP_TTL_SECONDS,
        )
        cache.set(cooldown_key, True, timeout=cls.OTP_COOLDOWN_SECONDS)
        cache.set(rate_limit_key, hourly_count + 1, timeout=3600)

        is_email = "@" in cleaned_id
        masked = mask_email(cleaned_id) if is_email else mask_phone(cleaned_id)
        return {
            "target": masked,
            "channel": "email" if is_email else "mobile",
            "message": f"If an active account exists, a 6-digit OTP has been dispatched to {masked}.",
        }

    @classmethod
    def verify_password_reset_otp(
        cls, identifier: str, otp: str, ip_address: Optional[str] = None
    ) -> Dict[str, str]:
        """Validate the 6-digit OTP code and exchange for a secure reset token."""
        cleaned_id = identifier.strip().lower()
        now = timezone.now()

        otp_record = (
            OTPVerification.objects.filter(
                mobile_number=cleaned_id,
                purpose=OTPVerification.PurposeChoices.PASSWORD_RESET,
                is_used=False,
                expires_at__gte=now,
            )
            .order_by("-created_at")
            .first()
        )

        if not otp_record:
            raise DomainException(
                detail="Invalid or expired reset OTP code.",
                code="INVALID_OTP",
                status_code=400,
            )

        if otp_record.attempts >= otp_record.max_attempts:
            otp_record.is_used = True
            otp_record.save(update_fields=["is_used", "updated_at"])
            raise DomainException(
                detail="Maximum verification attempts exceeded. Please request a new OTP.",
                code="OTP_MAX_ATTEMPTS_EXCEEDED",
                status_code=400,
            )

        provided_hash = cls._hash_otp(cleaned_id, otp.strip())
        if otp_record.otp_hash != provided_hash:
            otp_record.attempts += 1
            otp_record.save(update_fields=["attempts", "updated_at"])
            raise DomainException(
                detail="Incorrect OTP code. Please check and try again.",
                code="INVALID_OTP",
                status_code=400,
            )

        # Mark OTP used
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used", "updated_at"])
        cache.delete(f"pwd_reset_otp:{cleaned_id}")

        user = otp_record.user
        if not user or not user.is_active:
            raise DomainException(
                detail="User account is inactive or not found.",
                code="ACCOUNT_INACTIVE",
                status_code=403,
            )

        # Generate temporary reset token
        raw_token = generate_secure_token(32)
        token_hash = cls._hash_token(raw_token)
        expires_at = timezone.now() + timedelta(minutes=cls.PASSWORD_RESET_TTL_MINUTES)

        PasswordResetRequest.objects.filter(user=user, is_used=False).update(is_used=True)
        PasswordResetRequest.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
        )

        return {
            "reset_token": raw_token,
            "message": "OTP verified successfully. You may now set your new password.",
        }

    @classmethod
    def request_password_reset(cls, email: str, ip_address: Optional[str] = None) -> bool:
        """Initiate tokenized password reset flow with anti-enumeration protection."""
        user = User.objects.filter(email=email).first()

        if (
            user
            and user.is_active
            and (
                user.role == User.RoleChoices.ADMIN
                or user.onboarding_status == User.OnboardingStatusChoices.ACTIVE
            )
        ):
            raw_token = generate_secure_token(32)
            token_hash = cls._hash_token(raw_token)
            expires_at = timezone.now() + timedelta(minutes=cls.PASSWORD_RESET_TTL_MINUTES)

            # Invalidate previous unused reset requests
            PasswordResetRequest.objects.filter(user=user, is_used=False).update(is_used=True)

            PasswordResetRequest.objects.create(
                user=user,
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
            )

            # In dev, log the reset token
            logger.info(f"[PASSWORD RESET TOKEN] Email: {email} | Token: {raw_token}")

        # Always return True to prevent account enumeration
        return True

    @classmethod
    def reset_password(
        cls,
        token: str,
        new_password: str,
        ip_address: Optional[str] = None,
    ) -> bool:
        """Validate reset token and update user password."""
        token_hash = cls._hash_token(token)
        now = timezone.now()

        reset_req = PasswordResetRequest.objects.filter(
            token_hash=token_hash,
            is_used=False,
            expires_at__gte=now,
        ).first()

        if not reset_req:
            raise DomainException(
                detail="Invalid or expired password reset token.",
                code="INVALID_RESET_TOKEN",
                status_code=400,
            )

        user = reset_req.user
        user.set_password(new_password)
        user.save(update_fields=["password", "updated_at"])

        reset_req.is_used = True
        reset_req.save(update_fields=["is_used", "updated_at"])

        AuditLog.objects.create(
            actor=user,
            action="PASSWORD_RESET_COMPLETED",
            target_model="User",
            target_id=str(user.id),
            ip_address=ip_address,
            payload={"method": "tokenized_reset"},
        )
        return True

    @classmethod
    def reset_password_flexible(
        cls,
        new_password: str,
        token: Optional[str] = None,
        identifier: Optional[str] = None,
        otp: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """Reset password using either a verified reset token or direct OTP verification."""
        if token and token.strip():
            return cls.reset_password(token.strip(), new_password, ip_address)

        if identifier and otp:
            verify_res = cls.verify_password_reset_otp(identifier, otp, ip_address)
            return cls.reset_password(verify_res["reset_token"], new_password, ip_address)

        raise DomainException(
            detail="A valid reset token or (identifier + OTP) must be provided.",
            code="INVALID_PARAMETERS",
            status_code=400,
        )

    @classmethod
    def issue_tokens_for_user(cls, user: User) -> Tuple[str, str]:
        """Issue access and refresh JWT tokens with custom claims."""
        refresh = RefreshToken.for_user(user)
        refresh["role"] = user.role
        refresh["onboarding_status"] = user.onboarding_status
        return str(refresh.access_token), str(refresh)

    @classmethod
    def get_user_profile_data(cls, user: User) -> Dict[str, Any]:
        """Construct serialized user and linked profile dictionary."""
        data = {
            "id": str(user.id),
            "email": user.email,
            "mobile_number": user.mobile_number,
            "role": user.role,
            "is_active": user.is_active,
            "onboarding_status": user.onboarding_status,
        }

        if hasattr(user, "student_profile") and user.student_profile:
            p = user.student_profile
            data["student_profile"] = {
                "id": str(p.id),
                "student_id_number": p.student_id_number,
                "full_name": p.full_name,
                "batch_code": p.batch_code,
                "college_name": p.college_name,
                "graduation_year": p.graduation_year,
                "dob": str(p.dob) if p.dob else None,
                "branch": p.branch,
                "bio": p.bio,
                "github_url": p.github_url,
                "linkedin_url": p.linkedin_url,
                "course_opted": p.course_opted,
                "attendance_percentage": str(p.attendance_percentage),
                "total_classes": p.total_classes,
                "attended_classes": p.attended_classes,
                "current_streak_days": p.current_streak_days,
                "highest_streak_days": p.highest_streak_days,
                "total_points": str(p.total_points),
                "avatar_url": p.avatar_url,
            }
        elif hasattr(user, "admin_profile") and user.admin_profile:
            ap = user.admin_profile
            data["admin_profile"] = {
                "id": str(ap.id),
                "full_name": ap.full_name,
                "designation": ap.designation,
                "department": ap.department,
                "phone_number": ap.phone_number,
                "bio": ap.bio,
                "avatar_url": ap.avatar_url,
                "can_review_projects": ap.can_review_projects,
                "can_manage_curriculum": ap.can_manage_curriculum,
            }

        return data


class StudentProvisioningService:
    """Administrative service to provision and manage student accounts."""

    @classmethod
    @transaction.atomic
    def provision_student(
        cls,
        admin_user: User,
        full_name: str,
        student_id_number: str,
        batch_code: str,
        email: Optional[str] = None,
        mobile_number: Optional[str] = None,
        password: Optional[str] = None,
        college_name: str = "",
        graduation_year: Optional[int] = None,
        onboarding_status: str = User.OnboardingStatusChoices.ACTIVE,
        ip_address: Optional[str] = None,
    ) -> Tuple[User, StudentProfile]:
        """Admin creates student with approved email and mobile number."""
        if not email and not mobile_number:
            raise DomainException("Student must have either an approved email or mobile number.")

        if email and User.objects.filter(email=email).exists():
            raise DomainException("An account with this email already exists.")

        if mobile_number and User.objects.filter(mobile_number=mobile_number).exists():
            raise DomainException("An account with this mobile number already exists.")

        if StudentProfile.objects.filter(student_id_number=student_id_number).exists():
            raise DomainException("A student with this ID number already exists.")

        user = User.objects.create_user(
            email=email,
            mobile_number=mobile_number,
            password=password,
            role=User.RoleChoices.STUDENT,
            onboarding_status=onboarding_status,
            is_active=True,
        )

        profile = StudentProfile.objects.create(
            user=user,
            student_id_number=student_id_number,
            full_name=full_name,
            batch_code=batch_code,
            college_name=college_name,
            graduation_year=graduation_year,
        )

        AuditLog.objects.create(
            actor=admin_user,
            action="STUDENT_PROVISIONED",
            target_model="StudentProfile",
            target_id=str(profile.id),
            ip_address=ip_address,
            payload={
                "student_id_number": student_id_number,
                "full_name": full_name,
                "batch_code": batch_code,
                "email": email,
                "mobile_number": mobile_number,
                "onboarding_status": onboarding_status,
            },
        )
        return user, profile

    @classmethod
    @transaction.atomic
    def update_student_status(
        cls,
        admin_user: User,
        student_profile_id: str,
        is_active: Optional[bool] = None,
        onboarding_status: Optional[str] = None,
        reason: str = "",
        ip_address: Optional[str] = None,
    ) -> StudentProfile:
        """Admin activates/deactivates student or grants/revokes portal access."""
        profile = (
            StudentProfile.objects.select_related("user").filter(id=student_profile_id).first()
        )
        if not profile:
            raise DomainException("Student profile not found.", status_code=404)

        user = profile.user
        update_fields = ["updated_at"]

        if is_active is not None:
            user.is_active = is_active
            update_fields.append("is_active")

        if onboarding_status is not None:
            if onboarding_status not in User.OnboardingStatusChoices.values:
                raise DomainException("Invalid onboarding status specified.")
            user.onboarding_status = onboarding_status
            update_fields.append("onboarding_status")

        user.save(update_fields=update_fields)

        AuditLog.objects.create(
            actor=admin_user,
            action="STUDENT_STATUS_UPDATED",
            target_model="StudentProfile",
            target_id=str(profile.id),
            ip_address=ip_address,
            payload={
                "is_active": user.is_active,
                "onboarding_status": user.onboarding_status,
                "reason": reason,
            },
        )
        return profile
