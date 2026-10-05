from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel, TimeStampedModel, UUIDModel


class StudentProfile(BaseModel):
    """Core academic profile for enrolled students."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile"
    )
    student_id_number = models.CharField(max_length=50, unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    batch_code = models.CharField(max_length=50, db_index=True)
    college_name = models.CharField(max_length=255, blank=True, default="")
    graduation_year = models.PositiveIntegerField(null=True, blank=True)

    # Student Editable profile extensions
    dob = models.DateField(null=True, blank=True)
    branch = models.CharField(max_length=100, blank=True, default="Computer Science")
    bio = models.TextField(blank=True, default="")
    github_url = models.URLField(max_length=255, blank=True, default="")
    linkedin_url = models.URLField(max_length=255, blank=True, default="")

    # Fixed course opted (assigned by institutional admin)
    course_opted = models.CharField(
        max_length=200, blank=True, default="Full Stack Software & Assessment Track"
    )

    # Attendance telemetry
    attendance_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("100.00"), db_index=True
    )
    total_classes = models.PositiveIntegerField(default=45)
    attended_classes = models.PositiveIntegerField(default=45)

    # Gamification & Progress
    current_streak_days = models.PositiveIntegerField(default=0)
    highest_streak_days = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True, help_text="Date of last solved problem for streak tracking")
    total_points = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), db_index=True
    )
    avatar_url = models.URLField(max_length=500, blank=True, default="")

    class Meta:
        verbose_name = "Student Profile"
        verbose_name_plural = "Student Profiles"
        indexes = [
            models.Index(fields=["batch_code", "-total_points"], name="batch_points_idx"),
            models.Index(fields=["-total_points"], name="global_points_idx"),
            models.Index(fields=["user", "batch_code"], name="student_user_batch_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_points__gte=Decimal("0.00")),
                name="non_negative_student_points",
            ),
            models.CheckConstraint(
                condition=models.Q(current_streak_days__lte=models.F("highest_streak_days")),
                name="current_streak_lte_highest",
            ),
        ]

    def recalculate_attendance(self):
        """Calculate live attendance percentage based on total and attended sessions."""
        if self.total_classes > 0:
            pct = (Decimal(self.attended_classes) / Decimal(self.total_classes)) * Decimal("100.00")
            self.attendance_percentage = min(Decimal("100.00"), max(Decimal("0.00"), round(pct, 2)))
        else:
            self.attendance_percentage = Decimal("100.00")

    def record_activity_and_update_streak(self, activity_date=None):
        """Update consecutive daily problem solving streak.
        - If already solved today: no duplicate increment.
        - If solved yesterday: increment streak by 1.
        - If missed yesterday or first time: reset streak to 1.
        - Update highest streak if current exceeds it.
        """
        from datetime import timedelta
        from django.utils import timezone

        if activity_date is None:
            activity_date = timezone.localdate()

        yesterday = activity_date - timedelta(days=1)

        if self.last_activity_date == activity_date:
            # Already solved today
            return self.current_streak_days

        if self.last_activity_date == yesterday:
            self.current_streak_days += 1
        else:
            self.current_streak_days = 1

        self.last_activity_date = activity_date
        if self.current_streak_days > self.highest_streak_days:
            self.highest_streak_days = self.current_streak_days

        self.save(update_fields=["current_streak_days", "highest_streak_days", "last_activity_date", "updated_at"])
        return self.current_streak_days

    def get_effective_streak(self, current_date=None):
        """Calculate effective streak. If user missed yesterday and today, returns 0."""
        from datetime import timedelta
        from django.utils import timezone

        if current_date is None:
            current_date = timezone.localdate()

        if not self.last_activity_date:
            return 0

        yesterday = current_date - timedelta(days=1)
        if self.last_activity_date == current_date or self.last_activity_date == yesterday:
            return self.current_streak_days
        return 0

    def clean(self):
        super().clean()
        if self.current_streak_days > self.highest_streak_days:
            self.highest_streak_days = self.current_streak_days
        self.recalculate_attendance()

    def save(self, *args, **kwargs):
        self.recalculate_attendance()
        super().save(*args, **kwargs)
        try:
            from apps.leaderboard.services import LeaderboardService
            LeaderboardService.invalidate_cache(batch_code=self.batch_code)
        except Exception:
            pass

    def __str__(self):
        return f"{self.full_name} ({self.student_id_number})"


class AttendanceRecord(UUIDModel, TimeStampedModel):
    """Daily or session attendance tracking for enrolled students."""

    class AttendanceStatus(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EXCUSED = "EXCUSED", "Excused"

    student_profile = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="attendance_records"
    )
    date = models.DateField(db_index=True)
    session_title = models.CharField(max_length=200, default="Daily Training & Coding Lab")
    status = models.CharField(
        max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT
    )
    remarks = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["student_profile", "date"], name="attendance_stud_date_idx"),
            models.Index(fields=["date", "status"], name="attendance_date_status_idx"),
        ]

    def __str__(self):
        return f"{self.student_profile.full_name} - {self.date}: {self.status}"
