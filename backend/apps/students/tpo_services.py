"""Service layer for TPO College Dashboard, Roster, Student Performance, and Learning Analytics."""

import logging
from decimal import Decimal
from typing import Any

from django.db import models
from django.db.models import Avg, Count, Max, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.accounts.services import AuthService
from apps.assignments.models import CodeSubmission, CodingQuestion
from apps.common.exceptions import DomainException
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.scoring.models import ScoreRecord
from apps.students.models import AttendanceRecord, College, StudentProfile

logger = logging.getLogger(__name__)


class TPODashboardService:
    """Provides high-performance, strictly college-scoped data for TPOs."""

    @classmethod
    def get_assigned_college_or_fail(cls, tpo_user) -> College:
        """Resolve authoritative assigned college or fail closed."""
        return AuthService.get_tpo_assigned_college(tpo_user)

    @classmethod
    def get_college_students_queryset(cls, tpo_user) -> models.QuerySet[StudentProfile]:
        """Return the scoped StudentProfile queryset for the TPO's assigned college.

        Authoritative Scoping Rule (Security Gate):
        1. Prioritizes the canonical foreign-key relationship `college == assigned_college`.
        2. If and only if the relational foreign key is NULL (legacy registration record),
           falls back to `college_name` matching `college.name`.
        3. Never allows a conflicting text field to override an explicit relational foreign key.
        """
        college = cls.get_assigned_college_or_fail(tpo_user)
        return StudentProfile.objects.filter(
            Q(college=college) | Q(college__isnull=True, college_name__iexact=college.name)
        ).select_related("user", "college")

    @classmethod
    def get_college_summary(cls, tpo_user) -> dict[str, Any]:
        """Compute real, verified summary metrics for the assigned college dashboard."""
        college = cls.get_assigned_college_or_fail(tpo_user)
        students_qs = cls.get_college_students_queryset(tpo_user)

        total_students = students_qs.count()
        active_students = students_qs.filter(user__is_active=True).count()
        inactive_students = total_students - active_students

        # Attendance Aggregates
        attendance_stats = students_qs.aggregate(
            avg_attendance=Avg("attendance_percentage"),
        )
        avg_att = attendance_stats.get("avg_attendance")
        average_attendance_percentage = (
            float(round(avg_att, 2)) if avg_att is not None else 0.0
        )
        students_above_75_attendance = students_qs.filter(
            attendance_percentage__gte=Decimal("75.00")
        ).count()

        # Technology / Course Opted Distribution
        tech_counts = (
            students_qs.values("course_opted")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        technology_distribution = [
            {
                "name": item["course_opted"] or "General Assessment Track",
                "count": item["count"],
            }
            for item in tech_counts
        ]

        # Branch Distribution
        branch_counts = (
            students_qs.values("branch")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        branch_distribution = [
            {
                "name": item["branch"] or "Computer Science",
                "count": item["count"],
            }
            for item in branch_counts
        ]

        # Batch Distribution
        batch_counts = (
            students_qs.values("batch_code")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        batch_distribution = [
            {
                "batch_code": item["batch_code"] or "Unassigned",
                "count": item["count"],
            }
            for item in batch_counts
        ]

        # Assignment Submissions within this College
        student_ids = students_qs.values_list("id", flat=True)
        submissions_qs = CodeSubmission.objects.filter(student_id__in=student_ids)
        total_submissions = submissions_qs.count()
        accepted_submissions = submissions_qs.filter(
            status=CodeSubmission.SubmissionStatus.ACCEPTED
        ).count()

        # Top 5 Performers
        top_students = students_qs.order_by("-total_points", "-attendance_percentage")[:5]
        top_performers = [
            {
                "id": str(s.id),
                "student_id_number": s.student_id_number,
                "full_name": s.full_name,
                "total_points": float(s.total_points),
                "batch_code": s.batch_code,
                "branch": s.branch,
                "attendance_percentage": float(s.attendance_percentage),
                "avatar_url": s.avatar_url,
            }
            for s in top_students
        ]

        return {
            "college": {
                "id": str(college.id),
                "name": college.name,
                "code": college.code,
                "city": college.city,
                "state": college.state,
                "is_active": college.is_active,
            },
            "total_students": total_students,
            "active_students": active_students,
            "inactive_students": inactive_students,
            "average_attendance_percentage": average_attendance_percentage,
            "students_above_75_attendance": students_above_75_attendance,
            "total_submissions": total_submissions,
            "accepted_submissions": accepted_submissions,
            "technology_distribution": technology_distribution,
            "branch_distribution": branch_distribution,
            "batch_distribution": batch_distribution,
            "top_performers": top_performers,
        }

    @classmethod
    def get_student_detail(cls, tpo_user, student_id) -> dict[str, Any]:
        """Retrieve detailed student performance summary, scoped strictly by assigned college."""
        students_qs = cls.get_college_students_queryset(tpo_user)
        student = students_qs.filter(id=student_id).first()

        if not student:
            raise DomainException(
                detail="Student record not found or not enrolled in your assigned college.",
                code="STUDENT_NOT_FOUND",
                status_code=404,
            )

        # Enrolled courses
        enrollments = CourseEnrollment.objects.filter(student=student).select_related("course")
        enrollments_data = [
            {
                "id": str(e.id),
                "course_id": str(e.course.id),
                "course_title": e.course.title,
                "status": e.status,
                "enrolled_at": e.enrolled_at,
                "completed_at": e.completed_at,
            }
            for e in enrollments
        ]

        # Recent submissions
        recent_submissions = (
            CodeSubmission.objects.filter(student=student)
            .select_related("question")
            .order_by("-submitted_at")[:10]
        )
        submissions_data = [
            {
                "id": str(sub.id),
                "question_id": str(sub.question.id) if sub.question else None,
                "question_title": sub.question.title if sub.question else "Coding Challenge",
                "language": sub.language,
                "status": sub.status,
                "score_awarded": float(sub.score_awarded),
                "passed_test_cases": sub.passed_test_cases,
                "total_test_cases": sub.total_test_cases,
                "submitted_at": sub.submitted_at,
            }
            for sub in recent_submissions
        ]

        # Score Breakdown
        score_breakdown = {
            "ASSIGNMENT": 0.0,
            "DAILY_TASK": 0.0,
            "PROJECT": 0.0,
            "STREAK_BONUS": 0.0,
            "ADMIN_ADJUSTMENT": 0.0,
            "TOTAL": float(student.total_points),
        }
        for rec in ScoreRecord.objects.filter(student=student).values("source_type").annotate(pts=models.Sum("points")):
            source = rec["source_type"]
            if source in score_breakdown:
                score_breakdown[source] = float(rec["pts"] or 0.0)

        # Recent Attendance
        recent_attendance = (
            AttendanceRecord.objects.filter(student_profile=student)
            .order_by("-date", "-created_at")[:15]
        )
        attendance_data = [
            {
                "id": str(att.id),
                "date": att.date,
                "session_title": att.session_title,
                "technology": att.technology,
                "status": att.status,
                "remarks": att.remarks,
            }
            for att in recent_attendance
        ]

        return {
            "id": str(student.id),
            "user_id": str(student.user.id) if student.user else None,
            "student_id_number": student.student_id_number,
            "full_name": student.full_name,
            "email": student.user.email if student.user else "",
            "batch_code": student.batch_code,
            "college_id": str(student.college.id) if student.college else None,
            "college_name": student.college.name if student.college else student.college_name,
            "branch": student.branch,
            "graduation_year": student.graduation_year,
            "course_opted": student.course_opted,
            "bio": student.bio,
            "github_url": student.github_url,
            "linkedin_url": student.linkedin_url,
            "attendance_percentage": float(student.attendance_percentage),
            "total_classes": student.total_classes,
            "attended_classes": student.attended_classes,
            "current_streak_days": student.current_streak_days,
            "highest_streak_days": student.highest_streak_days,
            "total_points": float(student.total_points),
            "avatar_url": student.avatar_url,
            "is_active": student.user.is_active if student.user else True,
            "created_at": student.created_at,
            "enrollments": enrollments_data,
            "recent_submissions": submissions_data,
            "score_breakdown": score_breakdown,
            "recent_attendance": attendance_data,
        }


class TPOAnalyticsService:
    """Provides high-performance, strictly college-scoped academic performance and learning analytics."""

    @classmethod
    def get_learning_progress(cls, tpo_user, course_id=None) -> dict[str, Any]:
        """Compute curriculum and module progression metrics for the assigned college."""
        students_qs = TPODashboardService.get_college_students_queryset(tpo_user)
        student_ids = list(students_qs.values_list("id", flat=True))
        total_students = len(student_ids)

        # 1. Course Enrollment Summary
        enrollments_qs = CourseEnrollment.objects.filter(student_id__in=student_ids).select_related("course")
        if course_id:
            enrollments_qs = enrollments_qs.filter(course_id=course_id)

        course_map = {}
        for enr in enrollments_qs:
            cid = str(enr.course.id)
            if cid not in course_map:
                course_map[cid] = {
                    "course_id": cid,
                    "course_title": enr.course.title,
                    "enrolled_count": 0,
                    "completed_count": 0,
                    "in_progress_count": 0,
                }
            course_map[cid]["enrolled_count"] += 1
            if enr.status == CourseEnrollment.EnrollmentStatus.COMPLETED:
                course_map[cid]["completed_count"] += 1
            else:
                course_map[cid]["in_progress_count"] += 1

        course_progression_summary = list(course_map.values())

        # 2. Module Completion Summary
        modules_qs = Module.objects.filter(is_published=True).select_related("course")
        if course_id:
            modules_qs = modules_qs.filter(course_id=course_id)

        progress_qs = StudentModuleProgress.objects.filter(student_id__in=student_ids).select_related("module")
        if course_id:
            progress_qs = progress_qs.filter(module__course_id=course_id)

        module_stats = {}
        for mod in modules_qs:
            mid = str(mod.id)
            module_stats[mid] = {
                "module_id": mid,
                "module_title": mod.title,
                "course_title": mod.course.title,
                "order_index": mod.order_index,
                "completed_count": 0,
                "in_progress_count": 0,
            }

        for prog in progress_qs:
            mid = str(prog.module_id)
            if mid in module_stats:
                if prog.status == StudentModuleProgress.ModuleStatus.COMPLETED:
                    module_stats[mid]["completed_count"] += 1
                elif prog.status == StudentModuleProgress.ModuleStatus.IN_PROGRESS:
                    module_stats[mid]["in_progress_count"] += 1

        module_completion_summary = list(module_stats.values())
        # Sort by course title and order index
        module_completion_summary.sort(key=lambda x: (x["course_title"], x["order_index"]))

        # 3. Overall Student Progress Table
        # Map student completed modules count
        student_completed_counts = {
            row["student_id"]: row["cnt"]
            for row in StudentModuleProgress.objects.filter(
                student_id__in=student_ids,
                status=StudentModuleProgress.ModuleStatus.COMPLETED,
            )
            .values("student_id")
            .annotate(cnt=Count("id"))
        }

        total_active_modules = modules_qs.count()
        student_progress_list = []
        for s in students_qs.order_by("full_name"):
            completed = student_completed_counts.get(s.id, 0)
            progress_pct = (
                round((completed / total_active_modules) * 100, 1)
                if total_active_modules > 0
                else 0.0
            )

            # Determine progression status
            if completed == total_active_modules and total_active_modules > 0:
                prog_status = "COMPLETED"
            elif completed > 0 or s.current_streak_days > 0:
                prog_status = "ON_TRACK"
            else:
                prog_status = "NOT_STARTED"

            student_progress_list.append(
                {
                    "id": str(s.id),
                    "student_id_number": s.student_id_number,
                    "full_name": s.full_name,
                    "batch_code": s.batch_code,
                    "branch": s.branch,
                    "course_opted": s.course_opted,
                    "completed_modules": completed,
                    "total_modules": total_active_modules,
                    "progress_percentage": progress_pct,
                    "status": prog_status,
                }
            )

        return {
            "total_students": total_students,
            "total_courses": len(course_progression_summary),
            "total_modules": total_active_modules,
            "course_progression": course_progression_summary,
            "module_completion": module_completion_summary,
            "student_progress": student_progress_list,
        }

    @classmethod
    def get_assignments_labs(
        cls, tpo_user, date_from=None, date_to=None
    ) -> dict[str, Any]:
        """Compute coding challenge and lab submission performance metrics."""
        students_qs = TPODashboardService.get_college_students_queryset(tpo_user)
        student_ids = list(students_qs.values_list("id", flat=True))
        total_students = len(student_ids)

        submissions_qs = CodeSubmission.objects.filter(student_id__in=student_ids)
        if date_from:
            submissions_qs = submissions_qs.filter(submitted_at__date__gte=date_from)
        if date_to:
            submissions_qs = submissions_qs.filter(submitted_at__date__lte=date_to)

        total_attempts = submissions_qs.count()
        participating_students = submissions_qs.values("student_id").distinct().count()
        unique_questions_attempted = (
            submissions_qs.values("question_id").distinct().count()
        )

        accepted_submissions = submissions_qs.filter(
            status=CodeSubmission.SubmissionStatus.ACCEPTED
        ).count()
        wrong_answers = submissions_qs.filter(
            status=CodeSubmission.SubmissionStatus.WRONG_ANSWER
        ).count()
        runtime_errors = submissions_qs.filter(
            status=CodeSubmission.SubmissionStatus.RUNTIME_ERROR
        ).count()
        compilation_errors = submissions_qs.filter(
            status=CodeSubmission.SubmissionStatus.COMPILATION_ERROR
        ).count()
        time_limit_exceeded = submissions_qs.filter(
            status=CodeSubmission.SubmissionStatus.TIME_LIMIT_EXCEEDED
        ).count()
        memory_limit_exceeded = submissions_qs.filter(
            status=CodeSubmission.SubmissionStatus.MEMORY_LIMIT_EXCEEDED
        ).count()
        pending_submissions = submissions_qs.filter(
            status__in=[
                CodeSubmission.SubmissionStatus.PENDING,
                CodeSubmission.SubmissionStatus.RUNNING,
            ]
        ).count()

        rejected_submissions = (
            wrong_answers
            + runtime_errors
            + compilation_errors
            + time_limit_exceeded
            + memory_limit_exceeded
        )
        evaluated_submissions = accepted_submissions + rejected_submissions

        pass_rate_percentage = (
            round((accepted_submissions / evaluated_submissions) * 100, 1)
            if evaluated_submissions > 0
            else 0.0
        )
        unattempted_students = max(0, total_students - participating_students)

        # Language Breakdown
        lang_breakdown = (
            submissions_qs.values("language")
            .annotate(
                total=Count("id"),
                accepted=Count("id", filter=Q(status=CodeSubmission.SubmissionStatus.ACCEPTED)),
            )
            .order_by("-total")
        )
        language_stats = [
            {
                "language": row["language"],
                "total_submissions": row["total"],
                "accepted_submissions": row["accepted"],
                "pass_rate": (
                    round((row["accepted"] / row["total"]) * 100, 1)
                    if row["total"] > 0
                    else 0.0
                ),
            }
            for row in lang_breakdown
        ]

        # Recent 25 activity records
        recent_activity = (
            submissions_qs.select_related("student", "question")
            .order_by("-submitted_at")[:25]
        )
        recent_timeline = [
            {
                "id": str(sub.id),
                "student_id": str(sub.student.id),
                "student_name": sub.student.full_name,
                "student_id_number": sub.student.student_id_number,
                "question_title": (
                    sub.question.title if sub.question else "Coding Problem"
                ),
                "language": sub.language,
                "status": sub.status,
                "score_awarded": float(sub.score_awarded),
                "passed_test_cases": sub.passed_test_cases,
                "total_test_cases": sub.total_test_cases,
                "submitted_at": sub.submitted_at,
            }
            for sub in recent_activity
        ]

        return {
            "total_students": total_students,
            "participating_students": participating_students,
            "unattempted_students": unattempted_students,
            "total_attempts": total_attempts,
            "unique_questions_attempted": unique_questions_attempted,
            "accepted_submissions": accepted_submissions,
            "rejected_submissions": rejected_submissions,
            "pending_submissions": pending_submissions,
            "pass_rate_percentage": pass_rate_percentage,
            "verdict_breakdown": {
                "ACCEPTED": accepted_submissions,
                "WRONG_ANSWER": wrong_answers,
                "RUNTIME_ERROR": runtime_errors,
                "COMPILATION_ERROR": compilation_errors,
                "TIME_LIMIT_EXCEEDED": time_limit_exceeded,
                "MEMORY_LIMIT_EXCEEDED": memory_limit_exceeded,
                "PENDING_OR_QUEUED": pending_submissions,
            },
            "language_stats": language_stats,
            "recent_timeline": recent_timeline,
        }

    @classmethod
    def get_attendance_analytics(cls, tpo_user, batch_code=None) -> dict[str, Any]:
        """Compute institutional attendance distributions and policy compliance."""
        students_qs = TPODashboardService.get_college_students_queryset(tpo_user)
        if batch_code and batch_code != "ALL":
            students_qs = students_qs.filter(batch_code=batch_code)

        total_students = students_qs.count()
        if total_students == 0:
            return {
                "total_students": 0,
                "college_average_attendance": 0.0,
                "policy_threshold_percentage": 75.0,
                "distribution_bands": {
                    "excellent_gte_85": {"count": 0, "percentage": 0.0},
                    "satisfactory_75_to_84": {"count": 0, "percentage": 0.0},
                    "critical_below_75": {"count": 0, "percentage": 0.0},
                },
                "batch_breakdown": [],
                "critical_students": [],
                "has_session_records": False,
            }

        avg_stat = students_qs.aggregate(avg=Avg("attendance_percentage"))
        college_avg = float(round(avg_stat["avg"] or Decimal("0.0"), 2))

        # Distribution Bands
        excellent_cnt = students_qs.filter(attendance_percentage__gte=Decimal("85.00")).count()
        satisfactory_cnt = students_qs.filter(
            attendance_percentage__gte=Decimal("75.00"),
            attendance_percentage__lt=Decimal("85.00"),
        ).count()
        critical_cnt = students_qs.filter(attendance_percentage__lt=Decimal("75.00")).count()

        distribution_bands = {
            "excellent_gte_85": {
                "count": excellent_cnt,
                "percentage": round((excellent_cnt / total_students) * 100, 1),
            },
            "satisfactory_75_to_84": {
                "count": satisfactory_cnt,
                "percentage": round((satisfactory_cnt / total_students) * 100, 1),
            },
            "critical_below_75": {
                "count": critical_cnt,
                "percentage": round((critical_cnt / total_students) * 100, 1),
            },
        }

        # Batch Breakdown
        batch_stats = (
            students_qs.values("batch_code")
            .annotate(
                student_count=Count("id"),
                avg_attendance=Avg("attendance_percentage"),
            )
            .order_by("batch_code")
        )
        batch_breakdown = [
            {
                "batch_code": row["batch_code"] or "General",
                "student_count": row["student_count"],
                "average_attendance": float(round(row["avg_attendance"] or Decimal("0.0"), 1)),
            }
            for row in batch_stats
        ]

        # Students below 75%
        critical_students_qs = students_qs.filter(
            attendance_percentage__lt=Decimal("75.00")
        ).order_by("attendance_percentage", "full_name")
        critical_students = [
            {
                "id": str(s.id),
                "student_id_number": s.student_id_number,
                "full_name": s.full_name,
                "batch_code": s.batch_code,
                "branch": s.branch,
                "attendance_percentage": float(s.attendance_percentage),
                "attended_classes": s.attended_classes,
                "total_classes": s.total_classes,
            }
            for s in critical_students_qs
        ]

        student_ids = students_qs.values_list("id", flat=True)
        has_session_records = AttendanceRecord.objects.filter(
            student_profile_id__in=student_ids
        ).exists()

        return {
            "total_students": total_students,
            "college_average_attendance": college_avg,
            "policy_threshold_percentage": 75.0,
            "distribution_bands": distribution_bands,
            "batch_breakdown": batch_breakdown,
            "critical_students": critical_students,
            "has_session_records": has_session_records,
        }

    @classmethod
    def get_performance_trends(cls, tpo_user) -> dict[str, Any]:
        """Compute verified historical monthly trend lines for the assigned college."""
        students_qs = TPODashboardService.get_college_students_queryset(tpo_user)
        student_ids = list(students_qs.values_list("id", flat=True))

        if not student_ids:
            return {
                "has_sufficient_history": False,
                "unavailable_reason": "No student records available to calculate trends.",
                "monthly_score_trends": [],
                "monthly_submission_trends": [],
            }

        # 1. Monthly Score Trend
        score_trend_qs = (
            ScoreRecord.objects.filter(student_id__in=student_ids)
            .annotate(month=TruncMonth("awarded_at"))
            .values("month")
            .annotate(
                total_points=Sum("points"),
                awards_count=Count("id"),
            )
            .order_by("month")
        )

        monthly_score_trends = [
            {
                "period": row["month"].strftime("%b %Y") if row["month"] else "Recent",
                "total_points": float(row["total_points"] or 0.0),
                "awards_count": row["awards_count"],
            }
            for row in score_trend_qs
        ]

        # 2. Monthly Submission Trend
        sub_trend_qs = (
            CodeSubmission.objects.filter(student_id__in=student_ids)
            .annotate(month=TruncMonth("submitted_at"))
            .values("month")
            .annotate(
                total_submissions=Count("id"),
                accepted_submissions=Count(
                    "id",
                    filter=Q(status=CodeSubmission.SubmissionStatus.ACCEPTED),
                ),
            )
            .order_by("month")
        )

        monthly_submission_trends = [
            {
                "period": row["month"].strftime("%b %Y") if row["month"] else "Recent",
                "total_submissions": row["total_submissions"],
                "accepted_submissions": row["accepted_submissions"],
                "pass_rate": (
                    round((row["accepted_submissions"] / row["total_submissions"]) * 100, 1)
                    if row["total_submissions"] > 0
                    else 0.0
                ),
            }
            for row in sub_trend_qs
        ]

        has_sufficient = len(monthly_score_trends) >= 1 or len(monthly_submission_trends) >= 1

        return {
            "has_sufficient_history": has_sufficient,
            "unavailable_reason": (
                ""
                if has_sufficient
                else "Insufficient historical data points logged for this institution."
            ),
            "monthly_score_trends": monthly_score_trends,
            "monthly_submission_trends": monthly_submission_trends,
        }

    @classmethod
    def get_students_needing_support(
        cls, tpo_user, risk_type=None
    ) -> list[dict[str, Any]]:
        """Identify students requiring academic or attendance intervention using explicit, transparent rules."""
        students_qs = TPODashboardService.get_college_students_queryset(tpo_user)
        student_ids = list(students_qs.values_list("id", flat=True))

        # Pre-query submission stats per student
        sub_stats = {
            row["student_id"]: {
                "total": row["total"],
                "accepted": row["accepted"],
            }
            for row in CodeSubmission.objects.filter(student_id__in=student_ids)
            .values("student_id")
            .annotate(
                total=Count("id"),
                accepted=Count("id", filter=Q(status=CodeSubmission.SubmissionStatus.ACCEPTED)),
            )
        }

        # Pre-query module progress count
        completed_mod_counts = {
            row["student_id"]: row["cnt"]
            for row in StudentModuleProgress.objects.filter(
                student_id__in=student_ids,
                status=StudentModuleProgress.ModuleStatus.COMPLETED,
            )
            .values("student_id")
            .annotate(cnt=Count("id"))
        }

        flagged_students = []

        for s in students_qs:
            reasons = []
            s_subs = sub_stats.get(s.id, {"total": 0, "accepted": 0})
            completed_mods = completed_mod_counts.get(s.id, 0)

            # Rule 1: Low Attendance (< 75.00%)
            if s.attendance_percentage < Decimal("75.00"):
                reasons.append(
                    {
                        "code": "LOW_ATTENDANCE",
                        "label": "Low Attendance",
                        "severity": "HIGH" if s.attendance_percentage < Decimal("60.00") else "MEDIUM",
                        "detail": f"Attendance is {s.attendance_percentage}% (below 75% institutional threshold)",
                    }
                )

            # Rule 2: Zero Coding Submissions
            if s_subs["total"] == 0:
                reasons.append(
                    {
                        "code": "ZERO_SUBMISSIONS",
                        "label": "No Lab Attempts",
                        "severity": "HIGH",
                        "detail": "No coding assignments or lab exercises attempted yet",
                    }
                )
            # Rule 3: High Failure Rate on Coding Submissions
            elif s_subs["total"] >= 3 and s_subs["accepted"] == 0:
                reasons.append(
                    {
                        "code": "HIGH_FAILURE_RATE",
                        "label": "High Lab Error Rate",
                        "severity": "HIGH",
                        "detail": f"0 of {s_subs['total']} coding submissions accepted (0% pass rate)",
                    }
                )

            # Rule 4: Stalled Academic Progress (0 points & 0 modules completed & 0 streak)
            if s.total_points == Decimal("0.00") and completed_mods == 0 and s.current_streak_days == 0:
                reasons.append(
                    {
                        "code": "STALLED_PROGRESS",
                        "label": "Stalled Learning Progress",
                        "severity": "MEDIUM",
                        "detail": "0 points awarded and no completed curriculum modules",
                    }
                )

            if reasons:
                # If filtered by risk_type
                if risk_type and risk_type != "ALL":
                    if not any(r["code"] == risk_type for r in reasons):
                        continue

                flagged_students.append(
                    {
                        "id": str(s.id),
                        "student_id_number": s.student_id_number,
                        "full_name": s.full_name,
                        "batch_code": s.batch_code,
                        "branch": s.branch,
                        "course_opted": s.course_opted,
                        "attendance_percentage": float(s.attendance_percentage),
                        "total_points": float(s.total_points),
                        "submissions_count": s_subs["total"],
                        "accepted_submissions_count": s_subs["accepted"],
                        "reasons": reasons,
                    }
                )

        # Sort flagged students by number of high-severity reasons and lowest attendance
        flagged_students.sort(
            key=lambda x: (
                -len([r for r in x["reasons"] if r["severity"] == "HIGH"]),
                x["attendance_percentage"],
            )
        )

        return flagged_students

    @classmethod
    def get_college_leaderboard(cls, tpo_user, limit=50) -> list[dict[str, Any]]:
        """Return strictly college-scoped leaderboard ranking students by points and attendance."""
        students_qs = TPODashboardService.get_college_students_queryset(tpo_user)

        ranked_qs = students_qs.order_by(
            "-total_points",
            "-attendance_percentage",
            "-current_streak_days",
            "created_at",
        )[:limit]

        leaderboard = []
        for rank, s in enumerate(ranked_qs, start=1):
            leaderboard.append(
                {
                    "rank": rank,
                    "id": str(s.id),
                    "student_id_number": s.student_id_number,
                    "full_name": s.full_name,
                    "batch_code": s.batch_code,
                    "branch": s.branch,
                    "course_opted": s.course_opted,
                    "total_points": float(s.total_points),
                    "attendance_percentage": float(s.attendance_percentage),
                    "current_streak_days": s.current_streak_days,
                    "avatar_url": s.avatar_url,
                }
            )

        return leaderboard
