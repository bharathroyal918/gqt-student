"""Domain services for Contact module, Company Information, and Anti-Spam Rate Limiting."""

import logging
import uuid
from typing import Any

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import AuditLog, User
from apps.common.utils import mask_email
from apps.contact.models import ContactInquiry

logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = 600  # 10 minutes
RATE_LIMIT_MAX_SUBMISSIONS = 5  # Max 5 inquiries per IP within 10 minutes


class ContactService:
    """Service handling company info dissemination, rate limiting, and inquiry management."""

    @classmethod
    def get_company_info(cls) -> dict[str, Any]:
        """Return standardized public institutional contact information."""
        return {
            "company_name": "Global Quality Technologies (GQT)",
            "tagline": "Empowering Future Software Engineers with Industrial Coding Mastery",
            "support_email": "info@gqtech.in",
            "admissions_email": "info@gqtech.in",
            "phone_primary": "+91 9448403469",
            "phone_support": "+91 9448403469",
            "office_address": {
                "street": "324, 2nd floor, 3rd A Cross Rd, above City Union Bank, L/m:",
                "city": "Yelahanka New Town, Bengaluru",
                "state": "Karnataka",
                "postal_code": "560064",
                "country": "India",
            },
            "office_hours": "Monday to Saturday: 9:00 AM – 6:30 PM IST",
            "social_links": {
                "linkedin": "https://linkedin.com/company/gqt-technologies",
                "github": "https://github.com/gqt-technologies",
                "youtube": "https://youtube.com/@gqt-learning",
                "twitter": "https://twitter.com/gqt_tech",
            },
        }

    @classmethod
    def check_rate_limit(cls, identifier: str) -> None:
        """Enforce submission rate limits using Redis / LocMem cache to prevent spam."""
        cache_key = f"contact_rate_limit:{identifier}"
        current_count = cache.get(cache_key, 0)

        if current_count >= RATE_LIMIT_MAX_SUBMISSIONS:
            logger.warning(
                "Rate limit exceeded for contact inquiry submission from identifier: %s",
                identifier,
            )
            raise ValidationError(
                "You have exceeded the submission limit. Please wait 10 minutes before submitting another inquiry."
            )

        cache.set(cache_key, current_count + 1, timeout=RATE_LIMIT_WINDOW_SECONDS)

    @classmethod
    @transaction.atomic
    def submit_inquiry(
        cls,
        name: str,
        email: str,
        subject: str,
        message: str,
        category: str = ContactInquiry.CategoryChoices.TECHNICAL_SUPPORT,
        user: User | None = None,
        ip_address: str | None = None,
        user_agent: str = "",
        honeypot: str = "",
    ) -> ContactInquiry:
        """Validate, spam-check, rate-limit, and persist a contact inquiry."""
        # 1. Anti-spam honeypot detection: bots fill out hidden fields
        if honeypot.strip():
            logger.warning("Bot spam detected via honeypot field. Suppressing inquiry.")
            raise ValidationError("Invalid request payload.")

        # 2. Rate limiting check (keyed on IP address or User ID)
        limiter_key = (
            str(user.id)
            if user and user.is_authenticated
            else (ip_address or "anonymous")
        )
        cls.check_rate_limit(limiter_key)

        # 3. Validation
        clean_name = name.strip()
        clean_email = email.strip().lower()
        clean_subject = subject.strip()
        clean_message = message.strip()

        if len(clean_name) < 2:
            raise ValidationError("Name must contain at least 2 characters.")
        if len(clean_message) < 10:
            raise ValidationError("Message must contain at least 10 characters.")

        if category not in ContactInquiry.CategoryChoices.values:
            category = ContactInquiry.CategoryChoices.TECHNICAL_SUPPORT

        # 4. Create record
        inquiry = ContactInquiry.objects.create(
            user=user if user and user.is_authenticated else None,
            name=clean_name,
            email=clean_email,
            subject=clean_subject,
            category=category,
            message=clean_message,
            status=ContactInquiry.InquiryStatus.PENDING,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else "",
        )

        logger.info(
            "Contact inquiry #%s created from %s (%s)",
            inquiry.id,
            mask_email(clean_email),
            inquiry.category,
        )
        return inquiry

    @classmethod
    def list_admin_inquiries(
        cls,
        status_filter: str | None = None,
        category_filter: str | None = None,
        search: str | None = None,
    ):
        """Admin listing of submitted inquiries with filtering."""
        qs = ContactInquiry.objects.select_related("user", "resolved_by").order_by(
            "-created_at"
        )

        if status_filter:
            qs = qs.filter(status=status_filter)
        if category_filter:
            qs = qs.filter(category=category_filter)
        if search:
            from django.db.models import Q

            qs = qs.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(subject__icontains=search)
                | Q(message__icontains=search)
            )

        return qs

    @classmethod
    @transaction.atomic
    def update_inquiry_status(
        cls,
        inquiry_id: uuid.UUID,
        admin_user: User,
        status_val: str,
        admin_notes: str | None = None,
        ip_address: str | None = None,
    ) -> ContactInquiry:
        """Admin resolves, investigates, or closes an inquiry ticket."""
        inquiry = get_object_or_404(ContactInquiry, id=inquiry_id)

        if status_val not in ContactInquiry.InquiryStatus.values:
            raise ValidationError(f"Invalid status choice: {status_val}")

        inquiry.status = status_val
        if admin_notes is not None:
            inquiry.admin_notes = admin_notes.strip()

        if status_val in [
            ContactInquiry.InquiryStatus.RESOLVED,
            ContactInquiry.InquiryStatus.CLOSED,
        ]:
            inquiry.resolved_by = admin_user
            inquiry.resolved_at = timezone.now()

        inquiry.save()

        AuditLog.objects.create(
            actor=admin_user,
            action="CONTACT_INQUIRY_STATUS_UPDATED",
            target_model="ContactInquiry",
            target_id=str(inquiry.id),
            ip_address=ip_address,
            payload={"status": status_val, "admin_notes": admin_notes},
        )

        logger.info(
            "Admin %s updated inquiry %s to %s",
            mask_email(admin_user.email),
            inquiry.id,
            status_val,
        )
        return inquiry
