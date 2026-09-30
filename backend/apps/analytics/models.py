from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class ActivityEvent(BaseModel):
    """Event-level interaction tracking for engagement and diagnostics."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="activity_events",
    )
    event_name = models.CharField(max_length=100, db_index=True)
    entity_type = models.CharField(max_length=50, blank=True, default="")
    entity_id = models.CharField(max_length=64, blank=True, default="")
    properties = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Activity Event"
        verbose_name_plural = "Activity Events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "event_name", "-created_at"], name="act_user_evt_date_idx"
            ),
            models.Index(fields=["event_name", "-created_at"], name="act_name_date_idx"),
        ]

    def __str__(self):
        return f"Event '{self.event_name}' by User {self.user_id} at {self.created_at}"


class DailyStudentAnalytics(BaseModel):
    """Pre-aggregated daily activity summary for high-performance reporting."""

    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="daily_analytics"
    )
    date = models.DateField(db_index=True)
    submissions_count = models.PositiveIntegerField(default=0)
    questions_solved_count = models.PositiveIntegerField(default=0)
    time_spent_minutes = models.PositiveIntegerField(default=0)
    score_earned = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        verbose_name = "Daily Student Analytics"
        verbose_name_plural = "Daily Student Analytics"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date", "-score_earned"], name="daily_ana_date_score_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "date"], name="unique_student_daily_analytics"
            )
        ]

    def __str__(self):
        return f"{self.date}: {self.student} ({self.questions_solved_count} solved, {self.score_earned} pts)"


class ExportJob(BaseModel):
    """Asynchronous background reporting export job."""

    class ReportType(models.TextChoices):
        STUDENT_PERFORMANCE = "STUDENT_PERFORMANCE", "Student Performance"
        COURSE_STATISTICS = "COURSE_STATISTICS", "Course Statistics"
        ASSIGNMENT_COMPLETION = "ASSIGNMENT_COMPLETION", "Assignment Completion"
        PROJECT_PERFORMANCE = "PROJECT_PERFORMANCE", "Project Performance"
        MONTHLY_ACTIVITY = "MONTHLY_ACTIVITY", "Monthly Activity"
        FULL_EXECUTIVE = "FULL_EXECUTIVE", "Full Executive Report"

    class ExportFormat(models.TextChoices):
        CSV = "CSV", "Comma-Separated Values (CSV)"
        JSON = "JSON", "JavaScript Object Notation (JSON)"

    class JobStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="export_jobs",
    )
    report_type = models.CharField(max_length=50, choices=ReportType.choices, db_index=True)
    format = models.CharField(max_length=10, choices=ExportFormat.choices, default=ExportFormat.CSV)
    status = models.CharField(
        max_length=20, choices=JobStatus.choices, default=JobStatus.PENDING, db_index=True
    )
    filters = models.JSONField(default=dict, blank=True)
    file_name = models.CharField(max_length=255, blank=True, default="")
    file_path = models.CharField(max_length=500, blank=True, default="")
    file_size_bytes = models.BigIntegerField(default=0)
    row_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Export Job"
        verbose_name_plural = "Export Jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status", "-created_at"], name="exp_usr_stat_idx"),
            models.Index(fields=["report_type", "status"], name="exp_type_stat_idx"),
        ]

    def __str__(self):
        return f"ExportJob {self.id} [{self.report_type} - {self.status}]"

