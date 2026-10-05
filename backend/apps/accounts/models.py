from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel, TimeStampedModel, UUIDModel


class UserManager(BaseUserManager):
    """Custom manager for the User model supporting email or mobile auth."""

    def create_user(self, email=None, mobile_number=None, password=None, **extra_fields):
        if not email and not mobile_number:
            raise ValueError("A user must have either an email address or mobile number.")

        if email:
            email = self.normalize_email(email)

        user = self.model(email=email, mobile_number=mobile_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.RoleChoices.ADMIN)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email=email, password=password, **extra_fields)


class Role(BaseModel):
    """Granular system roles and permission sets."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default="")
    permissions = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """Custom enterprise user model supporting Email/Pass and Mobile/OTP."""

    class RoleChoices(models.TextChoices):
        ADMIN = "ADMIN", "Administrator / Staff"
        STUDENT = "STUDENT", "Student"

    class OnboardingStatusChoices(models.TextChoices):
        PENDING_ACTIVATION = "PENDING_ACTIVATION", "Pending Activation"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    email = models.EmailField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    mobile_number = models.CharField(
        max_length=20, unique=True, null=True, blank=True, db_index=True
    )
    role = models.CharField(
        max_length=20, choices=RoleChoices.choices, default=RoleChoices.STUDENT, db_index=True
    )
    onboarding_status = models.CharField(
        max_length=30,
        choices=OnboardingStatusChoices.choices,
        default=OnboardingStatusChoices.ACTIVE,
        db_index=True,
    )

    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email", "is_active"], name="user_email_active_idx"),
            models.Index(fields=["mobile_number", "is_active"], name="user_mobile_active_idx"),
            models.Index(fields=["role", "is_active"], name="user_role_active_idx"),
        ]

    def clean(self):
        super().clean()
        if not self.email and not self.mobile_number:
            raise ValidationError("Either an email address or mobile number must be provided.")

    def __str__(self):
        return self.email or self.mobile_number or str(self.id)


class AdminProfile(BaseModel):
    """Profile extension for staff and institutional administrators."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="admin_profile")
    full_name = models.CharField(max_length=150, blank=True, default="Administrator")
    designation = models.CharField(max_length=100, blank=True, default="Portal Administrator")
    department = models.CharField(max_length=100, default="Academic Operations")
    phone_number = models.CharField(max_length=30, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    avatar_url = models.CharField(max_length=500, blank=True, default="")
    can_review_projects = models.BooleanField(default=True)
    can_manage_curriculum = models.BooleanField(default=True)

    def __str__(self):
        return f"AdminProfile: {self.full_name or self.user.email}"


class LoginActivity(UUIDModel, TimeStampedModel):
    """Audit log of all authentication attempts."""

    class LoginType(models.TextChoices):
        EMAIL_PASSWORD = "EMAIL_PASSWORD", "Email & Password"
        MOBILE_OTP = "MOBILE_OTP", "Mobile & OTP"
        TOKEN_REFRESH = "TOKEN_REFRESH", "Token Refresh"

    class LoginStatus(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED_CREDENTIALS = "FAILED_CREDENTIALS", "Failed Credentials"
        FAILED_OTP = "FAILED_OTP", "Failed OTP"
        LOCKED = "LOCKED", "Account Locked"

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="login_activities"
    )
    identifier = models.CharField(max_length=255, db_index=True)
    login_type = models.CharField(max_length=30, choices=LoginType.choices)
    status = models.CharField(max_length=30, choices=LoginStatus.choices, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True, default="")
    failure_reason = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Login Activity"
        verbose_name_plural = "Login Activities"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"], name="login_user_created_idx"),
            models.Index(fields=["ip_address", "created_at"], name="login_ip_created_idx"),
            models.Index(fields=["status", "created_at"], name="login_status_created_idx"),
        ]

    def __str__(self):
        return f"[{self.status}] {self.identifier} ({self.login_type}) at {self.created_at}"


class OTPVerification(UUIDModel, TimeStampedModel):
    """Lifecycle tracking for cryptographically generated one-time passwords."""

    class PurposeChoices(models.TextChoices):
        LOGIN = "LOGIN", "Login Authentication"
        PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"
        PHONE_VERIFY = "PHONE_VERIFY", "Phone Verification"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="otp_verifications"
    )
    mobile_number = models.CharField(max_length=20, db_index=True)
    otp_hash = models.CharField(max_length=128)
    purpose = models.CharField(
        max_length=30, choices=PurposeChoices.choices, default=PurposeChoices.LOGIN
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    is_used = models.BooleanField(default=False, db_index=True)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = "OTP Verification"
        verbose_name_plural = "OTP Verifications"
        indexes = [
            models.Index(
                fields=["mobile_number", "is_used", "expires_at"],
                name="otp_mobile_used_exp_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(attempts__lte=models.F("max_attempts")),
                name="otp_attempts_within_limit",
            )
        ]

    def is_valid(self) -> bool:
        return (
            not self.is_used
            and timezone.now() <= self.expires_at
            and self.attempts < self.max_attempts
        )

    def __str__(self):
        return f"OTP for {self.mobile_number} ({self.purpose})"


class PasswordResetRequest(UUIDModel, TimeStampedModel):
    """Tracks tokenized password reset workflows."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_resets")
    token_hash = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    is_used = models.BooleanField(default=False, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Password Reset Request"
        verbose_name_plural = "Password Reset Requests"
        indexes = [
            models.Index(fields=["token_hash", "is_used"], name="pwd_reset_token_used_idx"),
            models.Index(fields=["user", "is_used"], name="pwd_reset_user_used_idx"),
        ]

    def is_valid(self) -> bool:
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"Password reset for {self.user.email} (used={self.is_used})"


class AuditLog(UUIDModel, TimeStampedModel):
    """Immutable audit trail for compliance and administrative actions."""

    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="audit_logs")
    action = models.CharField(max_length=100, db_index=True)
    target_model = models.CharField(max_length=100, db_index=True)
    target_id = models.CharField(max_length=100, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    payload = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "created_at"], name="audit_actor_created_idx"),
            models.Index(fields=["target_model", "target_id"], name="audit_target_idx"),
        ]

    def __str__(self):
        return f"[{self.created_at}] {self.action} by {self.actor_id}"
