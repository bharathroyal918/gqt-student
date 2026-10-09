from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Notification(BaseModel):
    """Targeted user alerts for platform and academic events."""

    class NotificationType(models.TextChoices):
        TASK_DEADLINE = "TASK_DEADLINE", "Task Deadline Approaching"
        PROJECT_MARKED = "PROJECT_MARKED", "Project Marked"
        RANK_CHANGE = "RANK_CHANGE", "Rank Change"
        ADMIN_ANNOUNCEMENT = "ADMIN_ANNOUNCEMENT", "Admin Announcement"
        ACHIEVEMENT = "ACHIEVEMENT", "Achievement Unlocked"
        CERTIFICATE = "CERTIFICATE", "Certificate Issued"
        SUBMISSION_GRADED = "SUBMISSION_GRADED", "Submission Graded"
        MODULE_UNLOCKED = "MODULE_UNLOCKED", "Module Unlocked"
        PROJECT_FEEDBACK = "PROJECT_FEEDBACK", "Project Feedback"
        STREAK_ALERT = "STREAK_ALERT", "Streak Alert"
        DEADLINE_REMINDER = "DEADLINE_REMINDER", "Deadline Reminder"
        TASK_COMPLETED = "TASK_COMPLETED", "Task Completed"
        SYSTEM_NOTICE = "SYSTEM_NOTICE", "System Notice"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    notification_type = models.CharField(
        max_length=40,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM_NOTICE,
    )
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    action_url = models.CharField(max_length=500, blank=True, default="")
    idempotency_key = models.CharField(
        max_length=255, null=True, blank=True, unique=True, db_index=True
    )
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "is_read", "-created_at"],
                name="notif_recip_read_idx",
            ),
            models.Index(fields=["idempotency_key"], name="notif_idem_idx"),
        ]

    def __str__(self):
        return f"[{self.notification_type}] {self.title} to {self.recipient}"


class Announcement(BaseModel):
    """Institutional broadcasts targeted globally or to specific cohorts/batches."""

    class PriorityChoices(models.TextChoices):
        LOW = "LOW", "Low"
        NORMAL = "NORMAL", "Normal"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"

    class TargetAudienceChoices(models.TextChoices):
        ALL = "ALL", "All Students"
        BATCH = "BATCH", "Specific Batch"
        COURSE = "COURSE", "Course Enrollees"
        SPECIFIC = "SPECIFIC", "Selected Students"

    title = models.CharField(max_length=255)
    content = models.TextField(help_text="Markdown announcement content")
    target_audience = models.CharField(
        max_length=20,
        choices=TargetAudienceChoices.choices,
        default=TargetAudienceChoices.ALL,
        db_index=True,
    )
    target_batch = models.CharField(
        max_length=50,
        blank=True,
        default="",
        db_index=True,
        help_text="Batch code if targeting specific batch",
    )
    target_course = models.ForeignKey(
        "courses.Course",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="announcements",
    )
    priority = models.CharField(
        max_length=20,
        choices=PriorityChoices.choices,
        default=PriorityChoices.NORMAL,
        db_index=True,
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="published_announcements",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    delivery_count = models.PositiveIntegerField(default=0)
    email_sent_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["is_active", "is_published", "-created_at"],
                name="ann_active_pub_idx",
            ),
            models.Index(
                fields=["target_audience", "target_batch", "-created_at"],
                name="ann_aud_batch_idx",
            ),
        ]

    def __str__(self):
        scope = (
            self.target_batch
            if self.target_batch
            else (
                "Global"
                if self.target_audience == self.TargetAudienceChoices.ALL
                else self.target_audience
            )
        )
        return f"{self.title} ({scope}) [{self.priority}]"
