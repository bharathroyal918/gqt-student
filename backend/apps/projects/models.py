from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Project(BaseModel):
    """Capstone and milestone projects assigned to students."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    description = models.TextField(help_text="Detailed markdown project specifications")
    deliverables_instructions = models.TextField(
        help_text="Instructions for repository and demo submission"
    )
    course = models.ForeignKey(
        "courses.Course",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
    )
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("10.00"))
    due_date = models.DateTimeField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ProjectSubmission(BaseModel):
    """Capstone project submission by an enrolled student."""

    class SubmissionStatus(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        CHANGES_REQUESTED = "CHANGES_REQUESTED", "Changes Requested"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="project_submissions"
    )
    github_repository_url = models.URLField(max_length=500, blank=True, default="")
    live_demo_url = models.URLField(max_length=500, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=30,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.SUBMITTED,
        db_index=True,
    )
    score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True, help_text="Evaluated project score"
    )
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_projects",
    )

    class Meta:
        verbose_name = "Project Submission"
        verbose_name_plural = "Project Submissions"
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "student"], name="unique_student_project_submission"
            )
        ]
        indexes = [
            models.Index(fields=["project", "status"], name="proj_subm_status_idx"),
            models.Index(fields=["student", "status"], name="proj_student_status_idx"),
        ]

    def __str__(self):
        return f"{self.project.title} by {self.student} [{self.status}]"


class ProjectFile(BaseModel):
    """Uploaded assets, documentation, or ZIP archives for project submission."""

    submission = models.ForeignKey(
        ProjectSubmission, on_delete=models.CASCADE, related_name="files"
    )
    file = models.FileField(upload_to="project_files/%Y/%m/")
    file_name = models.CharField(max_length=255)
    file_size_bytes = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Project File"
        verbose_name_plural = "Project Files"

    def __str__(self):
        return f"{self.file_name} ({self.file_size_bytes} bytes)"


class ProjectFeedback(BaseModel):
    """Institutional review comments, rubric feedback, and grading notes."""

    submission = models.ForeignKey(
        ProjectSubmission, on_delete=models.CASCADE, related_name="feedbacks"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="given_project_feedbacks"
    )
    feedback_text = models.TextField()
    suggested_changes = models.TextField(blank=True, default="")
    rating = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Rating on a 1-5 scale"
    )

    class Meta:
        verbose_name = "Project Feedback"
        verbose_name_plural = "Project Feedbacks"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Feedback by {self.reviewer} on {self.submission_id}"
