from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel


class Module(BaseModel):
    """Represents a sequential learning topic unit (e.g. 1. Data Types, 2. If-Else)."""

    course = models.ForeignKey(
        "courses.Course", on_delete=models.CASCADE, related_name="modules"
    )
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180)
    order_index = models.PositiveSmallIntegerField(db_index=True)
    summary = models.TextField(blank=True, default="")
    lecture_content = models.TextField(blank=True, default="")
    passing_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("80.00")
    )
    is_published = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Curriculum Module"
        verbose_name_plural = "Curriculum Modules"
        ordering = ["course", "order_index"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order_index"], name="unique_course_module_order"
            ),
            models.UniqueConstraint(
                fields=["course", "slug"], name="unique_course_module_slug"
            ),
            models.CheckConstraint(
                condition=models.Q(passing_percentage__gte=Decimal("0.00"))
                & models.Q(passing_percentage__lte=Decimal("100.00")),
                name="valid_module_passing_percentage",
            ),
        ]

    def __str__(self):
        return f"{self.order_index}. {self.title}"


class ModulePrerequisite(BaseModel):
    """Explicit prerequisite dependency rule between modules."""

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="prerequisites"
    )
    prerequisite_module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="dependent_modules"
    )

    class Meta:
        verbose_name = "Module Prerequisite"
        verbose_name_plural = "Module Prerequisites"
        constraints = [
            models.UniqueConstraint(
                fields=["module", "prerequisite_module"],
                name="unique_module_prerequisite",
            ),
            models.CheckConstraint(
                condition=~models.Q(module=models.F("prerequisite_module")),
                name="prevent_self_prerequisite",
            ),
        ]

    def clean(self):
        super().clean()
        if self.module_id == self.prerequisite_module_id:
            raise ValidationError("A module cannot be a prerequisite of itself.")
        if self.module.order_index <= self.prerequisite_module.order_index:
            raise ValidationError(
                "Prerequisite module order_index must precede the target module."
            )

    def __str__(self):
        return f"{self.prerequisite_module.title} -> {self.module.title}"


class StudentModuleProgress(BaseModel):
    """Reliable source of truth for student progress and completion across modules."""

    class ModuleStatus(models.TextChoices):
        LOCKED = "LOCKED", "Locked"
        UNLOCKED = "UNLOCKED", "Unlocked"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="module_progresses",
    )
    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="student_progresses"
    )
    status = models.CharField(
        max_length=20,
        choices=ModuleStatus.choices,
        default=ModuleStatus.LOCKED,
        db_index=True,
    )
    score_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    unlocked_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    unlocked_by_override = models.BooleanField(default=False)
    override_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="granted_module_overrides",
    )

    class Meta:
        verbose_name = "Student Module Progress"
        verbose_name_plural = "Student Module Progresses"
        indexes = [
            models.Index(
                fields=["student", "status"], name="mod_prog_student_status_idx"
            ),
            models.Index(
                fields=["module", "status"], name="mod_prog_module_status_idx"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "module"], name="unique_student_module_progress"
            ),
            models.CheckConstraint(
                condition=models.Q(score_percentage__gte=Decimal("0.00"))
                & models.Q(score_percentage__lte=Decimal("100.00")),
                name="valid_module_score_percentage",
            ),
        ]

    def __str__(self):
        return f"{self.student}: {self.module.title} [{self.status}]"
