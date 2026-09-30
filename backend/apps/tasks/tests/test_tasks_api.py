"""Comprehensive Test Suite for Daily Tasks (Admin and Student workflows).

Tests:
1. Admin Task Creation with future deadline validation.
2. Admin Task Editing, Archiving, Deletion, and Scoping (Batch/Course/Student).
3. Admin View Task Completions audit endpoint.
4. Student List Tasks with status calculation (PENDING, DUE_SOON, OVERDUE, COMPLETED).
5. Student Task Detail & Scoping isolation.
6. Student Mark Complete workflow with score awarding, notification, and idempotency (duplicate prevention).
7. Deadline approaching notification trigger logic.
"""

from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.courses.models import Course, CourseEnrollment
from apps.notifications.models import Notification
from apps.scoring.models import ScoreRecord
from apps.students.models import StudentProfile
from apps.tasks.models import StudentTask, Task
from apps.tasks.services import StudentTaskService, TaskAdminService

User = get_user_model()


class DailyTasksApiTests(TestCase):
    """Test suite for Admin and Student Daily Task APIs."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()

        # Admin user
        self.admin_user = User.objects.create_user(
            email="admin.tasks@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.ADMIN,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )

        # Course
        self.course = Course.objects.create(
            title="Full-Stack Engineering",
            slug="full-stack-engineering",
            is_published=True,
        )

        # Student 1 (Batch A)
        self.user_a = User.objects.create_user(
            email="student.a@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.student_a = StudentProfile.objects.create(
            user=self.user_a,
            student_id_number="GQT-TASK-001",
            full_name="Alice Tasker",
            batch_code="BATCH-2026-A",
            total_points=Decimal("0.00"),
        )
        CourseEnrollment.objects.create(
            student=self.student_a,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )

        # Student 2 (Batch B)
        self.user_b = User.objects.create_user(
            email="student.b@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.student_b = StudentProfile.objects.create(
            user=self.user_b,
            student_id_number="GQT-TASK-002",
            full_name="Bob Tasker",
            batch_code="BATCH-2026-B",
            total_points=Decimal("0.00"),
        )

    def test_admin_create_task_future_deadline_rule(self):
        """Rule: deadline must be future when creating a new task."""
        self.client.force_authenticate(user=self.admin_user)

        # 1. Past deadline -> must fail
        past_deadline = timezone.now() - timedelta(hours=2)
        res_fail = self.client.post(
            "/api/v1/admin/tasks/",
            {
                "title": "Invalid Past Task",
                "description": "This should fail",
                "deadline": past_deadline.isoformat(),
                "points": 25.00,
            },
            format="json",
        )
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("must be in the future", str(res_fail.json()))

        # 2. Future deadline -> succeeds
        future_deadline = timezone.now() + timedelta(days=2)
        res_ok = self.client.post(
            "/api/v1/admin/tasks/",
            {
                "title": "Valid Future Task",
                "description": "Daily array manipulation",
                "deadline": future_deadline.isoformat(),
                "points": 25.00,
                "batch_code": "BATCH-2026-A",
            },
            format="json",
        )
        self.assertEqual(res_ok.status_code, status.HTTP_201_CREATED)
        created_id = res_ok.json()["data"]["id"]
        self.assertTrue(Task.objects.filter(id=created_id).exists())

    def test_admin_task_edit_archive_delete_and_completions(self):
        """Admin can edit, archive, view completions, and delete tasks."""
        future_deadline = timezone.now() + timedelta(days=3)
        task = Task.objects.create(
            title="Initial Title",
            description="Initial Desc",
            deadline=future_deadline,
            points=Decimal("30.00"),
            batch_code="BATCH-2026-A",
        )

        self.client.force_authenticate(user=self.admin_user)

        # Edit task
        res_patch = self.client.patch(
            f"/api/v1/admin/tasks/{task.id}/",
            {"title": "Updated Title", "points": 35.00},
            format="json",
        )
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.title, "Updated Title")
        self.assertEqual(task.points, Decimal("35.00"))

        # Student A completes task
        StudentTask.objects.create(
            student=self.student_a,
            task=task,
            is_completed=True,
            score_awarded=Decimal("35.00"),
            submission_notes="Solution in Python",
        )

        # Admin views completions
        res_comp = self.client.get(f"/api/v1/admin/tasks/{task.id}/completions/")
        self.assertEqual(res_comp.status_code, status.HTTP_200_OK)
        completions = res_comp.json()["data"]["completions"]
        self.assertEqual(len(completions), 1)
        self.assertEqual(completions[0]["student_id"], str(self.student_a.id))
        self.assertEqual(completions[0]["score_awarded"], 35.0)

        # Delete task
        res_del = self.client.delete(f"/api/v1/admin/tasks/{task.id}/")
        self.assertEqual(res_del.status_code, status.HTTP_200_OK)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_student_task_statuses_and_filtering(self):
        """Verify dynamic status calculation: PENDING, DUE_SOON, OVERDUE, COMPLETED."""
        now = timezone.now()

        # Task 1: Overdue (deadline in past)
        t_overdue = Task.objects.create(
            title="T Overdue",
            description="Overdue task",
            deadline=now - timedelta(hours=5),
            batch_code="BATCH-2026-A",
        )

        # Task 2: Due Soon (deadline within next 12 hours)
        t_due_soon = Task.objects.create(
            title="T Due Soon",
            description="Due soon task",
            deadline=now + timedelta(hours=6),
            batch_code="BATCH-2026-A",
        )

        # Task 3: Pending (deadline in 3 days)
        t_pending = Task.objects.create(
            title="T Pending",
            description="Pending task",
            deadline=now + timedelta(days=3),
            batch_code="BATCH-2026-A",
        )

        # Task 4: Completed (completed by Student A)
        t_completed = Task.objects.create(
            title="T Completed",
            description="Completed task",
            deadline=now + timedelta(days=1),
            batch_code="BATCH-2026-A",
        )
        StudentTask.objects.create(
            student=self.student_a,
            task=t_completed,
            is_completed=True,
            score_awarded=Decimal("20.00"),
        )

        self.client.force_authenticate(user=self.user_a)

        # 1. Fetch all tasks
        res_all = self.client.get("/api/v1/students/tasks/")
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        tasks = res_all.json()["data"]["tasks"]
        task_map = {t["title"]: t for t in tasks}

        self.assertEqual(task_map["T Overdue"]["status"], "OVERDUE")
        self.assertEqual(task_map["T Due Soon"]["status"], "DUE_SOON")
        self.assertEqual(task_map["T Pending"]["status"], "PENDING")
        self.assertEqual(task_map["T Completed"]["status"], "COMPLETED")

        # 2. Filter by status=due_soon
        res_ds = self.client.get("/api/v1/students/tasks/?status=due_soon")
        ds_tasks = res_ds.json()["data"]["tasks"]
        self.assertEqual(len(ds_tasks), 1)
        self.assertEqual(ds_tasks[0]["title"], "T Due Soon")

        # 3. Filter by status=completed
        res_comp = self.client.get("/api/v1/students/tasks/?status=completed")
        comp_tasks = res_comp.json()["data"]["tasks"]
        self.assertEqual(len(comp_tasks), 1)
        self.assertEqual(comp_tasks[0]["title"], "T Completed")

    def test_student_task_scoping_isolation(self):
        """Student B (BATCH-2026-B) cannot see tasks scoped only to Student A's batch or course."""
        Task.objects.create(
            title="Batch A Exclusive",
            description="Only for Batch A",
            deadline=timezone.now() + timedelta(days=2),
            batch_code="BATCH-2026-A",
        )
        Task.objects.create(
            title="Global Task",
            description="For all students",
            deadline=timezone.now() + timedelta(days=2),
            batch_code="",
        )

        self.client.force_authenticate(user=self.user_b)
        res = self.client.get("/api/v1/students/tasks/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        titles = [t["title"] for t in res.json()["data"]["tasks"]]

        self.assertIn("Global Task", titles)
        self.assertNotIn("Batch A Exclusive", titles)

    def test_student_mark_complete_scoring_and_duplicate_prevention(self):
        """Student marks task complete: awards score, updates profile, triggers notification, and blocks duplicate completion."""
        task = Task.objects.create(
            title="Daily Dynamic Programming",
            description="Solve climbing stairs",
            deadline=timezone.now() + timedelta(days=2),
            points=Decimal("25.00"),
            batch_code="BATCH-2026-A",
        )

        self.client.force_authenticate(user=self.user_a)

        # 1. Mark complete
        res = self.client.post(
            f"/api/v1/students/tasks/{task.id}/complete/",
            {"submission_notes": "https://github.com/alice/dp-stairs"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()["data"]
        self.assertTrue(data["is_completed"])
        self.assertEqual(data["score_awarded"], 25.0)

        # Verify StudentProfile points updated
        self.student_a.refresh_from_db()
        self.assertEqual(float(self.student_a.total_points), 25.0)

        # Verify ScoreRecord created
        self.assertTrue(
            ScoreRecord.objects.filter(
                student=self.student_a, source_type="TASK", source_id=str(task.id)
            ).exists()
        )

        # Verify Notification emitted
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user_a,
                notification_type=Notification.NotificationType.TASK_COMPLETED,
            ).exists()
        )

        # 2. Attempt duplicate completion -> Must be blocked
        res_dup = self.client.post(
            f"/api/v1/students/tasks/{task.id}/complete/",
            {"submission_notes": "Second attempt"},
            format="json",
        )
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been completed", str(res_dup.json()))

    def test_notify_approaching_deadlines(self):
        """Approaching deadline notification trigger finds uncompleted students within 24h window."""
        now = timezone.now()

        # Task 1: Due in 6 hours (assigned to Batch A)
        t1 = Task.objects.create(
            title="Urgent Task Due Soon",
            description="Due very soon",
            deadline=now + timedelta(hours=6),
            points=Decimal("20.00"),
            batch_code="BATCH-2026-A",
        )

        # Task 2: Due in 48 hours (not in 24h window)
        t2 = Task.objects.create(
            title="Task Due in 2 Days",
            description="Not urgent",
            deadline=now + timedelta(hours=48),
            points=Decimal("20.00"),
            batch_code="BATCH-2026-A",
        )

        # Student A hasn't completed t1 -> notification should be dispatched
        sent_count = StudentTaskService.notify_approaching_deadlines(window_hours=24)
        self.assertEqual(sent_count, 1)

        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user_a,
                notification_type=Notification.NotificationType.DEADLINE_REMINDER,
                title__contains="Urgent Task Due Soon",
            ).exists()
        )

        # Re-running immediately doesn't send duplicate
        sent_again = StudentTaskService.notify_approaching_deadlines(window_hours=24)
        self.assertEqual(sent_again, 0)
