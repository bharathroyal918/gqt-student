from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


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

    current_streak_days = models.PositiveIntegerField(default=0)
    highest_streak_days = models.PositiveIntegerField(default=0)
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

    def clean(self):
        super().clean()
        if self.current_streak_days > self.highest_streak_days:
            self.highest_streak_days = self.current_streak_days

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            from apps.leaderboard.services import LeaderboardService
            LeaderboardService.invalidate_cache(batch_code=self.batch_code)
        except Exception:
            pass

    def __str__(self):
        return f"{self.full_name} ({self.student_id_number})"

