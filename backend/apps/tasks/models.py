"""Models for Daily Practice Tasks and Student Completions."""

from datetime import timedelta
from decimal import Decimal
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel


class Task(BaseModel):
    """Daily practice challenge scheduled for students with deadlines and cohort scoping."""

    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Pending"
        COMPLETED = "COMPLETED", "Completed"
        DUE_SOON = "DUE_SOON", "Due Soon"
        OVERDUE = "OVERDUE", "Overdue"

    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_date = models.DateField(null=True, blank=True, db_index=True)
    deadline = models.DateTimeField(null=True, blank=True, db_index=True)
    question = models.ForeignKey(
        "assignments.CodingQuestion",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="daily_tasks",
    )
    points = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("20.00"))
    is_active = models.BooleanField(default=True, db_index=True)

    # Scoping / Target assignment
    batch_code = models.CharField(max_length=50, blank=True, default="", db_index=True)
    course = models.ForeignKey(
        "courses.Course",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="daily_tasks",
    )
    assigned_student = models.ForeignKey(
        "students.StudentProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
    )

    class Meta:
        verbose_name = "Daily Task"
        verbose_name_plural = "Daily Tasks"
        ordering = ["-scheduled_date", "-created_at"]
        indexes = [
            models.Index(fields=["is_active", "deadline"], name="task_active_deadline_idx"),
            models.Index(fields=["batch_code", "is_active"], name="task_batch_active_idx"),
        ]

    def __str__(self):
        date_str = str(self.scheduled_date) if self.scheduled_date else "Unscheduled"
        return f"{date_str}: {self.title}"

    def compute_student_status(self, is_completed: bool) -> str:
        """Determines the live status of the task for a student (COMPLETED, OVERDUE, DUE_SOON, PENDING)."""
        if is_completed:
            return self.StatusChoices.COMPLETED

        if self.deadline:
            now = timezone.now()
            if self.deadline < now:
                return self.StatusChoices.OVERDUE
            elif self.deadline <= now + timedelta(hours=24):
                return self.StatusChoices.DUE_SOON

        return self.StatusChoices.PENDING


class StudentTask(BaseModel):
    """Record of a student completing a daily practice task challenge."""

    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="task_completions"
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="completions")
    is_completed = models.BooleanField(default=True)
    completed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    score_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("20.00"))
    submission_notes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Student Task Completion"
        verbose_name_plural = "Student Task Completions"
        ordering = ["-completed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "task"], name="unique_student_daily_task_completion"
            )
        ]
        indexes = [
            models.Index(fields=["student", "completed_at"], name="student_task_comp_date_idx"),
        ]

    def __str__(self):
        return f"{self.student} completed {self.task.title} ({self.score_awarded} pts)"
