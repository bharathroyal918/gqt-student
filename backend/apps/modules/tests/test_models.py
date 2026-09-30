from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.courses.models import Course
from apps.modules.models import Module, ModulePrerequisite, StudentModuleProgress
from apps.students.models import StudentProfile

User = get_user_model()


class ModuleModelTests(TestCase):
    """Test suite for Module, ModulePrerequisite, and StudentModuleProgress."""

    def setUp(self):
        self.user = User.objects.create_user(email="mod.student@gqt.local", password="Password123!")
        self.student = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-002",
            full_name="Module Student",
            batch_code="BATCH-2026-A",
        )
        self.course = Course.objects.create(
            title="Python Mastery",
            slug="python-mastery",
        )
        self.module_1 = Module.objects.create(
            course=self.course,
            title="Data Types",
            slug="data-types",
            order_index=1,
            passing_percentage=Decimal("80.00"),
        )
        self.module_2 = Module.objects.create(
            course=self.course,
            title="If-Else",
            slug="if-else",
            order_index=2,
            passing_percentage=Decimal("80.00"),
        )

    def test_unique_module_order_per_course(self):
        with self.assertRaises(IntegrityError):
            Module.objects.create(
                course=self.course,
                title="Duplicate Order Module",
                slug="dup-order",
                order_index=1,
            )

    def test_module_prerequisite_creation(self):
        prereq = ModulePrerequisite.objects.create(
            module=self.module_2,
            prerequisite_module=self.module_1,
        )
        self.assertEqual(prereq.module, self.module_2)
        self.assertEqual(prereq.prerequisite_module, self.module_1)

    def test_prevent_self_prerequisite(self):
        prereq = ModulePrerequisite(
            module=self.module_1,
            prerequisite_module=self.module_1,
        )
        with self.assertRaises(ValidationError):
            prereq.clean()

    def test_student_module_progress_unique_constraint(self):
        StudentModuleProgress.objects.create(
            student=self.student,
            module=self.module_1,
            status=StudentModuleProgress.ModuleStatus.UNLOCKED,
        )
        with self.assertRaises(IntegrityError):
            StudentModuleProgress.objects.create(
                student=self.student,
                module=self.module_1,
                status=StudentModuleProgress.ModuleStatus.IN_PROGRESS,
            )
