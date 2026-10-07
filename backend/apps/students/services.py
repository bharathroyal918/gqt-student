"""Domain services for administrative student management, enrollments, and academic reporting."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.shortcuts import get_object_or_404

from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Q, Sum

from django.core.cache import cache
from apps.accounts.models import AuditLog, User
from apps.assignments.models import CodeSubmission, CodingQuestion, StudentQuestionProgress
from apps.certificates.models import StudentBadge
from apps.common.exceptions import DomainException
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.notifications.models import Notification
from apps.scoring.models import ScoreEvent, ScoreRecord
from apps.students.models import AttendanceRecord, StudentProfile
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
    def grant_student_access(
        cls, student_id: str, admin_user: User, ip_address: Optional[str] = None
    ) -> StudentProfile:
        """Admin explicitly grants full portal and curriculum access to a student."""
        student = cls.get_student_detail(student_id)
        user = student.user

        user.onboarding_status = User.OnboardingStatusChoices.ACTIVE
        user.is_active = True
        user.save(update_fields=["onboarding_status", "is_active", "updated_at"])

        # Automatically enroll in published courses if student has none
        if not student.enrollments.filter(status=CourseEnrollment.EnrollmentStatus.ACTIVE).exists():
            default_courses = Course.objects.filter(is_published=True, is_deleted=False)[:2]
            for c in default_courses:
                CourseEnrollment.objects.get_or_create(
                    student=student,
                    course=c,
                    defaults={"status": CourseEnrollment.EnrollmentStatus.ACTIVE},
                )

        Notification.objects.create(
            recipient=user,
            title="Portal Access Granted!",
            body="Your GQT Student Portal access has been verified and authorized by the administration.",
            notification_type=Notification.NotificationType.SYSTEM_NOTICE,
        )

        AuditLog.objects.create(
            actor=admin_user,
            action="STUDENT_ACCESS_GRANTED",
            target_model="StudentProfile",
            target_id=str(student.id),
            ip_address=ip_address,
            payload={"student_email": user.email, "student_name": student.full_name},
        )
        return student

    @classmethod
    @transaction.atomic
    def revoke_student_access(
        cls, student_id: str, admin_user: User, ip_address: Optional[str] = None
    ) -> StudentProfile:
        """Admin suspends or revokes portal access for a student."""
        student = cls.get_student_detail(student_id)
        user = student.user

        user.onboarding_status = User.OnboardingStatusChoices.SUSPENDED
        user.save(update_fields=["onboarding_status", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="STUDENT_ACCESS_REVOKED",
            target_model="StudentProfile",
            target_id=str(student.id),
            ip_address=ip_address,
            payload={"student_email": user.email, "student_name": student.full_name},
        )
        return student

    @classmethod
    @transaction.atomic
    def grant_access_by_email(
        cls,
        email: str,
        admin_user: User,
        course_opted: str = "Full Stack Software & Assessment Track",
        batch_code: str = "BATCH-2026-A",
        ip_address: Optional[str] = None,
    ) -> StudentProfile:
        """Admin provides direct access to a student using their registered institutional email."""
        clean_email = email.strip().lower()
        user = User.objects.filter(email=clean_email).first()

        if not user:
            raise DomainException(f"No student registered with email {clean_email}.", status_code=404)

        student = getattr(user, "student_profile", None)
        if not student:
            raise DomainException("User does not have an attached Student Profile.", status_code=400)

        user.onboarding_status = User.OnboardingStatusChoices.ACTIVE
        user.is_active = True
        user.save(update_fields=["onboarding_status", "is_active", "updated_at"])

        if course_opted:
            student.course_opted = course_opted.strip()
        if batch_code:
            student.batch_code = batch_code.strip()
        student.save(update_fields=["course_opted", "batch_code", "updated_at"])

        # Auto-enroll in default published courses
        default_courses = Course.objects.filter(is_published=True, is_deleted=False)[:2]
        for c in default_courses:
            CourseEnrollment.objects.get_or_create(
                student=student,
                course=c,
                defaults={"status": CourseEnrollment.EnrollmentStatus.ACTIVE},
            )

        Notification.objects.create(
            recipient=user,
            title="Account Authorized by Administrator",
            body=f"Your email ({clean_email}) has been authorized for {student.course_opted}.",
            notification_type=Notification.NotificationType.SYSTEM_NOTICE,
        )

        AuditLog.objects.create(
            actor=admin_user,
            action="STUDENT_ACCESS_GRANTED_BY_EMAIL",
            target_model="StudentProfile",
            target_id=str(student.id),
            ip_address=ip_address,
            payload={"email": clean_email, "course_opted": student.course_opted},
        )
        return student

    @classmethod
    @transaction.atomic
    def mark_attendance(
        cls,
        student_id: str,
        date,
        status: str,
        session_title: str,
        remarks: str,
        admin_user: User,
        ip_address: Optional[str] = None,
    ) -> AttendanceRecord:
        """Admin records daily session attendance for a student."""
        student = cls.get_student_detail(student_id)

        record, _ = AttendanceRecord.objects.update_or_create(
            student_profile=student,
            date=date,
            defaults={
                "status": status,
                "session_title": session_title or "Daily Training & Coding Lab",
                "remarks": remarks or "",
            },
        )

        # Recalculate totals
        total = AttendanceRecord.objects.filter(student_profile=student).count()
        attended = AttendanceRecord.objects.filter(
            student_profile=student,
            status__in=[AttendanceRecord.AttendanceStatus.PRESENT, AttendanceRecord.AttendanceStatus.LATE],
        ).count()

        student.total_classes = max(total, student.total_classes)
        student.attended_classes = attended
        student.recalculate_attendance()
        student.save(update_fields=["total_classes", "attended_classes", "attendance_percentage", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="ATTENDANCE_MARKED",
            target_model="AttendanceRecord",
            target_id=str(record.id),
            ip_address=ip_address,
            payload={"student_id": str(student.id), "date": str(date), "status": status},
        )
        return record

    @classmethod
    def get_student_attendance(cls, student_id: str) -> Dict[str, Any]:
        """Admin inspects student's full attendance history."""
        student = cls.get_student_detail(student_id)
        records = AttendanceRecord.objects.filter(student_profile=student).order_by("-date")[:50]
        return {
            "attendance_percentage": float(student.attendance_percentage),
            "total_classes": student.total_classes,
            "attended_classes": student.attended_classes,
            "missed_classes": max(0, student.total_classes - student.attended_classes),
            "records": [
                {
                    "id": str(r.id),
                    "date": str(r.date),
                    "session_title": r.session_title,
                    "status": r.status,
                    "remarks": r.remarks,
                    "created_at": r.created_at.isoformat(),
                }
                for r in records
            ],
        }

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
        dob=None,
        branch: Optional[str] = None,
        course_opted: Optional[str] = None,
        avatar_url: Optional[str] = None,
        email: Optional[str] = None,
        mobile_number: Optional[str] = None,
        is_active: Optional[bool] = None,
        onboarding_status: Optional[str] = None,
        total_classes: Optional[int] = None,
        attended_classes: Optional[int] = None,
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

        if dob is not None:
            student.dob = dob
            updated_fields_profile.append("dob")

        if branch is not None:
            student.branch = branch.strip()
            updated_fields_profile.append("branch")

        if course_opted is not None:
            student.course_opted = course_opted.strip()
            updated_fields_profile.append("course_opted")

        if avatar_url is not None:
            student.avatar_url = (avatar_url or "").strip()
            updated_fields_profile.append("avatar_url")

        if total_classes is not None:
            student.total_classes = total_classes
            updated_fields_profile.append("total_classes")

        if attended_classes is not None:
            student.attended_classes = attended_classes
            updated_fields_profile.append("attended_classes")

        if total_classes is not None or attended_classes is not None:
            student.recalculate_attendance()
            updated_fields_profile.append("attendance_percentage")

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
            "current_streak_days": student.get_effective_streak(),
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
            else (profile.course_opted or "Full-Stack Software Engineering")
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
            "graduation_year": profile.graduation_year,
            "dob": str(profile.dob) if profile.dob else None,
            "branch": profile.branch,
            "bio": profile.bio,
            "github_url": profile.github_url,
            "linkedin_url": profile.linkedin_url,
            "course_opted": profile.course_opted or course_title,
            "attendance_percentage": float(profile.attendance_percentage),
            "total_classes": profile.total_classes,
            "attended_classes": profile.attended_classes,
            "onboarding_status": user.onboarding_status,
            "is_approved": user.onboarding_status == User.OnboardingStatusChoices.ACTIVE,
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
        start_date = today - timedelta(days=6)
        recent_events = (
            ScoreEvent.objects.filter(
                student=profile,
                created_at__date__gte=start_date,
            )
            .values("created_at__date")
            .annotate(total=Sum("delta"))
        )
        events_by_date = {event["created_at__date"]: event["total"] for event in recent_events}
        chart_history = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_points = events_by_date.get(day, Decimal("0.00")) or Decimal("0.00")
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
            "attendance": {
                "percentage": float(profile.attendance_percentage),
                "total_classes": profile.total_classes,
                "attended_classes": profile.attended_classes,
                "missed_classes": max(0, profile.total_classes - profile.attended_classes),
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

        # 5. LEETCODE-STYLE STREAK & YEARLY ACTIVITY HEATMAP
        activity_heatmap = cls.get_student_activity_heatmap_data(profile=profile)
        profile_data["current_streak_days"] = activity_heatmap["current_streak"]

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
            "activity_heatmap": activity_heatmap,
        }

    @classmethod
    def get_student_activity_heatmap_data(cls, profile: StudentProfile) -> Dict[str, Any]:
        """Calculates 365-day problem-solving activity matrix and streaks."""
        today_date = timezone.localdate()
        effective_streak = profile.get_effective_streak(today_date)

        days_in_grid = 365
        grid_start_date = today_date - timedelta(days=days_in_grid - 1)

        # Aggregate daily accepted submissions & solved questions
        daily_submissions = (
            CodeSubmission.objects.filter(
                student=profile,
                created_at__date__gte=grid_start_date,
            )
            .values("created_at__date")
            .annotate(
                total_subs=Count("id"),
                accepted_subs=Count("id", filter=Q(status=CodeSubmission.SubmissionStatus.ACCEPTED)),
                points_sum=Sum("score_awarded"),
            )
        )

        daily_score_events = (
            ScoreEvent.objects.filter(
                student=profile,
                created_at__date__gte=grid_start_date,
            )
            .values("created_at__date")
            .annotate(total_events=Count("id"), points_sum=Sum("delta"))
        )

        daily_map = {}
        for row in daily_submissions:
            d = row["created_at__date"]
            daily_map[d] = {
                "count": row["accepted_subs"] or row["total_subs"],
                "points": float(row["points_sum"] or 0),
            }

        for row in daily_score_events:
            d = row["created_at__date"]
            if d not in daily_map:
                daily_map[d] = {
                    "count": row["total_events"],
                    "points": float(row["points_sum"] or 0),
                }
            else:
                daily_map[d]["points"] = max(
                    daily_map[d]["points"], float(row["points_sum"] or 0)
                )

        heatmap_records = []
        total_active_days = 0
        total_submissions_year = 0

        for i in range(days_in_grid):
            current_day = grid_start_date + timedelta(days=i)
            day_data = daily_map.get(current_day, {"count": 0, "points": 0.0})
            cnt = day_data["count"]
            pts = day_data["points"]

            if cnt > 0 or pts > 0:
                total_active_days += 1
                total_submissions_year += max(cnt, 1)

            # Intensity Level: 0 = empty, 1 = 1-2, 2 = 3-4, 3 = 5+
            if cnt == 0 and pts == 0:
                level = 0
            elif cnt <= 2 and pts < 30:
                level = 1
            elif cnt <= 4 or pts < 80:
                level = 2
            else:
                level = 3

            heatmap_records.append(
                {
                    "date": str(current_day),
                    "day_name": current_day.strftime("%a"),
                    "month_name": current_day.strftime("%b"),
                    "month_index": current_day.month,
                    "day_of_week": current_day.weekday(),  # 0=Mon, 6=Sun
                    "count": cnt,
                    "points": pts,
                    "level": level,
                    "is_today": current_day == today_date,
                }
            )

        solved_today = (
            daily_map.get(today_date, {}).get("count", 0) > 0
            or profile.last_activity_date == today_date
        )

        return {
            "start_date": str(grid_start_date),
            "end_date": str(today_date),
            "current_streak": effective_streak,
            "longest_streak": profile.highest_streak_days,
            "total_active_days": total_active_days,
            "total_submissions_year": total_submissions_year,
            "solved_today": solved_today,
            "last_activity_date": str(profile.last_activity_date)
            if profile.last_activity_date
            else None,
            "records": heatmap_records,
        }

    @classmethod
    def get_student_activity_heatmap(cls, user: User) -> Dict[str, Any]:
        """Entry point for authenticated user activity heatmap."""
        profile = StudentProfile.objects.filter(user=user).first()
        if not profile:
            raise DomainException("Student profile not found.", status_code=404)
        return cls.get_student_activity_heatmap_data(profile)

    @classmethod
    @transaction.atomic
    def update_student_profile(
        cls,
        user: User,
        **kwargs,
    ) -> StudentProfile:
        """Student updates their own permitted profile fields (DOB, branch, college, avatar, bio, URLs).
        
        Strictly prohibits mutating email, full_name, student_id_number, course_opted, or points.
        """
        profile = StudentProfile.objects.filter(user=user).first()
        if not profile:
            raise DomainException("Student profile not found.", status_code=404)

        updated_fields = ["updated_at"]

        if "dob" in kwargs:
            profile.dob = kwargs["dob"]
            updated_fields.append("dob")

        if "branch" in kwargs:
            val = kwargs["branch"]
            profile.branch = (val or "").strip()
            updated_fields.append("branch")

        if "college_name" in kwargs:
            val = kwargs["college_name"]
            profile.college_name = (val or "").strip()
            updated_fields.append("college_name")

        if "graduation_year" in kwargs:
            val = kwargs["graduation_year"]
            profile.graduation_year = val if val else None
            updated_fields.append("graduation_year")

        if "avatar_url" in kwargs:
            val = kwargs["avatar_url"]
            profile.avatar_url = (val or "").strip()
            updated_fields.append("avatar_url")

        if "bio" in kwargs:
            val = kwargs["bio"]
            profile.bio = (val or "").strip()
            updated_fields.append("bio")

        if "github_url" in kwargs:
            val = kwargs["github_url"]
            profile.github_url = (val or "").strip()
            updated_fields.append("github_url")

        if "linkedin_url" in kwargs:
            val = kwargs["linkedin_url"]
            profile.linkedin_url = (val or "").strip()
            updated_fields.append("linkedin_url")

        if len(updated_fields) > 1:
            profile.save(update_fields=updated_fields)
        else:
            profile.save()

        return profile

    @classmethod
    def get_student_attendance(cls, user: User) -> Dict[str, Any]:
        """Retrieve authenticated student's attendance records, profile details, and personal QR token."""
        import json
        profile = StudentProfile.objects.filter(user=user).first()
        if not profile:
            raise DomainException("Student profile not found.", status_code=404)

        active_enrollments = CourseEnrollment.objects.filter(
            student=profile, status=CourseEnrollment.EnrollmentStatus.ACTIVE
        ).select_related("course")
        
        enrolled_courses = [e.course.title for e in active_enrollments]
        has_enrollments = len(enrolled_courses) > 0 or bool(profile.course_opted and profile.course_opted.strip())
        primary_course = enrolled_courses[0] if enrolled_courses else (profile.course_opted or "Not Enrolled")

        records = AttendanceRecord.objects.filter(student_profile=profile).order_by("-date", "-created_at")[:50]
        
        # Build student QR identification payload
        student_qr_payload = {
            "type": "STUDENT_ATTENDANCE_ID",
            "student_id": profile.student_id_number,
            "full_name": profile.full_name,
            "batch_code": profile.batch_code,
            "course": primary_course,
            "college": profile.college_name,
            "email": user.email,
        }

        return {
            "student": {
                "full_name": profile.full_name,
                "student_id": profile.student_id_number,
                "batch_code": profile.batch_code,
                "course_name": primary_course,
                "college_name": profile.college_name,
                "has_enrollments": has_enrollments,
                "enrolled_courses": enrolled_courses,
            },
            "student_qr_data": json.dumps(student_qr_payload),
            "attendance_percentage": float(profile.attendance_percentage),
            "total_classes": profile.total_classes,
            "attended_classes": profile.attended_classes,
            "missed_classes": max(0, profile.total_classes - profile.attended_classes),
            "current_streak_days": profile.current_streak_days,
            "records": [
                {
                    "id": str(r.id),
                    "date": str(r.date),
                    "session_title": r.session_title,
                    "status": r.status,
                    "remarks": r.remarks,
                    "created_at": r.created_at.isoformat(),
                }
                for r in records
            ],
        }

    @classmethod
    @transaction.atomic
    def mark_qr_attendance(
        cls, user: User, qr_data: str, session_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Scan and record QR Code attendance for enrolled students.
        
        Validates:
        1. Student profile existence.
        2. Course registration: Verifies that student is registered in at least one course.
           If NOT registered, raises:
           'You are not registered yet for any course. Please contact administrator to enroll in the course.'
        3. Parses QR code payload.
        4. Marks attendance as PRESENT idempotently for the session date.
        5. Updates real-time streak and telemetry.
        """
        import json
        profile = StudentProfile.objects.filter(user=user).first()
        if not profile:
            raise DomainException("Student profile not found.", status_code=404)

        # Check course registration
        active_enrollments = CourseEnrollment.objects.filter(
            student=profile, status=CourseEnrollment.EnrollmentStatus.ACTIVE
        ).select_related("course")

        has_active_courses = active_enrollments.exists() or (bool(profile.course_opted) and profile.course_opted.strip() != "")

        if not has_active_courses:
            raise DomainException(
                "You are not registered yet for any course. Please contact administrator to enroll in the course.",
                status_code=400,
            )

        course_name = active_enrollments.first().course.title if active_enrollments.exists() else (profile.course_opted or "General Track")
        session_title = "Daily Training & Coding Lab"

        raw_qr = (qr_data or session_code or "").strip()
        if raw_qr:
            try:
                if raw_qr.startswith("{") and raw_qr.endswith("}"):
                    parsed = json.loads(raw_qr)
                    session_title = parsed.get("session_title") or parsed.get("title") or parsed.get("name") or session_title
                    if "course_name" in parsed:
                        course_name = parsed["course_name"]
                elif ":" in raw_qr:
                    parts = raw_qr.split(":", 1)
                    if len(parts) == 2 and parts[1].strip():
                        session_title = parts[1].strip()
                else:
                    session_title = raw_qr
            except Exception:
                session_title = raw_qr[:60]

        today = timezone.localdate()
        now = timezone.now()

        # Check if already marked today for this specific session
        existing = AttendanceRecord.objects.filter(
            student_profile=profile,
            date=today,
            session_title=session_title,
        ).first()

        is_already_marked = False
        if existing:
            is_already_marked = True
            attendance_record = existing
            message = f"Attendance already recorded as {existing.status} for today's session."
        else:
            attendance_record = AttendanceRecord.objects.create(
                student_profile=profile,
                date=today,
                session_title=session_title,
                status=AttendanceRecord.AttendanceStatus.PRESENT,
                remarks="Verified via QR Code Scanner",
            )
            profile.attended_classes = (profile.attended_classes or 0) + 1
            if (profile.total_classes or 0) < profile.attended_classes:
                profile.total_classes = profile.attended_classes
            profile.recalculate_attendance()
            profile.save(update_fields=["attended_classes", "total_classes", "attendance_percentage", "updated_at"])

            # Increment learning activity streak
            profile.record_activity_and_update_streak(activity_date=today)
            message = "Attendance marked successfully! Marked as PRESENT."

        return {
            "success": True,
            "message": message,
            "is_already_marked": is_already_marked,
            "attendance": {
                "id": str(attendance_record.id),
                "date": str(attendance_record.date),
                "session_title": attendance_record.session_title,
                "status": attendance_record.status,
                "remarks": attendance_record.remarks,
                "timestamp": now.strftime("%I:%M %p, %d %b %Y"),
            },
            "student": {
                "full_name": profile.full_name,
                "student_id": profile.student_id_number,
                "batch_code": profile.batch_code,
                "course_name": course_name,
                "college_name": profile.college_name,
            },
            "stats": {
                "attendance_percentage": float(profile.attendance_percentage),
                "attended_classes": profile.attended_classes,
                "total_classes": profile.total_classes,
                "streak_days": profile.current_streak_days,
            },
        }

