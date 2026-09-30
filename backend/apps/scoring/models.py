from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class ScoreRecord(BaseModel):
    """Reliable single source of truth for points awarded to a student."""

    class SourceType(models.TextChoices):
        ASSIGNMENT = "ASSIGNMENT", "Coding Assignment"
        DAILY_TASK = "DAILY_TASK", "Daily Task"
        PROJECT = "PROJECT", "Capstone Project"
        STREAK_BONUS = "STREAK_BONUS", "Streak Bonus"
        ADMIN_ADJUSTMENT = "ADMIN_ADJUSTMENT", "Administrative Adjustment"

    class ScoringPolicy(models.TextChoices):
        FULL = "FULL", "Full Credit"
        HALF = "HALF", "Half Credit"
        ZERO = "ZERO", "Zero Credit"
        MANUAL = "MANUAL", "Manual Review"

    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="score_records"
    )
    source_type = models.CharField(max_length=30, choices=SourceType.choices, db_index=True)
    source_id = models.UUIDField(
        db_index=True, help_text="ID of QuestionSubmission, TaskCompletion, etc."
    )
    points = models.DecimalField(max_digits=7, decimal_places=2)
    policy_applied = models.CharField(
        max_length=20, choices=ScoringPolicy.choices, default=ScoringPolicy.FULL
    )
    awarded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    awarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="awarded_scores",
    )

    class Meta:
        verbose_name = "Score Record"
        verbose_name_plural = "Score Records"
        ordering = ["-awarded_at"]
        indexes = [
            models.Index(fields=["student", "source_type"], name="score_student_src_idx"),
            models.Index(fields=["source_type", "source_id"], name="score_source_lookup_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "source_type", "source_id"],
                name="unique_student_source_score_record",
            )
        ]

    def __str__(self):
        return f"{self.student}: {self.points} pts via {self.source_type}"


class ScoreEvent(BaseModel):
    """Audit log of points transactions, adjustments, or recalculations."""

    class EventType(models.TextChoices):
        SUBMISSION_EVALUATED = "SUBMISSION_EVALUATED", "Submission Evaluated"
        ADMIN_OVERRIDE = "ADMIN_OVERRIDE", "Admin Override"
        STREAK_BONUS_ADDED = "STREAK_BONUS_ADDED", "Streak Bonus Added"
        DEDUCTION = "DEDUCTION", "Score Deduction"
        RECALCULATION = "RECALCULATION", "Recalculation"

    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="score_events"
    )
    score_record = models.ForeignKey(
        ScoreRecord, null=True, blank=True, on_delete=models.CASCADE, related_name="events"
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    delta = models.DecimalField(max_digits=7, decimal_places=2)
    reason = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Score Event"
        verbose_name_plural = "Score Events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "created_at"], name="score_event_student_date_idx"),
        ]

    def __str__(self):
        return f"[{self.event_type}] {self.delta} pts for {self.student}"


class LeaderboardSnapshot(BaseModel):
    """Periodic frozen point-in-time leaderboard snapshot for historical trend analysis."""

    snapshot_date = models.DateField(db_index=True)
    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="leaderboard_snapshots"
    )
    batch_code = models.CharField(max_length=50, db_index=True)
    total_score = models.DecimalField(max_digits=10, decimal_places=2)
    global_rank = models.PositiveIntegerField(db_index=True)
    batch_rank = models.PositiveIntegerField(db_index=True)
    streak_days = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Leaderboard Snapshot"
        verbose_name_plural = "Leaderboard Snapshots"
        ordering = ["snapshot_date", "global_rank"]
        indexes = [
            models.Index(
                fields=["snapshot_date", "batch_code", "batch_rank"],
                name="lb_snap_date_batch_idx",
            ),
            models.Index(
                fields=["snapshot_date", "global_rank"],
                name="lb_snap_date_global_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["snapshot_date", "student"],
                name="unique_daily_student_leaderboard_snapshot",
            )
        ]

    def __str__(self):
        return f"{self.snapshot_date}: #{self.global_rank} {self.student} ({self.total_score} pts)"
