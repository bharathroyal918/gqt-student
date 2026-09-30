from django.db import models

from apps.common.models import BaseModel


class Badge(BaseModel):
    """Gamification badges awarded for academic milestones and coding streaks."""

    class CriteriaType(models.TextChoices):
        STREAK_MILESTONE = "STREAK_MILESTONE", "Streak Milestone"
        QUESTIONS_SOLVED = "QUESTIONS_SOLVED", "Questions Solved"
        MODULE_COMPLETION = "MODULE_COMPLETION", "Module Completion"
        COURSE_COMPLETION = "COURSE_COMPLETION", "Course Completion"
        PROJECT_COMPLETION = "PROJECT_COMPLETION", "Project Completion"
        ASSIGNMENT_ACHIEVEMENT = "ASSIGNMENT_ACHIEVEMENT", "Assignment Achievement"
        POINTS_MILESTONE = "POINTS_MILESTONE", "Points Milestone"
        LEADERBOARD_TOP = "LEADERBOARD_TOP", "Leaderboard Top Rank"
        PROJECT_EXCELLENCE = "PROJECT_EXCELLENCE", "Project Excellence"

    slug = models.SlugField(max_length=60, unique=True, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_url = models.CharField(max_length=500, blank=True, default="")
    criteria_type = models.CharField(max_length=40, choices=CriteriaType.choices)
    criteria_threshold = models.PositiveIntegerField(default=1)
    points_reward = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.criteria_type})"


class StudentBadge(BaseModel):
    """Junction table recording badges unlocked by students."""

    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="earned_badges"
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awarded_students")
    awarded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Student Badge"
        verbose_name_plural = "Student Badges"
        ordering = ["-awarded_at"]
        constraints = [
            models.UniqueConstraint(fields=["student", "badge"], name="unique_student_badge")
        ]

    def __str__(self):
        return f"{self.student} earned {self.badge.name}"


class Certificate(BaseModel):
    """Cryptographically verifiable institutional completion certificate."""

    certificate_id = models.CharField(
        max_length=64, unique=True, db_index=True, help_text="e.g. GQT-CERT-2026-XXXX"
    )
    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="certificates"
    )
    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="issued_certificates"
    )
    student_name = models.CharField(max_length=200, default="")
    course_title = models.CharField(max_length=200, default="")
    title = models.CharField(max_length=255, default="Certificate of Completion")
    verification_hash = models.CharField(max_length=64, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True, db_index=True)
    pdf_file = models.FileField(upload_to="certificates/%Y/", blank=True, null=True)
    is_revoked = models.BooleanField(default=False, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"
        ordering = ["-issued_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"], name="unique_student_course_certificate"
            )
        ]

    def __str__(self):
        return f"Certificate {self.certificate_id}: {self.student_name} in {self.course_title}"
