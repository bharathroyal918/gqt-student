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
