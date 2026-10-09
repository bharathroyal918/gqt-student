from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class ContactInquiry(BaseModel):
    """Student support and helpdesk ticket queries."""

    class CategoryChoices(models.TextChoices):
        TECHNICAL_SUPPORT = "TECHNICAL_SUPPORT", "Technical Support"
        COURSE_DOUBT = "COURSE_DOUBT", "Course / Curriculum Doubt"
        ACCOUNT_ISSUE = "ACCOUNT_ISSUE", "Account / Login Issue"
        GENERAL_FEEDBACK = "GENERAL_FEEDBACK", "General Feedback"

    class InquiryStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        INVESTIGATING = "INVESTIGATING", "Investigating"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="contact_inquiries",
    )
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=255)
    subject = models.CharField(max_length=200)
    category = models.CharField(
        max_length=30,
        choices=CategoryChoices.choices,
        default=CategoryChoices.TECHNICAL_SUPPORT,
        db_index=True,
    )
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=InquiryStatus.choices,
        default=InquiryStatus.PENDING,
        db_index=True,
    )
    admin_notes = models.TextField(blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, default="")
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resolved_inquiries",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Contact Inquiry"
        verbose_name_plural = "Contact Inquiries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["status", "-created_at"], name="contact_status_date_idx"
            ),
            models.Index(fields=["category", "status"], name="contact_cat_status_idx"),
        ]

    def __str__(self):
        return f"[{self.status}] {self.subject} from {self.email}"
