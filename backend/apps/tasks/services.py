"""Domain services for Daily Practice Tasks and Student Task Progression."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.db import models, transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import AuditLog, User
from apps.assignments.models import CodingQuestion
from apps.common.exceptions import DomainException
from apps.courses.models import Course, CourseEnrollment
from apps.notifications.models import Notification
from apps.scoring.services import ScoringService
from apps.students.models import StudentProfile
from apps.tasks.models import StudentTask, Task


class TaskAdminService:
    """Service managing daily practice tasks, calendar scheduling, deadlines, and cohort assignments."""

    @classmethod
    def get_task(cls, task_id: str) -> Task:
        return get_object_or_404(
            Task.objects.select_related("question", "course", "assigned_student").prefetch_related("completions__student__user"),
            id=task_id,
        )

    @classmethod
    @transaction.atomic
    def create_task(
        cls,
        admin_user: User,
        title: str,
        description: str,
        scheduled_date: Optional[date] = None,
        deadline: Optional[datetime] = None,
        question_id: Optional[str] = None,
        points: Decimal = Decimal("20.00"),
        batch_code: Optional[str] = None,
        course_id: Optional[str] = None,
        assigned_student_id: Optional[str] = None,
        is_active: bool = True,
        ip_address: Optional[str] = None,
    ) -> Task:
        # Rule: Deadline must be in the future when creating a task
        if deadline is not None and deadline <= timezone.now():
            raise DomainException("Task deadline must be in the future when creating a new task.")

        question = None
        if question_id:
            question = get_object_or_404(CodingQuestion, id=question_id)

        course = None
        if course_id:
            course = get_object_or_404(Course, id=course_id)

        assigned_student = None
        if assigned_student_id:
            assigned_student = get_object_or_404(StudentProfile, id=assigned_student_id)

        task = Task.objects.create(
            title=title.strip(),
            description=description.strip(),
            scheduled_date=scheduled_date,
            deadline=deadline,
            question=question,
            points=points,
            batch_code=batch_code.strip() if batch_code else "",
            course=course,
            assigned_student=assigned_student,
            is_active=is_active,
        )

        AuditLog.objects.create(
            actor=admin_user,
            action="TASK_CREATED",
            target_model="Task",
            target_id=str(task.id),
            ip_address=ip_address,
            payload={
                "title": task.title,
                "points": str(points),
                "scheduled_date": str(scheduled_date) if scheduled_date else None,
                "deadline": deadline.isoformat() if deadline else None,
                "batch_code": task.batch_code,
            },
        )
        return task

    @classmethod
    @transaction.atomic
    def update_task(
        cls,
        task_id: str,
        admin_user: User,
        title: Optional[str] = None,
        description: Optional[str] = None,
        scheduled_date: Optional[date] = None,
        deadline: Optional[datetime] = None,
        question_id: Optional[str] = None,
        points: Optional[Decimal] = None,
        batch_code: Optional[str] = None,
        course_id: Optional[str] = None,
        assigned_student_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        ip_address: Optional[str] = None,
    ) -> Task:
        task = cls.get_task(task_id)
        update_fields = ["updated_at"]

        if title is not None:
            task.title = title.strip()
            update_fields.append("title")

        if description is not None:
            task.description = description.strip()
            update_fields.append("description")

        if scheduled_date is not None:
            task.scheduled_date = scheduled_date
            update_fields.append("scheduled_date")

        if deadline is not None:
            if deadline <= timezone.now():
                raise DomainException("Updated deadline must be in the future.")
            task.deadline = deadline
            update_fields.append("deadline")

        if question_id is not None:
            if question_id == "":
                task.question = None
            else:
                task.question = get_object_or_404(CodingQuestion, id=question_id)
            update_fields.append("question")

        if course_id is not None:
            if course_id == "":
                task.course = None
            else:
                task.course = get_object_or_404(Course, id=course_id)
            update_fields.append("course")

        if assigned_student_id is not None:
            if assigned_student_id == "":
                task.assigned_student = None
            else:
                task.assigned_student = get_object_or_404(StudentProfile, id=assigned_student_id)
            update_fields.append("assigned_student")

        if batch_code is not None:
            task.batch_code = batch_code.strip()
            update_fields.append("batch_code")

        if points is not None:
            task.points = points
            update_fields.append("points")

        if is_active is not None:
            task.is_active = is_active
            update_fields.append("is_active")

        task.save(update_fields=update_fields)

        AuditLog.objects.create(
            actor=admin_user,
            action="TASK_UPDATED",
            target_model="Task",
            target_id=str(task.id),
            ip_address=ip_address,
            payload={"updated_fields": update_fields},
        )
        return task

    @classmethod
    @transaction.atomic
    def archive_task(cls, task_id: str, admin_user: User, ip_address: Optional[str] = None) -> Task:
        task = cls.get_task(task_id)
        task.is_active = False
        task.save(update_fields=["is_active", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="TASK_ARCHIVED",
            target_model="Task",
            target_id=str(task.id),
            ip_address=ip_address,
        )
        return task

    @classmethod
    @transaction.atomic
    def delete_task(cls, task_id: str, admin_user: User, ip_address: Optional[str] = None) -> None:
        task = cls.get_task(task_id)
        task_title = task.title
        task.delete()

        AuditLog.objects.create(
            actor=admin_user,
            action="TASK_DELETED",
            target_model="Task",
            target_id=task_id,
            ip_address=ip_address,
            payload={"title": task_title},
        )

    @classmethod
    def get_task_completions(cls, task_id: str) -> List[Dict[str, Any]]:
        task = cls.get_task(task_id)
        completions = task.completions.select_related("student__user").order_by("-completed_at")
        
        return [
            {
                "id": str(c.id),
                "student_id": str(c.student.id),
                "student_id_number": c.student.student_id_number,
                "full_name": c.student.full_name,
                "email": c.student.user.email,
                "batch_code": c.student.batch_code,
                "is_completed": c.is_completed,
                "completed_at": c.completed_at,
                "score_awarded": float(c.score_awarded),
                "submission_notes": c.submission_notes,
            }
            for c in completions
        ]


class StudentTaskService:
    """Service providing student task queries, status telemetry, completion marking, and deadline alerts."""

    @classmethod
    def get_assigned_tasks_queryset(cls, student: StudentProfile):
        """Returns all active tasks scoped to the student (assigned individually, by batch, enrolled course, or global)."""
        enrolled_course_ids = CourseEnrollment.objects.filter(
            student=student, status=CourseEnrollment.EnrollmentStatus.ACTIVE
        ).values_list("course_id", flat=True)

        scope_filter = (
            Q(assigned_student=student)
            | Q(batch_code=student.batch_code)
            | Q(course_id__in=enrolled_course_ids)
            | (Q(assigned_student__isnull=True) & Q(batch_code="") & Q(course__isnull=True))
        )

        return (
            Task.objects.filter(is_active=True)
            .filter(scope_filter)
            .select_related("question", "course")
            .prefetch_related(
                Prefetch(
                    "completions",
                    queryset=StudentTask.objects.filter(student=student),
                    to_attr="student_completion",
                )
            )
            .order_by("deadline", "-scheduled_date", "-created_at")
        )

    @classmethod
    def get_student_tasks(
        cls, student: StudentProfile, status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        tasks = cls.get_assigned_tasks_queryset(student)
        results = []

        now = timezone.now()

        for task in tasks:
            completions = getattr(task, "student_completion", [])
            completion = completions[0] if completions else None
            is_completed = bool(completion and completion.is_completed)

            computed_status = task.compute_student_status(is_completed)

            # Deadline status indicator
            if is_completed:
                deadline_status = "COMPLETED"
            elif task.deadline:
                if task.deadline < now:
                    deadline_status = "OVERDUE"
                elif task.deadline <= now + timedelta(hours=24):
                    deadline_status = "DUE_SOON"
                else:
                    deadline_status = "UPCOMING"
            else:
                deadline_status = "NO_DEADLINE"

            task_payload = {
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                "scheduled_date": str(task.scheduled_date) if task.scheduled_date else None,
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "points": float(task.points),
                "question_id": str(task.question.id) if task.question else None,
                "question_title": task.question.title if task.question else None,
                "course_id": str(task.course.id) if task.course else None,
                "course_title": task.course.title if task.course else None,
                "status": computed_status,
                "deadline_status": deadline_status,
                "is_completed": is_completed,
                "completed_at": completion.completed_at if completion else None,
                "score_awarded": float(completion.score_awarded) if completion else 0.0,
                "submission_notes": completion.submission_notes if completion else "",
            }

            if status_filter and status_filter.upper() != "ALL":
                if computed_status != status_filter.upper():
                    continue

            results.append(task_payload)

        return results

    @classmethod
    def get_student_task_detail(cls, student: StudentProfile, task_id: str) -> Dict[str, Any]:
        tasks = cls.get_assigned_tasks_queryset(student).filter(id=task_id)
        task = tasks.first()
        if not task:
            raise DomainException("Task not found or not assigned to you.")

        completions = getattr(task, "student_completion", [])
        completion = completions[0] if completions else None
        is_completed = bool(completion and completion.is_completed)
        computed_status = task.compute_student_status(is_completed)

        now = timezone.now()
        if is_completed:
            deadline_status = "COMPLETED"
        elif task.deadline:
            if task.deadline < now:
                deadline_status = "OVERDUE"
            elif task.deadline <= now + timedelta(hours=24):
                deadline_status = "DUE_SOON"
            else:
                deadline_status = "UPCOMING"
        else:
            deadline_status = "NO_DEADLINE"

        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "scheduled_date": str(task.scheduled_date) if task.scheduled_date else None,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "points": float(task.points),
            "question_id": str(task.question.id) if task.question else None,
            "question_title": task.question.title if task.question else None,
            "course_id": str(task.course.id) if task.course else None,
            "course_title": task.course.title if task.course else None,
            "status": computed_status,
            "deadline_status": deadline_status,
            "is_completed": is_completed,
            "completed_at": completion.completed_at if completion else None,
            "score_awarded": float(completion.score_awarded) if completion else 0.0,
            "submission_notes": completion.submission_notes if completion else "",
        }

    @classmethod
    @transaction.atomic
    def mark_task_complete(
        cls, student: StudentProfile, task_id: str, submission_notes: str = ""
    ) -> Dict[str, Any]:
        """Marks a daily task completed for the student, guarantees idempotency, and records scoring/events."""
        tasks = cls.get_assigned_tasks_queryset(student).filter(id=task_id)
        task = tasks.first()
        if not task:
            raise DomainException("Task not found or not assigned to you.")

        # Prevent duplicate completion
        existing = StudentTask.objects.filter(student=student, task=task).first()
        if existing and existing.is_completed:
            raise DomainException("This task has already been completed.")

        student_task, created = StudentTask.objects.update_or_create(
            student=student,
            task=task,
            defaults={
                "is_completed": True,
                "score_awarded": task.points,
                "submission_notes": submission_notes.strip(),
            },
        )

        # Process Score Change via centralized ScoringService
        ScoringService.process_score_change(
            student=student,
            source_type="TASK",
            source_id=str(task.id),
            new_points=task.points,
            policy_applied="FULL",
            reason=f"Completed Daily Task: {task.title}",
            notification_title=f"Task Completed: {task.title}",
            notification_body=f"Congratulations! You completed '{task.title}' and earned {task.points} points.",
        )

        # Emit completion notification
        Notification.objects.create(
            recipient=student.user,
            title=f"Daily Task Completed: {task.title}",
            body=f"You successfully completed the practice task '{task.title}' and earned {task.points} pts!",
            notification_type=Notification.NotificationType.TASK_COMPLETED,
            action_url=f"/tasks/{task.id}",
        )

        return {
            "id": str(student_task.id),
            "task_id": str(task.id),
            "student_id": str(student.id),
            "is_completed": True,
            "score_awarded": float(student_task.score_awarded),
            "completed_at": student_task.completed_at,
            "submission_notes": student_task.submission_notes,
            "status": "COMPLETED",
        }

    @classmethod
    def notify_approaching_deadlines(cls, window_hours: int = 24) -> int:
        """Finds active tasks with deadlines within the upcoming window and alerts uncompleted students."""
        now = timezone.now()
        upcoming_window = now + timedelta(hours=window_hours)

        tasks = Task.objects.filter(
            is_active=True,
            deadline__isnull=False,
            deadline__gt=now,
            deadline__lte=upcoming_window,
        ).select_related("course", "assigned_student")

        notifications_sent = 0

        for task in tasks:
            # Determine target students
            students_qs = StudentProfile.objects.filter(user__is_active=True)
            if task.assigned_student:
                students_qs = students_qs.filter(id=task.assigned_student.id)
            elif task.batch_code:
                students_qs = students_qs.filter(batch_code=task.batch_code)
            elif task.course:
                students_qs = students_qs.filter(
                    enrollments__course=task.course,
                    enrollments__status=CourseEnrollment.EnrollmentStatus.ACTIVE,
                )

            # Exclude students who already completed the task
            completed_student_ids = task.completions.filter(is_completed=True).values_list(
                "student_id", flat=True
            )
            uncompleted_students = students_qs.exclude(id__in=completed_student_ids)

            for student in uncompleted_students:
                # Avoid spamming multiple notifications for the same task in the same 24 hours
                recent_alert_exists = Notification.objects.filter(
                    recipient=student.user,
                    notification_type=Notification.NotificationType.DEADLINE_REMINDER,
                    title__contains=task.title,
                    created_at__gte=now - timedelta(hours=12),
                ).exists()

                if not recent_alert_exists:
                    time_remaining = task.deadline - now
                    hours_left = max(1, int(time_remaining.total_seconds() // 3600))
                    Notification.objects.create(
                        recipient=student.user,
                        title=f"Deadline Approaching: {task.title}",
                        body=f"Task '{task.title}' is due in ~{hours_left} hours ({task.deadline.strftime('%Y-%m-%d %H:%M')}). Complete it to earn {task.points} points!",
                        notification_type=Notification.NotificationType.DEADLINE_REMINDER,
                        action_url=f"/tasks/{task.id}",
                    )
                    notifications_sent += 1

        return notifications_sent
