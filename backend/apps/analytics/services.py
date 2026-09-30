"""Domain services for executive institutional analytics, reporting, and asynchronous exports."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from django.core.cache import cache
from django.db.models import Avg, Case, Count, F, IntegerField, Max, Q, Sum, Value, When
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.accounts.models import User
from apps.analytics.models import ExportJob
from apps.analytics.tasks import dispatch_async_export
from apps.assignments.models import CodeSubmission, CodingQuestion, StudentQuestionProgress
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.projects.models import Project, ProjectSubmission
from apps.students.models import StudentProfile

logger = logging.getLogger(__name__)

CACHE_TTL_DASHBOARD = 120  # 2 minutes caching for high-load dashboard requests
CACHE_TTL_REPORTS = 180  # 3 minutes caching for heavy reports


class AnalyticsAdminService:
    """Service generating high-performance executive metrics, charts data, and reports."""

    @classmethod
    def _get_cache_key(cls, prefix: str, **kwargs) -> str:
        """Construct deterministic MD5 cache key from filter parameters."""
        raw_kwargs = json.dumps(kwargs, sort_keys=True, default=str)
        hashed = hashlib.md5(raw_kwargs.encode("utf-8")).hexdigest()
        return f"analytics:{prefix}:{hashed}"

    @classmethod
    def get_dashboard_analytics(
        cls,
        course_id: Optional[str] = None,
        batch_code: Optional[str] = None,
        days: int = 7,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Compute top-level KPI metrics, activity timelines, score distributions, and breakdown charts."""
        cache_key = cls._get_cache_key("dashboard", course_id=course_id, batch_code=batch_code, days=days)
        if use_cache:
            cached_val = cache.get(cache_key)
            if cached_val is not None:
                return cached_val

        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        timeline_start = now - timedelta(days=days)

        # 1. Student Metrics
        student_qs = StudentProfile.objects.select_related("user")
        if batch_code:
            student_qs = student_qs.filter(batch_code=batch_code.strip())
        if course_id:
            student_qs = student_qs.filter(enrollments__course_id=course_id)

        student_counts = student_qs.aggregate(
            total=Count("id"),
            active=Count(Case(When(user__is_active=True, then=1), output_field=IntegerField())),
        )
        total_students = student_counts["total"] or 0
        active_students = student_counts["active"] or 0

        # Top 5 Performers
        top_performers_qs = student_qs.filter(user__is_active=True).order_by("-total_points")[:5]
        top_performers = [
            {
                "id": str(s.id),
                "full_name": s.full_name,
                "student_id_number": s.student_id_number,
                "batch_code": s.batch_code,
                "total_points": float(s.total_points),
                "current_streak_days": s.current_streak_days,
            }
            for s in top_performers_qs
        ]

        # 2. Module & Curriculum Completion
        module_qs = Module.objects.filter(is_published=True)
        if course_id:
            module_qs = module_qs.filter(course_id=course_id)
        total_modules = module_qs.count()

        prog_qs = StudentModuleProgress.objects.filter(
            status=StudentModuleProgress.ModuleStatus.COMPLETED
        )
        if course_id:
            prog_qs = prog_qs.filter(module__course_id=course_id)
        if batch_code:
            prog_qs = prog_qs.filter(student__batch_code=batch_code.strip())
        completed_module_entries = prog_qs.count()

        expected_total = total_students * total_modules
        module_completion_rate = round(
            (completed_module_entries / expected_total * 100) if expected_total > 0 else 0, 2
        )

        # 3. Assignment Statistics
        sub_qs = CodeSubmission.objects.all()
        if course_id:
            sub_qs = sub_qs.filter(question__module__course_id=course_id)
        if batch_code:
            sub_qs = sub_qs.filter(student__batch_code=batch_code.strip())

        sub_stats = sub_qs.aggregate(
            total=Count("id"),
            accepted=Count(Case(When(status=CodeSubmission.SubmissionStatus.ACCEPTED, then=1), output_field=IntegerField())),
            today_total=Count(Case(When(submitted_at__gte=today_start, then=1), output_field=IntegerField())),
        )
        total_submissions = sub_stats["total"] or 0
        accepted_submissions = sub_stats["accepted"] or 0
        acceptance_rate = round(
            (accepted_submissions / total_submissions * 100) if total_submissions > 0 else 0, 2
        )

        today_submissions = sub_stats["today_total"] or 0
        today_active_students = (
            sub_qs.filter(submitted_at__gte=today_start)
            .values("student")
            .distinct()
            .count()
        )

        # Unique questions solved
        solved_qs = StudentQuestionProgress.objects.filter(is_solved=True)
        if course_id:
            solved_qs = solved_qs.filter(question__module__course_id=course_id)
        if batch_code:
            solved_qs = solved_qs.filter(student__batch_code=batch_code.strip())
        unique_solved_count = solved_qs.count()

        # Assignment difficulty distribution
        difficulty_counts = (
            CodingQuestion.objects.filter(is_active=True)
            .values("difficulty")
            .annotate(count=Count("id"))
        )
        diff_map = {d["difficulty"]: d["count"] for d in difficulty_counts}

        # 4. Project Completion Metrics
        project_qs = Project.objects.filter(is_active=True)
        if course_id:
            project_qs = project_qs.filter(course_id=course_id)
        total_projects = project_qs.count()

        proj_sub_qs = ProjectSubmission.objects.all()
        if course_id:
            proj_sub_qs = proj_sub_qs.filter(project__course_id=course_id)
        if batch_code:
            proj_sub_qs = proj_sub_qs.filter(student__batch_code=batch_code.strip())

        proj_stats = proj_sub_qs.aggregate(
            total_subs=Count("id"),
            approved_subs=Count(Case(When(status=ProjectSubmission.SubmissionStatus.APPROVED, then=1), output_field=IntegerField())),
            avg_score=Avg("score"),
        )
        total_project_subs = proj_stats["total_subs"] or 0
        approved_project_subs = proj_stats["approved_subs"] or 0
        project_approval_rate = round(
            (approved_project_subs / total_project_subs * 100) if total_project_subs > 0 else 0, 2
        )

        # 5. Score Distribution Buckets
        score_buckets = student_qs.aggregate(
            b_0_100=Count(Case(When(total_points__lte=100, then=1), output_field=IntegerField())),
            b_101_300=Count(Case(When(total_points__gt=100, total_points__lte=300, then=1), output_field=IntegerField())),
            b_301_600=Count(Case(When(total_points__gt=300, total_points__lte=600, then=1), output_field=IntegerField())),
            b_601_1000=Count(Case(When(total_points__gt=600, total_points__lte=1000, then=1), output_field=IntegerField())),
            b_1000_plus=Count(Case(When(total_points__gt=1000, then=1), output_field=IntegerField())),
        )
        score_distribution = [
            {"bracket": "0 - 100 pts", "count": score_buckets["b_0_100"] or 0},
            {"bracket": "101 - 300 pts", "count": score_buckets["b_101_300"] or 0},
            {"bracket": "301 - 600 pts", "count": score_buckets["b_301_600"] or 0},
            {"bracket": "601 - 1000 pts", "count": score_buckets["b_601_1000"] or 0},
            {"bracket": "1000+ pts", "count": score_buckets["b_1000_plus"] or 0},
        ]

        # 6. Daily Activity Timeline Chart
        daily_sub_counts = (
            sub_qs.filter(submitted_at__gte=timeline_start)
            .annotate(date=TruncDate("submitted_at"))
            .values("date")
            .annotate(
                submissions_count=Count("id"),
                active_students=Count("student", distinct=True),
            )
            .order_by("date")
        )
        timeline_dict = {
            item["date"].strftime("%Y-%m-%d"): {
                "submissions_count": item["submissions_count"],
                "active_students": item["active_students"],
            }
            for item in daily_sub_counts
            if item["date"]
        }

        timeline = []
        for i in range(days):
            day_dt = (timeline_start + timedelta(days=i)).date()
            day_str = day_dt.strftime("%Y-%m-%d")
            entry = timeline_dict.get(day_str, {"submissions_count": 0, "active_students": 0})
            timeline.append({
                "date": day_str,
                "label": day_dt.strftime("%b %d"),
                "submissions_count": entry["submissions_count"],
                "active_students": entry["active_students"],
            })

        result = {
            "total_students": total_students,
            "active_students": active_students,
            "module_completion_rate": module_completion_rate,
            "total_modules": total_modules,
            "completed_modules_count": completed_module_entries,
            "assignment_statistics": {
                "total_submissions": total_submissions,
                "accepted_submissions": accepted_submissions,
                "acceptance_rate": acceptance_rate,
                "unique_solved_count": unique_solved_count,
                "difficulty_distribution": {
                    "easy": diff_map.get("EASY", 0),
                    "medium": diff_map.get("MEDIUM", 0),
                    "hard": diff_map.get("HARD", 0),
                },
            },
            "today_activity": {
                "submissions_count": today_submissions,
                "active_students_count": today_active_students,
            },
            "project_statistics": {
                "total_projects": total_projects,
                "total_submissions": total_project_subs,
                "approved_submissions": approved_project_subs,
                "approval_rate": project_approval_rate,
                "average_score": float(proj_stats["avg_score"] or 0),
            },
            "score_distribution": score_distribution,
            "top_performers": top_performers,
            "activity_timeline": timeline,
            "filters_applied": {
                "course_id": course_id,
                "batch_code": batch_code,
                "days": days,
            },
        }

        cache.set(cache_key, result, CACHE_TTL_DASHBOARD)
        return result

    @classmethod
    def get_performance_report(
        cls,
        batch_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Aggregate student performance telemetry, cohort averages, and top scores."""
        cache_key = cls._get_cache_key("perf_report", batch_code=batch_code, start_date=start_date, end_date=end_date)
        if use_cache:
            cached_val = cache.get(cache_key)
            if cached_val is not None:
                return cached_val

        qs = StudentProfile.objects.select_related("user").filter(user__is_active=True)
        if batch_code:
            qs = qs.filter(batch_code=batch_code.strip())

        stats = qs.aggregate(
            avg_points=Avg("total_points"),
            max_points=Max("total_points"),
            avg_streak=Avg("current_streak_days"),
            max_streak=Max("highest_streak_days"),
            total_students=Count("id"),
        )

        batch_breakdown = (
            StudentProfile.objects.filter(user__is_active=True)
            .values("batch_code")
            .annotate(
                student_count=Count("id"),
                avg_points=Avg("total_points"),
                total_points_sum=Sum("total_points"),
            )
            .order_by("-avg_points")
        )

        student_list = [
            {
                "id": str(s.id),
                "student_id_number": s.student_id_number,
                "full_name": s.full_name,
                "batch_code": s.batch_code,
                "total_points": float(s.total_points),
                "current_streak_days": s.current_streak_days,
                "status": "ACTIVE" if s.user.is_active else "INACTIVE",
            }
            for s in qs.order_by("-total_points")[:200]
        ]

        result = {
            "batch_code": batch_code or "ALL",
            "total_students": stats["total_students"] or 0,
            "average_points": str(round(stats["avg_points"] or 0, 2)),
            "highest_points": str(stats["max_points"] or "0.00"),
            "average_streak_days": round(stats["avg_streak"] or 0, 1),
            "highest_streak_days": stats["max_streak"] or 0,
            "batch_breakdown": [
                {
                    "batch_code": b["batch_code"],
                    "student_count": b["student_count"],
                    "average_points": str(round(b["avg_points"] or 0, 2)),
                    "total_points": str(b["total_points_sum"] or "0.00"),
                }
                for b in batch_breakdown
            ],
            "students": student_list,
        }

        cache.set(cache_key, result, CACHE_TTL_REPORTS)
        return result

    @classmethod
    def get_completion_report(
        cls,
        course_id: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Aggregate course curriculum progress, enrollment statistics, and module completion rates."""
        cache_key = cls._get_cache_key("comp_report", course_id=course_id)
        if use_cache:
            cached_val = cache.get(cache_key)
            if cached_val is not None:
                return cached_val

        courses_qs = Course.objects.filter(is_deleted=False)
        if course_id:
            courses_qs = courses_qs.filter(id=course_id)

        course_data = []
        for course in courses_qs:
            enrolled_count = CourseEnrollment.objects.filter(
                course=course, status=CourseEnrollment.EnrollmentStatus.ACTIVE
            ).count()
            completed_count = CourseEnrollment.objects.filter(
                course=course, status=CourseEnrollment.EnrollmentStatus.COMPLETED
            ).count()

            modules = Module.objects.filter(course=course, is_published=True).order_by("order_index")
            module_stats = []
            for mod in modules:
                completed_mods = StudentModuleProgress.objects.filter(
                    module=mod, status=StudentModuleProgress.ModuleStatus.COMPLETED
                ).count()
                rate = round(
                    (completed_mods / enrolled_count * 100) if enrolled_count > 0 else 0, 2
                )
                module_stats.append({
                    "module_id": str(mod.id),
                    "module_title": mod.title,
                    "order_index": mod.order_index,
                    "completed_students": completed_mods,
                    "completion_rate": rate,
                })

            course_data.append({
                "course_id": str(course.id),
                "course_title": course.title,
                "active_enrollments": enrolled_count,
                "completed_enrollments": completed_count,
                "modules": module_stats,
            })

        result = {"courses": course_data}
        cache.set(cache_key, result, CACHE_TTL_REPORTS)
        return result

    @classmethod
    def get_assignment_report(
        cls,
        module_id: Optional[str] = None,
        course_id: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Aggregate question-level pass rates, test case failures, and difficulty analytics."""
        cache_key = cls._get_cache_key("assign_report", module_id=module_id, course_id=course_id)
        if use_cache:
            cached_val = cache.get(cache_key)
            if cached_val is not None:
                return cached_val

        questions = CodingQuestion.objects.filter(is_active=True).select_related("module", "module__course")
        if module_id:
            questions = questions.filter(module_id=module_id)
        if course_id:
            questions = questions.filter(module__course_id=course_id)

        questions = questions.order_by("module__course", "module__order_index", "order")

        question_stats = []
        for q in questions:
            sub_agg = CodeSubmission.objects.filter(question=q).aggregate(
                total=Count("id"),
                accepted=Count(Case(When(status=CodeSubmission.SubmissionStatus.ACCEPTED, then=1), output_field=IntegerField())),
            )
            total_sub = sub_agg["total"] or 0
            acc_sub = sub_agg["accepted"] or 0
            solved_students = StudentQuestionProgress.objects.filter(question=q, is_solved=True).count()
            pass_rate = round((acc_sub / total_sub * 100) if total_sub > 0 else 0, 2)

            question_stats.append({
                "question_id": str(q.id),
                "title": q.title,
                "module_title": q.module.title,
                "course_title": q.module.course.title,
                "difficulty": q.difficulty,
                "points": str(q.points),
                "total_submissions": total_sub,
                "accepted_submissions": acc_sub,
                "pass_rate": pass_rate,
                "unique_students_solved": solved_students,
            })

        result = {"questions": question_stats}
        cache.set(cache_key, result, CACHE_TTL_REPORTS)
        return result

    @classmethod
    def get_project_report(
        cls,
        course_id: Optional[str] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Aggregate capstone project submissions, evaluations, and grading distributions."""
        cache_key = cls._get_cache_key("proj_report", course_id=course_id)
        if use_cache:
            cached_val = cache.get(cache_key)
            if cached_val is not None:
                return cached_val

        projects = Project.objects.filter(is_active=True).select_related("course")
        if course_id:
            projects = projects.filter(course_id=course_id)

        project_stats = []
        for p in projects:
            subs = ProjectSubmission.objects.filter(project=p)
            sub_agg = subs.aggregate(
                total=Count("id"),
                approved=Count(Case(When(status=ProjectSubmission.SubmissionStatus.APPROVED, then=1), output_field=IntegerField())),
                under_review=Count(Case(When(status=ProjectSubmission.SubmissionStatus.UNDER_REVIEW, then=1), output_field=IntegerField())),
                rejected=Count(Case(When(status=ProjectSubmission.SubmissionStatus.REJECTED, then=1), output_field=IntegerField())),
                avg_score=Avg("score"),
            )

            project_stats.append({
                "project_id": str(p.id),
                "title": p.title,
                "course_title": p.course.title if p.course else None,
                "max_score": str(p.max_score),
                "total_submissions": sub_agg["total"] or 0,
                "approved_submissions": sub_agg["approved"] or 0,
                "under_review_submissions": sub_agg["under_review"] or 0,
                "rejected_submissions": sub_agg["rejected"] or 0,
                "average_score": str(round(sub_agg["avg_score"] or 0, 2)),
            })

        result = {"projects": project_stats}
        cache.set(cache_key, result, CACHE_TTL_REPORTS)
        return result

    @classmethod
    def get_monthly_activity_report(
        cls,
        days: int = 30,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Compile comprehensive time series activity analysis across submissions and user logins."""
        cache_key = cls._get_cache_key("month_report", days=days)
        if use_cache:
            cached_val = cache.get(cache_key)
            if cached_val is not None:
                return cached_val

        now = timezone.now()
        start_date = (now - timedelta(days=days)).date()
        start_dt = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))

        daily_sub_counts = (
            CodeSubmission.objects.filter(submitted_at__gte=start_dt)
            .annotate(date=TruncDate("submitted_at"))
            .values("date")
            .annotate(
                submissions_count=Count("id"),
                active_students=Count("student", distinct=True),
            )
            .order_by("date")
        )
        timeline_dict = {
            item["date"].strftime("%Y-%m-%d"): {
                "submissions_count": item["submissions_count"],
                "active_students": item["active_students"],
            }
            for item in daily_sub_counts
            if item["date"]
        }

        timeline = []
        for i in range(days):
            current_day = start_date + timedelta(days=i)
            day_str = current_day.strftime("%Y-%m-%d")
            entry = timeline_dict.get(day_str, {"submissions_count": 0, "active_students": 0})
            timeline.append({
                "date": day_str,
                "label": current_day.strftime("%b %d"),
                "submissions_count": entry["submissions_count"],
                "active_students": entry["active_students"],
            })

        result = {"days_analyzed": days, "timeline": timeline}
        cache.set(cache_key, result, CACHE_TTL_REPORTS)
        return result

    # --------------------------------------------------------------------------
    # ASYNCHRONOUS REPORT EXPORT ARCHITECTURE
    # --------------------------------------------------------------------------
    @classmethod
    def create_export_job(
        cls,
        user: User,
        report_type: str,
        export_format: str = "CSV",
        filters: Optional[Dict[str, Any]] = None,
    ) -> ExportJob:
        """Create non-blocking export job and dispatch to background worker pool."""
        job = ExportJob.objects.create(
            user=user,
            report_type=report_type,
            format=export_format.upper(),
            status=ExportJob.JobStatus.PENDING,
            filters=filters or {},
        )
        dispatch_async_export(str(job.id))
        return job

    @classmethod
    def list_export_jobs(cls, user: Optional[User] = None):
        """List export jobs with optional user filter."""
        qs = ExportJob.objects.select_related("user").order_by("-created_at")
        if user and not (user.is_superuser or getattr(user, "role", "") == "ADMIN"):
            qs = qs.filter(user=user)
        return qs
