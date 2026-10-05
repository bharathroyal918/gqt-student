from decimal import Decimal
from django.conf import settings
from django.db import models
from apps.common.models import BaseModel


class PlacementDrive(BaseModel):
    """Placement and internship drive organized for students."""

    class WorkMode(models.TextChoices):
        ON_SITE = "ON_SITE", "On-site"
        REMOTE = "REMOTE", "Remote"
        HYBRID = "HYBRID", "Hybrid"

    class DriveStatus(models.TextChoices):
        UPCOMING = "UPCOMING", "Upcoming"
        ONGOING = "ONGOING", "Active / Ongoing"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    company_name = models.CharField(max_length=200, db_index=True)
    company_code = models.CharField(max_length=50, blank=True, default="", help_text="e.g. GQT-TCS-2026")
    company_logo_url = models.URLField(max_length=500, blank=True, default="")
    role = models.CharField(max_length=200, help_text="e.g. Full Stack Developer, SDE-1")
    skills = models.TextField(help_text="Required skills, comma-separated e.g. React, Node.js, Python, SQL")
    location = models.CharField(max_length=200, default="Bengaluru, Karnataka")
    mode_of_work = models.CharField(
        max_length=20, choices=WorkMode.choices, default=WorkMode.ON_SITE, db_index=True
    )
    stipend_or_ctc = models.CharField(
        max_length=150, help_text="e.g. 6.5 - 8.5 LPA or 25,000/month Internship + PPO"
    )
    bond_period = models.CharField(
        max_length=150, default="None", help_text="e.g. None, 1 Year Service Agreement, 2 Years"
    )
    eligibility_criteria = models.TextField(
        default="B.Tech/BE (CSE/ISE/ECE/IT), Min 60% or 6.0 CGPA, No active backlogs",
        help_text="Detailed academic and stream criteria"
    )
    min_cgpa = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("0.00"), help_text="Minimum CGPA required (0 for no cutoff)"
    )
    eligible_batches = models.CharField(
        max_length=255, default="2025, 2026", help_text="Eligible graduating batches"
    )
    job_description = models.TextField(help_text="Full job profile, responsibilities, and interview process")
    application_deadline = models.DateTimeField(db_index=True)
    drive_date = models.DateTimeField(null=True, blank=True, help_text="Scheduled drive or interview date")
    status = models.CharField(
        max_length=20, choices=DriveStatus.choices, default=DriveStatus.ONGOING, db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_placement_drives",
    )

    class Meta:
        verbose_name = "Placement Drive"
        verbose_name_plural = "Placement Drives"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_active", "-application_deadline"], name="drive_status_active_idx"),
            models.Index(fields=["company_name", "role"], name="drive_comp_role_idx"),
        ]

    def __str__(self):
        return f"{self.company_name} - {self.role} ({self.status})"


class PlacementApplication(BaseModel):
    """Student application for an institutional placement drive."""

    class ApplicationStatus(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        SELECTED = "SELECTED", "Selected / Offered"
        REJECTED = "REJECTED", "Rejected"

    drive = models.ForeignKey(
        PlacementDrive, on_delete=models.CASCADE, related_name="applications"
    )
    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="placement_applications"
    )
    status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.APPLIED,
        db_index=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_placement_applications",
    )
    admin_notes = models.TextField(blank=True, default="", help_text="Internal feedback / assessment notes")
    rejection_reason = models.TextField(blank=True, default="", help_text="Reason shared or logged if rejected")

    # Captured Student Profile Data & Application Snapshot
    student_name = models.CharField(max_length=150)
    student_id_number = models.CharField(max_length=50)
    email = models.EmailField(max_length=254)
    phone_number = models.CharField(max_length=30, blank=True, default="")
    college_name = models.CharField(max_length=255, blank=True, default="")
    branch = models.CharField(max_length=100, blank=True, default="Computer Science")
    graduation_year = models.PositiveIntegerField(null=True, blank=True)
    cgpa_or_percentage = models.CharField(max_length=50, blank=True, default="")
    resume_file = models.FileField(
        upload_to="placement_resumes/%Y/%m/",
        null=True,
        blank=True,
        help_text="Directly uploaded student resume file (PDF/DOCX)",
    )
    resume_filename = models.CharField(max_length=255, blank=True, default="")
    resume_url = models.URLField(max_length=500, blank=True, default="", help_text="Google Drive / Cloud storage link")
    portfolio_url = models.URLField(max_length=500, blank=True, default="")
    github_url = models.URLField(max_length=500, blank=True, default="")
    linkedin_url = models.URLField(max_length=500, blank=True, default="")
    skills_summary = models.TextField(blank=True, default="")
    cover_note = models.TextField(blank=True, default="", help_text="Student's message or statement of intent")

    class Meta:
        verbose_name = "Placement Application"
        verbose_name_plural = "Placement Applications"
        ordering = ["-submitted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["drive", "student"], name="unique_student_drive_application"
            )
        ]
        indexes = [
            models.Index(fields=["drive", "status"], name="drive_app_status_idx"),
            models.Index(fields=["student", "status"], name="stud_app_status_idx"),
            models.Index(fields=["status", "-submitted_at"], name="app_status_time_idx"),
        ]

    def __str__(self):
        return f"{self.student_name} ({self.student_id_number}) -> {self.drive.company_name} [{self.status}]"
