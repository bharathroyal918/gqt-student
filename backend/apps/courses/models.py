from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class Course(BaseModel):
    """Institutional course curriculum container."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    thumbnail_url = models.URLField(max_length=500, blank=True, default="")
    is_published = models.BooleanField(default=False, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)
    order = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_courses",
    )

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ["order", "title"]
        indexes = [
            models.Index(fields=["is_published", "is_deleted"], name="course_pub_del_idx"),
        ]

    def delete(self, using=None, keep_parents=False):
        """Soft-deletion preserves academic historical records."""
        self.is_deleted = True
        self.save(update_fields=["is_deleted", "updated_at"])

    def __str__(self):
        return self.title


class CourseEnrollment(BaseModel):
    """Student enrollment record for a specific course."""

    class EnrollmentStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        REVOKED = "REVOKED", "Revoked"
        SUSPENDED = "SUSPENDED", "Suspended"

    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ACTIVE,
        db_index=True,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Course Enrollment"
        verbose_name_plural = "Course Enrollments"
        indexes = [
            models.Index(fields=["student", "status"], name="enrollment_student_status_idx"),
            models.Index(fields=["course", "status"], name="enrollment_course_status_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"], name="unique_student_course_enrollment"
            )
        ]

    def __str__(self):
        return f"{self.student} in {self.course.title} ({self.status})"


class RecordedClass(BaseModel):
    """Recorded video lecture / class session within a course."""

    class VideoSourceType(models.TextChoices):
        YOUTUBE = "YOUTUBE", "YouTube Link"
        DIRECT = "DIRECT", "Direct Upload / Video File"
        EXTERNAL = "EXTERNAL", "External URL / Stream"

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="recorded_classes"
    )
    module = models.ForeignKey(
        "modules.Module",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recorded_classes",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280)
    description = models.TextField(blank=True, default="")
    order_index = models.PositiveIntegerField(default=1, db_index=True)
    video_source_type = models.CharField(
        max_length=20,
        choices=VideoSourceType.choices,
        default=VideoSourceType.YOUTUBE,
        db_index=True,
    )
    youtube_url = models.URLField(max_length=500, blank=True, default="")
    youtube_video_id = models.CharField(max_length=100, blank=True, default="")
    video_file = models.FileField(
        upload_to="courses/videos/%Y/%m/",
        blank=True,
        null=True,
        help_text="Direct video upload for self-hosted / Supabase storage video lectures",
    )
    video_url = models.URLField(
        max_length=1000,
        blank=True,
        default="",
        help_text="Direct streaming URL or cloud storage URL",
    )
    duration_seconds = models.PositiveIntegerField(default=0)
    duration_formatted = models.CharField(max_length=20, blank=True, default="00:00")
    thumbnail_url = models.URLField(max_length=500, blank=True, default="")
    is_preview = models.BooleanField(
        default=False,
        help_text="Explicit preview override flag. Note: First 5 videos are always free preview.",
    )
    is_published = models.BooleanField(default=True, db_index=True)
    notes = models.TextField(blank=True, default="", help_text="Markdown lecture notes or syllabus summary")
    resources_url = models.URLField(max_length=500, blank=True, default="", help_text="Repository or supplementary materials URL")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_recorded_classes",
    )

    class Meta:
        verbose_name = "Recorded Class"
        verbose_name_plural = "Recorded Classes"
        ordering = ["order_index", "created_at"]
        indexes = [
            models.Index(fields=["course", "is_published", "order_index"], name="rec_class_course_pub_ord_idx"),
            models.Index(fields=["course", "order_index"], name="rec_class_course_ord_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "slug"], name="unique_course_recorded_class_slug"
            ),
        ]

    @staticmethod
    def extract_youtube_id(url: str) -> str:
        """Extract YouTube video ID from various YouTube URL formats."""
        if not url:
            return ""
        url = url.strip()
        import re

        # Regex covering:
        # https://www.youtube.com/watch?v=VIDEO_ID
        # https://youtu.be/VIDEO_ID
        # https://www.youtube.com/embed/VIDEO_ID
        # https://www.youtube.com/shorts/VIDEO_ID
        # https://www.youtube.com/v/VIDEO_ID
        patterns = [
            r"(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/|^)([A-Za-z0-9_-]{11})",
            r"[?&]v=([A-Za-z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    @property
    def is_free_preview(self) -> bool:
        """First 5 videos in any course are unlocked free previews for all registered students."""
        return bool(self.order_index <= 5 or self.is_preview)

    def save(self, *args, **kwargs):
        if self.video_source_type == self.VideoSourceType.YOUTUBE and self.youtube_url:
            yt_id = self.extract_youtube_id(self.youtube_url)
            if yt_id:
                self.youtube_video_id = yt_id
                if not self.thumbnail_url:
                    self.thumbnail_url = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"

        if self.duration_seconds > 0 and (not self.duration_formatted or self.duration_formatted == "00:00"):
            mins, secs = divmod(self.duration_seconds, 60)
            hrs, mins = divmod(mins, 60)
            if hrs > 0:
                self.duration_formatted = f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                self.duration_formatted = f"{mins:02d}:{secs:02d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.title} - #{self.order_index} {self.title}"


class StudentRecordedClassProgress(BaseModel):
    """Student viewing and completion progress for recorded classes."""

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="recorded_class_progresses",
    )
    recorded_class = models.ForeignKey(
        RecordedClass,
        on_delete=models.CASCADE,
        related_name="student_progresses",
    )
    last_position_seconds = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Student Recorded Class Progress"
        verbose_name_plural = "Student Recorded Class Progresses"
        indexes = [
            models.Index(fields=["student", "is_completed"], name="rec_prog_student_comp_idx"),
            models.Index(fields=["recorded_class", "is_completed"], name="rec_prog_class_comp_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "recorded_class"], name="unique_student_recorded_class_progress"
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.recorded_class.title} ({'Completed' if self.is_completed else 'In Progress'})"
