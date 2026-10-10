"""Admin service layer for secure TPO provisioning, college reassignment, and access lifecycle."""

import logging
from django.conf import settings
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from apps.accounts.models import AuditLog, PasswordResetRequest, TPOProfile, User
from apps.accounts.services import AuthService
from apps.common.exceptions import DomainException
from apps.common.utils import generate_secure_token, mask_email
from apps.students.models import College

logger = logging.getLogger(__name__)


class AdminTPOService:
    """Production service for administrative management of TPO accounts and college assignments."""

    @classmethod
    def list_tpos(cls, search: str | None = None, college_id: str | None = None, is_active: bool | None = None):
        """Queryset of TPO profiles with flexible multi-dimensional filtering."""
        qs = (
            TPOProfile.objects.select_related("user", "college", "assigned_by", "revoked_by")
            .all()
            .order_by("-created_at")
        )

        if search and search.strip():
            term = search.strip()
            qs = qs.filter(
                models.Q(full_name__icontains=term)
                | models.Q(user__email__icontains=term)
                | models.Q(designation__icontains=term)
                | models.Q(college__name__icontains=term)
                | models.Q(college__code__icontains=term)
            )

        if college_id:
            qs = qs.filter(college_id=college_id)

        if is_active is not None:
            qs = qs.filter(is_active=is_active)

        return qs

    @classmethod
    @transaction.atomic
    def provision_tpo(
        cls,
        admin_user: User,
        email: str,
        full_name: str,
        college_id: str,
        designation: str = "Training & Placement Officer",
        department: str = "Training & Placement Cell",
        phone_number: str = "",
        bio: str = "",
        ip_address: str | None = None,
    ) -> tuple[User, TPOProfile, str]:
        """Admin creates and provisions an authorized TPO account with college assignment and setup token."""
        clean_email = email.strip().lower()
        if not clean_email:
            raise DomainException(
                detail="A valid institutional email address is required.",
                code="INVALID_EMAIL",
                status_code=400,
            )

        # 1. Verify email uniqueness
        if User.objects.filter(email=clean_email).exists():
            existing_user = User.objects.filter(email=clean_email).first()
            role_label = existing_user.get_role_display() if existing_user else "User"
            raise DomainException(
                detail=f"An account with this email address already exists as {role_label}. Cannot silently convert role.",
                code="EMAIL_ALREADY_EXISTS",
                status_code=400,
            )

        # 2. Verify target college exists and is active
        college = College.objects.filter(id=college_id, is_active=True).first()
        if not college:
            raise DomainException(
                detail="The specified college was not found or is currently inactive.",
                code="COLLEGE_NOT_FOUND",
                status_code=400,
            )

        # 3. Create User account with TPO role
        # Set unusable initial password so the TPO must set their password via the secure activation link
        user = User.objects.create_user(
            email=clean_email,
            role=User.RoleChoices.TPO,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
            last_login_ip=ip_address,
        )

        # 4. Create TPOProfile
        tpo_profile = TPOProfile.objects.create(
            user=user,
            college=college,
            full_name=full_name.strip(),
            designation=designation.strip() or "Training & Placement Officer",
            department=department.strip() or "Training & Placement Cell",
            phone_number=phone_number.strip(),
            bio=bio.strip(),
            is_active=True,
            assigned_by=admin_user,
            assigned_at=timezone.now(),
        )

        # 5. Generate secure Password Reset / Setup Token
        raw_token = generate_secure_token(32)
        token_hash = AuthService._hash_token(raw_token)
        expires_at = timezone.now() + timezone.timedelta(hours=48)

        PasswordResetRequest.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
        )

        # 6. Record Audit Log
        AuditLog.objects.create(
            actor=admin_user,
            action="TPO_PROVISIONED",
            target_model="TPOProfile",
            target_id=str(tpo_profile.id),
            ip_address=ip_address,
            payload={
                "email": clean_email,
                "full_name": full_name,
                "college_id": str(college.id),
                "college_name": college.name,
                "college_code": college.code,
            },
        )

        # 7. Dispatch invitation email
        try:
            frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
            activation_link = f"{frontend_url}/reset-password?token={raw_token}"
            send_mail(
                subject="GQT Portal — Training & Placement Officer (TPO) Account Invitation",
                message=(
                    f"Hello {full_name},\n\n"
                    f"You have been invited as the Training & Placement Officer (TPO) for {college.name} "
                    f"on the GQT Student Learning and Assessment Portal.\n\n"
                    f"To activate your account and set your secure password, please click the link below:\n"
                    f"{activation_link}\n\n"
                    f"This activation link is valid for 48 hours.\n\n"
                    f"Regards,\n"
                    f"GQT Academic & Institutional Operations"
                ),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@gqt.edu"),
                recipient_list=[clean_email],
                fail_silently=True,
            )
        except Exception:
            logger.exception("Failed to dispatch invitation email to %s", mask_email(clean_email))

        return user, tpo_profile, raw_token

    @classmethod
    def get_tpo_detail(cls, tpo_id: str) -> TPOProfile:
        """Fetch single TPOProfile by UUID or raise 404 DomainException."""
        tpo = (
            TPOProfile.objects.select_related("user", "college", "assigned_by", "revoked_by")
            .filter(id=tpo_id)
            .first()
        )
        if not tpo:
            raise DomainException(
                detail="TPO profile not found.",
                code="TPO_NOT_FOUND",
                status_code=404,
            )
        return tpo

    @classmethod
    @transaction.atomic
    def update_tpo(cls, tpo_id: str, admin_user: User, ip_address: str | None = None, **data) -> TPOProfile:
        """Admin updates permitted metadata fields of a TPO profile."""
        tpo = cls.get_tpo_detail(tpo_id)

        update_fields = []
        for field in ["full_name", "designation", "department", "phone_number", "bio", "avatar_url"]:
            if field in data:
                setattr(tpo, field, data[field])
                update_fields.append(field)

        if update_fields:
            update_fields.append("updated_at")
            tpo.save(update_fields=update_fields)
            AuditLog.objects.create(
                actor=admin_user,
                action="TPO_METADATA_UPDATED",
                target_model="TPOProfile",
                target_id=str(tpo.id),
                ip_address=ip_address,
                payload={"updated_fields": [f for f in update_fields if f != "updated_at"]},
            )

        return tpo

    @classmethod
    @transaction.atomic
    def reassign_college(
        cls, tpo_id: str, new_college_id: str, admin_user: User, ip_address: str | None = None
    ) -> TPOProfile:
        """Atomically reassign a TPO to another active college and record previous assignment in audit history."""
        tpo = cls.get_tpo_detail(tpo_id)

        new_college = College.objects.filter(id=new_college_id, is_active=True).first()
        if not new_college:
            raise DomainException(
                detail="Target college not found or is currently inactive.",
                code="COLLEGE_NOT_FOUND",
                status_code=400,
            )

        old_college = tpo.college
        if old_college and old_college.id == new_college.id:
            return tpo  # Already assigned to this college

        tpo.college = new_college
        tpo.assigned_by = admin_user
        tpo.assigned_at = timezone.now()
        tpo.save(update_fields=["college", "assigned_by", "assigned_at", "updated_at"])

        # Record atomic audit event
        AuditLog.objects.create(
            actor=admin_user,
            action="TPO_COLLEGE_REASSIGNED",
            target_model="TPOProfile",
            target_id=str(tpo.id),
            ip_address=ip_address,
            payload={
                "previous_college_id": str(old_college.id) if old_college else None,
                "previous_college_name": old_college.name if old_college else "Unassigned",
                "new_college_id": str(new_college.id),
                "new_college_name": new_college.name,
                "new_college_code": new_college.code,
            },
        )

        return tpo

    @classmethod
    @transaction.atomic
    def deactivate_tpo(cls, tpo_id: str, admin_user: User, ip_address: str | None = None) -> TPOProfile:
        """Deactivate TPO authorization and revoke active sessions."""
        tpo = cls.get_tpo_detail(tpo_id)

        tpo.is_active = False
        tpo.revoked_by = admin_user
        tpo.revoked_at = timezone.now()
        tpo.save(update_fields=["is_active", "revoked_by", "revoked_at", "updated_at"])

        # Also deactivate user account
        user = tpo.user
        user.is_active = False
        user.save(update_fields=["is_active", "updated_at"])

        # Blacklist any outstanding refresh tokens for this user
        try:
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            logger.warning("Could not blacklist tokens for deactivated TPO user %s", user.id)

        AuditLog.objects.create(
            actor=admin_user,
            action="TPO_DEACTIVATED",
            target_model="TPOProfile",
            target_id=str(tpo.id),
            ip_address=ip_address,
            payload={
                "email": user.email,
                "college_id": str(tpo.college.id) if tpo.college else None,
                "college_name": tpo.college.name if tpo.college else "Unassigned",
            },
        )

        return tpo

    @classmethod
    @transaction.atomic
    def reactivate_tpo(cls, tpo_id: str, admin_user: User, ip_address: str | None = None) -> TPOProfile:
        """Reactivate a previously deactivated TPO account."""
        tpo = cls.get_tpo_detail(tpo_id)

        if not tpo.college or not tpo.college.is_active:
            raise DomainException(
                detail="Cannot reactivate TPO without an active college assignment. Please reassign to an active college first.",
                code="TPO_NO_ACTIVE_COLLEGE",
                status_code=400,
            )

        tpo.is_active = True
        tpo.revoked_by = None
        tpo.revoked_at = None
        tpo.save(update_fields=["is_active", "revoked_by", "revoked_at", "updated_at"])

        user = tpo.user
        user.is_active = True
        user.save(update_fields=["is_active", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="TPO_REACTIVATED",
            target_model="TPOProfile",
            target_id=str(tpo.id),
            ip_address=ip_address,
            payload={
                "email": user.email,
                "college_id": str(tpo.college.id),
                "college_name": tpo.college.name,
            },
        )

        return tpo

    @classmethod
    def get_tpo_audit_history(cls, tpo_id: str):
        """Retrieve audit trail of all administrative operations on this TPO."""
        cls.get_tpo_detail(tpo_id)  # verify existence
        return AuditLog.objects.filter(
            target_model="TPOProfile", target_id=str(tpo_id)
        ).select_related("actor").order_by("-created_at")
