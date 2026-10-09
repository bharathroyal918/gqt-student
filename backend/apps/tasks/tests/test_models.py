from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.students.models import StudentProfile
from apps.tasks.models import StudentTask, Task

User = get_user_model()


class TaskModelTests(TestCase):
    """Test suite for daily task and student task completion models."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="task.student@gqt.local", password="Password123!"
        )
        self.student = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-005",
            full_name="Task Student",
            batch_code="BATCH-2026-A",
        )
        self.today = date.today()
        self.task = Task.objects.create(
            title="Daily Array Rotation",
            description="Rotate an array to the right by K steps.",
            scheduled_date=self.today,
            deadline=timezone.now() + timedelta(days=2),
            points=Decimal("20.00"),
        )

    def test_student_task_completion_uniqueness(self):
        completion = StudentTask.objects.create(
            student=self.student,
            task=self.task,
            is_completed=True,
            score_awarded=Decimal("20.00"),
        )
        self.assertEqual(completion.student, self.student)
        self.assertEqual(completion.task, self.task)

        # Cannot record duplicate completion for the same daily task
        with self.assertRaises(IntegrityError):
            StudentTask.objects.create(
                student=self.student,
                task=self.task,
            )

    def test_compute_student_status(self):
        # 1. Not completed, future deadline -> PENDING
        self.assertEqual(
            self.task.compute_student_status(is_completed=False), "PENDING"
        )

        # 2. Completed -> COMPLETED
        self.assertEqual(
            self.task.compute_student_status(is_completed=True), "COMPLETED"
        )

        # 3. Due soon -> DUE_SOON
        self.task.deadline = timezone.now() + timedelta(hours=10)
        self.assertEqual(
            self.task.compute_student_status(is_completed=False), "DUE_SOON"
        )

        # 4. Overdue -> OVERDUE
        self.task.deadline = timezone.now() - timedelta(hours=10)
        self.assertEqual(
            self.task.compute_student_status(is_completed=False), "OVERDUE"
        )
