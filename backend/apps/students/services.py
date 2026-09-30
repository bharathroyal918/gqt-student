"""Domain services for administrative student management, enrollments, and academic reporting."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.shortcuts import get_object_or_404

from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum

from apps.accounts.models import AuditLog, User
from apps.assignments.models import CodeSubmission, CodingQuestion, StudentQuestionProgress
from apps.certificates.models import StudentBadge
from apps.common.exceptions import DomainException
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.notifications.models import Notification
from apps.scoring.models import ScoreEvent, ScoreRecord
from apps.students.models import StudentProfile
from apps.tasks.models import StudentTask


class StudentAdminService:
    """Administrative service handling student modifications, course assignments, and tracking."""

    @classmethod
    def get_student_detail(cls, student_id: str) -> StudentProfile:
        return get_object_or_404(
            StudentProfile.objects.select_related("user").prefetch_related("enrollments__course"),
            id=student_id,
        )

    @classmethod
    @transaction.atomic
    def update_student(
        cls,
        student_id: str,
        admin_user: User,
        full_name: Optional[str] = None,
        batch_code: Optional[str] = None,
        college_name: Optional[str] = None,
        graduation_year: Optional[int] = None,
        email: Optional[str] = None,
        mobile_number: Optional[str] = None,
        is_active: Optional[bool] = None,
        onboarding_status: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> StudentProfile:
        student = cls.get_student_detail(student_id)
        user = student.user
        updated_fields_profile = ["updated_at"]
        updated_fields_user = ["updated_at"]

        if full_name is not None:
            student.full_name = full_name.strip()
            updated_fields_profile.append("full_name")

        if batch_code is not None:
            student.batch_code = batch_code.strip()
            updated_fields_profile.append("batch_code")

        if college_name is not None:
            student.college_name = college_name.strip()
            updated_fields_profile.append("college_name")

        if graduation_year is not None:
            student.graduation_year = graduation_year
            updated_fields_profile.append("graduation_year")

        if email is not None:
            email_clean = email.strip().lower()
            if email_clean and User.objects.filter(email=email_clean).exclude(id=user.id).exists():
                raise DomainException("An account with this email already exists.")
            user.email = email_clean or None
            updated_fields_user.append("email")

        if mobile_number is not None:
            mob_clean = mobile_number.strip()
            if (
                mob_clean
                and User.objects.filter(mobile_number=mob_clean).exclude(id=user.id).exists()
            ):
                raise DomainException("An account with this mobile number already exists.")
            user.mobile_number = mob_clean or None
            updated_fields_user.append("mobile_number")

        if is_active is not None:
            user.is_active = is_active
            updated_fields_user.append("is_active")

        if onboarding_status is not None:
            if onboarding_status not in User.OnboardingStatusChoices.values:
                raise DomainException("Invalid onboarding status specified.")
            user.onboarding_status = onboarding_status
            updated_fields_user.append("onboarding_status")

        if len(updated_fields_user) > 1:
            user.save(update_fields=updated_fields_user)
        if len(updated_fields_profile) > 1:
            student.save(update_fields=updated_fields_profile)

        AuditLog.objects.create(
            actor=admin_user,
            action="STUDENT_UPDATED",
            target_model="StudentProfile",
            target_id=str(student.id),
            ip_address=ip_address,
            payload={
                "updated_profile_fields": updated_fields_profile,
                "updated_user_fields": updated_fields_user,
            },
        )
        return student

    @classmethod
    @transaction.atomic
    def assign_courses(
        cls,
        student_id: str,
        course_ids: List[str],
        admin_user: User,
        ip_address: Optional[str] = None,
    ) -> List[CourseEnrollment]:
        student = cls.get_student_detail(student_id)
        courses = Course.objects.filter(id__in=course_ids, is_deleted=False)
        if len(courses) != len(course_ids):
            raise DomainException("One or more specified courses do not exist or are deleted.")

        enrollments = []
        for course in courses:
            enrollment, created = CourseEnrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={"status": CourseEnrollment.EnrollmentStatus.ACTIVE},
            )
            if not created and enrollment.status != CourseEnrollment.EnrollmentStatus.ACTIVE:
                enrollment.status = CourseEnrollment.EnrollmentStatus.ACTIVE
                enrollment.save(update_fields=["status", "updated_at"])
            enrollments.append(enrollment)

        AuditLog.objects.create(
            actor=admin_user,
            action="COURSES_ASSIGNED",
            target_model="StudentProfile",
            target_id=str(student.id),
            ip_address=ip_address,
            payload={"course_ids": [str(c.id) for c in courses]},
        )
        return enrollments

    @classmethod
    def get_student_progress(cls, student_id: str) -> Dict[str, Any]:
        student = cls.get_student_detail(student_id)
        module_progress = (
            StudentModuleProgress.objects.filter(student=student)
            .select_related("module", "module__course")
            .order_by("module__course", "module__order_index")
        )
        question_progress = (
            StudentQuestionProgress.objects.filter(student=student)
            .select_related("question", "question__module")
            .order_by("question__module", "question__order")
        )

        total_modules = Module.objects.filter(is_published=True).count()
        completed_modules = module_progress.filter(
            status=StudentModuleProgress.ModuleStatus.COMPLETED
        ).count()

        total_questions = CodingQuestion.objects.filter(is_active=True).count()
        solved_questions = question_progress.filter(is_solved=True).count()

        return {
            "student_id": str(student.id),
            "student_id_number": student.student_id_number,
            "full_name": student.full_name,
            "overview": {
                "total_modules": total_modules,
                "completed_modules": completed_modules,
                "module_completion_rate": round(
                    (completed_modules / total_modules * 100) if total_modules > 0 else 0, 2
                ),
                "total_questions": total_questions,
                "solved_questions": solved_questions,
                "question_solve_rate": round(
                    (solved_questions / total_questions * 100) if total_questions > 0 else 0, 2
                ),
            },
            "modules": [
                {
                    "module_id": str(mp.module.id),
                    "module_title": mp.module.title,
                    "course_title": mp.module.course.title,
                    "status": mp.status,
                    "score_percentage": str(mp.score_percentage),
                    "completed_at": mp.completed_at,
                }
                for mp in module_progress
            ],
            "questions": [
                {
                    "question_id": str(qp.question.id),
                    "question_title": qp.question.title,
                    "module_title": qp.question.module.title,
                    "is_solved": qp.is_solved,
                    "best_score": str(qp.best_score),
                    "attempts_count": qp.attempts_count,
                    "first_solved_at": qp.first_solved_at,
                }
                for qp in question_progress
            ],
        }

    @classmethod
    def get_student_scores(cls, student_id: str) -> Dict[str, Any]:
        student = cls.get_student_detail(student_id)
        records = (
            ScoreRecord.objects.filter(student=student)
            .select_related("awarded_by")
            .order_by("-awarded_at")
        )

        breakdown = {}
        for r in records:
            breakdown[r.source_type] = breakdown.get(r.source_type, Decimal("0.00")) + r.points

        return {
            "student_id": str(student.id),
            "full_name": student.full_name,
            "total_points": str(student.total_points),
            "breakdown_by_source": {k: str(v) for k, v in breakdown.items()},
            "records": [
                {
                    "id": str(r.id),
                    "source_type": r.source_type,
                    "source_id": str(r.source_id),
                    "points": str(r.points),
                    "policy_applied": r.policy_applied,
                    "awarded_at": r.awarded_at,
                }
                for r in records
            ],
        }

    @classmethod
    def get_student_rank(cls, student_id: str) -> Dict[str, Any]:
        student = cls.get_student_detail(student_id)
        # Global rank
        higher_global = StudentProfile.objects.filter(
            total_points__gt=student.total_points, user__is_active=True
        ).count()
        global_rank = higher_global + 1

        # Batch rank
        higher_batch = StudentProfile.objects.filter(
            batch_code=student.batch_code,
            total_points__gt=student.total_points,
            user__is_active=True,
        ).count()
        batch_rank = higher_batch + 1

        total_students_global = StudentProfile.objects.filter(user__is_active=True).count()
        total_students_batch = StudentProfile.objects.filter(
            batch_code=student.batch_code, user__is_active=True
        ).count()

        return {
            "student_id": str(student.id),
            "full_name": student.full_name,
            "batch_code": student.batch_code,
            "total_points": str(student.total_points),
            "global_rank": global_rank,
            "total_students_global": total_students_global,
            "batch_rank": batch_rank,
            "total_students_batch": total_students_batch,
            "current_streak_days": student.current_streak_days,
            "highest_streak_days": student.highest_streak_days,
        }


class StudentDashboardService:
    """Service providing aggregated dashboard telemetry and leaderboard standing for the authenticated student."""

    @classmethod
    def get_dashboard_data(cls, user: User) -> Dict[str, Any]:
        if not user.is_authenticated:
            raise DomainException("Authentication required.")

        profile = StudentProfile.objects.filter(user=user).select_related("user").first()
        if not profile:
            raise DomainException("User does not have an active student profile.")

        # 1. PROFILE & COURSE
        higher_global = StudentProfile.objects.filter(
            total_points__gt=profile.total_points, user__is_active=True
        ).count()
        global_rank = higher_global + 1
        total_students_global = StudentProfile.objects.filter(user__is_active=True).count()

        active_enrollment = (
            profile.enrollments.filter(status=CourseEnrollment.EnrollmentStatus.ACTIVE)
            .select_related("course")
            .first()
        )

        course_title = (
            active_enrollment.course.title
            if active_enrollment
            else "Full-Stack Software Engineering"
        )
        course_id = str(active_enrollment.course.id) if active_enrollment else None

        if active_enrollment:
            total_modules = Module.objects.filter(
                course=active_enrollment.course, is_published=True
            ).count()
            completed_modules = StudentModuleProgress.objects.filter(
                student=profile,
                module__course=active_enrollment.course,
                status=StudentModuleProgress.ModuleStatus.COMPLETED,
            ).count()
        else:
            total_modules = Module.objects.filter(is_published=True).count()
            completed_modules = StudentModuleProgress.objects.filter(
                student=profile,
                status=StudentModuleProgress.ModuleStatus.COMPLETED,
            ).count()

        overall_progress = (
            round((completed_modules / total_modules) * 100, 1) if total_modules > 0 else 0.0
        )

        profile_data = {
            "id": str(profile.id),
            "student_id_number": profile.student_id_number,
            "full_name": profile.full_name,
            "email": user.email,
            "avatar_url": profile.avatar_url,
            "course": course_title,
            "course_id": course_id,
            "batch_code": profile.batch_code,
            "college_name": profile.college_name,
            "total_score": float(profile.total_points),
            "current_rank": global_rank,
            "total_students": total_students_global,
            "completed_modules": completed_modules,
            "total_modules": total_modules,
            "overall_progress": overall_progress,
            "current_streak_days": profile.current_streak_days,
            "highest_streak_days": profile.highest_streak_days,
        }

        # 2. LEADERBOARD (via LeaderboardService)
        from apps.leaderboard.services import LeaderboardService

        leaderboard_payload = LeaderboardService.get_full_leaderboard_for_student(student=profile)
        top_10 = leaderboard_payload["top_10"]
        current_student_leaderboard = leaderboard_payload["current_student"]
        global_rank = current_student_leaderboard["rank"]
        total_students_global = current_student_leaderboard["total_participants"]
        profile_data["current_rank"] = global_rank
        profile_data["total_students"] = total_students_global

        # 3. PROGRESS BREAKDOWN
        total_questions = CodingQuestion.objects.filter(is_active=True).count()
        solved_questions = StudentQuestionProgress.objects.filter(
            student=profile, is_solved=True
        ).count()
        assignment_percentage = (
            round((solved_questions / total_questions) * 100, 1) if total_questions > 0 else 0.0
        )
        assignment_points = (
            ScoreRecord.objects.filter(
                student=profile, source_type=ScoreRecord.SourceType.ASSIGNMENT
            ).aggregate(total=Sum("points"))["total"]
            or Decimal("0.00")
        )

        project_submissions_count = profile.project_submissions.count()
        approved_projects_count = profile.project_submissions.filter(status="APPROVED").count()
        project_points = (
            ScoreRecord.objects.filter(
                student=profile, source_type=ScoreRecord.SourceType.PROJECT
            ).aggregate(total=Sum("points"))["total"]
            or Decimal("0.00")
        )

        tasks_completed = profile.task_completions.filter(is_completed=True).count()
        task_points = (
            ScoreRecord.objects.filter(
                student=profile, source_type=ScoreRecord.SourceType.DAILY_TASK
            ).aggregate(total=Sum("points"))["total"]
            or Decimal("0.00")
        )

        today = timezone.now().date()
        chart_history = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_points = (
                ScoreEvent.objects.filter(
                    student=profile, created_at__date=day
                ).aggregate(total=Sum("delta"))["total"]
                or Decimal("0.00")
            )
            chart_history.append(
                {
                    "date": day.strftime("%a"),
                    "points": float(day_points),
                    "full_date": str(day),
                }
            )

        skills_radar = [
            {"skill": "Coding Labs", "score": min(100, int(assignment_percentage)), "fullMark": 100},
            {"skill": "Curriculum", "score": min(100, int(overall_progress)), "fullMark": 100},
            {"skill": "Projects", "score": min(100, int(approved_projects_count * 50)), "fullMark": 100},
            {"skill": "Daily Tasks", "score": min(100, int(tasks_completed * 10)), "fullMark": 100},
            {
                "skill": "Streak Consistency",
                "score": min(100, int(profile.current_streak_days * 10)),
                "fullMark": 100,
            },
        ]

        progress_data = {
            "overall_progress": overall_progress,
            "module_completion": {
                "completed": completed_modules,
                "total": total_modules,
                "percentage": overall_progress,
            },
            "assignment_progress": {
                "solved": solved_questions,
                "total": total_questions,
                "percentage": assignment_percentage,
                "total_points": float(assignment_points),
            },
            "project_score": {
                "submitted": project_submissions_count,
                "approved": approved_projects_count,
                "total_score": float(project_points),
            },
            "task_progress": {
                "completed": tasks_completed,
                "total_points": float(task_points),
            },
            "chart_history": chart_history,
            "skills_radar": skills_radar,
        }

        # 4. ACTIVITY
        recent_submissions = [
            {
                "id": str(sub.id),
                "question_title": sub.question.title,
                "language": sub.language,
                "status": sub.status,
                "execution_time_ms": sub.execution_time_ms,
                "score_awarded": float(sub.score_awarded),
                "submitted_at": sub.submitted_at.isoformat(),
            }
            for sub in CodeSubmission.objects.filter(student=profile)
            .select_related("question")
            .order_by("-submitted_at")[:5]
        ]

        recent_tasks = [
            {
                "id": str(st.id),
                "task_title": st.task.title,
                "scheduled_date": str(st.task.scheduled_date),
                "is_completed": st.is_completed,
                "score_awarded": float(st.score_awarded),
                "completed_at": st.completed_at.isoformat(),
            }
            for st in StudentTask.objects.filter(student=profile)
            .select_related("task")
            .order_by("-completed_at")[:5]
        ]

        recent_achievements = [
            {
                "id": str(sb.id),
                "badge_name": sb.badge.name,
                "badge_description": sb.badge.description,
                "icon_url": sb.badge.icon_url,
                "criteria_type": sb.badge.criteria_type,
                "awarded_at": sb.awarded_at.isoformat(),
            }
            for sb in StudentBadge.objects.filter(student=profile)
            .select_related("badge")
            .order_by("-awarded_at")[:5]
        ]

        notifications = [
            {
                "id": str(notif.id),
                "title": notif.title,
                "body": notif.body,
                "notification_type": notif.notification_type,
                "is_read": notif.is_read,
                "created_at": notif.created_at.isoformat(),
            }
            for notif in Notification.objects.filter(recipient=user).order_by("-created_at")[:5]
        ]

        return {
            "profile": profile_data,
            "leaderboard": {
                "top_10": top_10,
                "current_student": current_student_leaderboard,
            },
            "progress": progress_data,
            "activity": {
                "recent_submissions": recent_submissions,
                "recent_tasks": recent_tasks,
                "recent_achievements": recent_achievements,
                "notifications": notifications,
            },
        }

