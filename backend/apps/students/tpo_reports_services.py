"""Service layer for TPO reports, secure data export generation, and auditability."""

import csv
import io
import logging
from decimal import Decimal
from typing import Any

from django.db import models
from django.db.models import Avg, Count, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone

from apps.accounts.models import AuditLog
from apps.assignments.models import CodeSubmission
from apps.common.exceptions import DomainException
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.students.models import College, StudentProfile
from apps.students.tpo_services import TPOAnalyticsService, TPODashboardService

logger = logging.getLogger(__name__)


def sanitize_csv_cell(value: Any) -> str:
    """Mitigate CSV Formula Injection by prepending single quote if cell starts with risky chars."""
    if value is None:
        return ""
    str_val = str(value)
    if str_val and str_val[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{str_val}"
    return str_val


class TPOReportsService:
    """Production reporting service generating strictly college-scoped, secure report artifacts."""

    SUPPORTED_REPORTS = [
        {
            "id": "STUDENT_ROSTER",
            "name": "College Student Roster",
            "description": "Comprehensive enrollment roster of all students in your assigned institution.",
            "supported_formats": ["CSV", "JSON"],
            "supported_filters": ["batch_code", "course_opted", "is_active"],
        },
        {
            "id": "ATTENDANCE_COMPLIANCE",
            "name": "Attendance Compliance Report",
            "description": "Student-level attendance percentages, 75% policy threshold status, and placement eligibility.",
            "supported_formats": ["CSV", "JSON"],
            "supported_filters": ["batch_code"],
        },
        {
            "id": "LEARNING_PROGRESS",
            "name": "Curriculum & Module Progress Report",
            "description": "Detailed module completion metrics, syllabus milestones, and progression statuses.",
            "supported_formats": ["CSV", "JSON"],
            "supported_filters": ["course_id", "status"],
        },
        {
            "id": "ASSIGNMENTS_LABS",
            "name": "Assignment & Lab Performance Report",
            "description": "Coding challenge participation, attempts, accepted verdicts, pass rates, and points.",
            "supported_formats": ["CSV", "JSON"],
            "supported_filters": ["date_from", "date_to"],
        },
        {
            "id": "STUDENTS_NEEDING_SUPPORT",
            "name": "Students Needing Academic Support Report",
            "description": "Actionable list of students flagged for attendance deficit, lab inaction, or stalled progress.",
            "supported_formats": ["CSV", "JSON"],
            "supported_filters": ["risk_type"],
        },
        {
            "id": "COLLEGE_SUMMARY",
            "name": "College Performance & Telemetry Summary",
            "description": "Executive institutional summary with attendance, lab pass rates, and track distributions.",
            "supported_formats": ["CSV", "JSON"],
            "supported_filters": [],
        },
    ]

    @classmethod
    def get_supported_reports(cls) -> list[dict[str, Any]]:
        """Return registry of available report types and their supported capabilities."""
        return cls.SUPPORTED_REPORTS

    @classmethod
    def _build_student_roster_data(cls, tpo_user, filters: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
        qs = TPODashboardService.get_college_students_queryset(tpo_user)

        batch_code = filters.get("batch_code")
        if batch_code and batch_code != "ALL":
            qs = qs.filter(batch_code=batch_code)

        course_opted = filters.get("course_opted")
        if course_opted and course_opted != "ALL":
            qs = qs.filter(course_opted__icontains=course_opted)

        is_active = filters.get("is_active")
        if is_active is not None and is_active != "" and is_active != "ALL":
            is_act_bool = str(is_active).lower() in ("true", "1", "yes")
            qs = qs.filter(user__is_active=is_act_bool)

        headers = [
            "Student ID",
            "Full Name",
            "Email",
            "Mobile Number",
            "Batch Code",
            "Branch",
            "Course Opted",
            "Attendance %",
            "Total Points",
            "Current Streak (Days)",
            "Account Status",
            "Joined Date",
        ]

        rows = []
        for s in qs.order_by("full_name"):
            rows.append([
                s.student_id_number,
                s.full_name,
                s.user.email if s.user else "",
                s.user.mobile_number if s.user else "",
                s.batch_code or "Unassigned",
                s.branch or "General",
                s.course_opted or "General Track",
                float(s.attendance_percentage),
                float(s.total_points),
                s.current_streak_days,
                "Active" if (s.user and s.user.is_active) else "Inactive",
                s.created_at.strftime("%Y-%m-%d"),
            ])

        return headers, rows

    @classmethod
    def _build_attendance_compliance_data(cls, tpo_user, filters: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
        qs = TPODashboardService.get_college_students_queryset(tpo_user)

        batch_code = filters.get("batch_code")
        if batch_code and batch_code != "ALL":
            qs = qs.filter(batch_code=batch_code)

        headers = [
            "Student ID",
            "Full Name",
            "Batch Code",
            "Branch",
            "Classes Attended",
            "Total Classes",
            "Attendance %",
            "Policy Threshold Status (>=75%)",
            "Placement Eligibility Status",
        ]

        rows = []
        for s in qs.order_by("attendance_percentage", "full_name"):
            att_pct = float(s.attendance_percentage)
            is_compliant = att_pct >= 75.0
            rows.append([
                s.student_id_number,
                s.full_name,
                s.batch_code or "Unassigned",
                s.branch or "General",
                s.attended_classes,
                s.total_classes,
                att_pct,
                "Compliant (>=75%)" if is_compliant else "Deficit (<75%)",
                "Eligible" if is_compliant else "At Risk",
            ])

        return headers, rows

    @classmethod
    def _build_learning_progress_data(cls, tpo_user, filters: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
        course_id = filters.get("course_id")
        progress_data = TPOAnalyticsService.get_learning_progress(tpo_user, course_id=course_id)

        headers = [
            "Student ID",
            "Full Name",
            "Batch Code",
            "Branch",
            "Track Opted",
            "Completed Modules",
            "Total Applicable Modules",
            "Completion %",
            "Progression Status",
        ]

        status_filter = filters.get("status")
        rows = []
        for s in progress_data["student_progress"]:
            if status_filter and status_filter != "ALL" and s["status"] != status_filter:
                continue
            rows.append([
                s["student_id_number"],
                s["full_name"],
                s["batch_code"],
                s["branch"],
                s["course_opted"],
                s["completed_modules"],
                s["total_modules"],
                s["progress_percentage"],
                s["status"],
            ])

        return headers, rows

    @classmethod
    def _build_assignments_labs_data(cls, tpo_user, filters: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")
        students_qs = TPODashboardService.get_college_students_queryset(tpo_user)
        student_ids = list(students_qs.values_list("id", flat=True))

        subs_qs = CodeSubmission.objects.filter(student_id__in=student_ids)
        if date_from:
            subs_qs = subs_qs.filter(submitted_at__date__gte=date_from)
        if date_to:
            subs_qs = subs_qs.filter(submitted_at__date__lte=date_to)

        # Aggregate stats per student
        student_stats = {
            row["student_id"]: {
                "total_attempts": row["total_attempts"],
                "unique_questions": row["unique_questions"],
                "accepted": row["accepted"],
                "rejected": row["rejected"],
                "score_sum": float(row["score_sum"] or 0.0),
            }
            for row in subs_qs.values("student_id").annotate(
                total_attempts=Count("id"),
                unique_questions=Count("question_id", distinct=True),
                accepted=Count("id", filter=Q(status=CodeSubmission.SubmissionStatus.ACCEPTED)),
                rejected=Count(
                    "id",
                    filter=Q(
                        status__in=[
                            CodeSubmission.SubmissionStatus.WRONG_ANSWER,
                            CodeSubmission.SubmissionStatus.RUNTIME_ERROR,
                            CodeSubmission.SubmissionStatus.COMPILATION_ERROR,
                            CodeSubmission.SubmissionStatus.TIME_LIMIT_EXCEEDED,
                            CodeSubmission.SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
                        ]
                    ),
                ),
                score_sum=models.Sum("score_awarded"),
            )
        }

        headers = [
            "Student ID",
            "Full Name",
            "Batch Code",
            "Branch",
            "Unique Questions Attempted",
            "Total Submission Attempts",
            "Accepted Submissions",
            "Rejected Submissions",
            "Evaluated Pass Rate %",
            "Total Points Earned",
        ]

        rows = []
        for s in students_qs.order_by("full_name"):
            st = student_stats.get(
                s.id,
                {"total_attempts": 0, "unique_questions": 0, "accepted": 0, "rejected": 0, "score_sum": 0.0},
            )
            evaluated = st["accepted"] + st["rejected"]
            pass_rate = round((st["accepted"] / evaluated) * 100, 1) if evaluated > 0 else 0.0

            rows.append([
                s.student_id_number,
                s.full_name,
                s.batch_code or "Unassigned",
                s.branch or "General",
                st["unique_questions"],
                st["total_attempts"],
                st["accepted"],
                st["rejected"],
                pass_rate,
                st["score_sum"],
            ])

        return headers, rows

    @classmethod
    def _build_students_needing_support_data(cls, tpo_user, filters: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
        risk_type = filters.get("risk_type")
        flagged_students = TPOAnalyticsService.get_students_needing_support(tpo_user, risk_type=risk_type)

        headers = [
            "Student ID",
            "Full Name",
            "Batch Code",
            "Branch",
            "Attendance %",
            "Total Points",
            "Lab Attempts Count",
            "Accepted Labs Count",
            "Highest Severity",
            "Support Reasons & Explanation",
        ]

        rows = []
        for s in flagged_students:
            severities = [r["severity"] for r in s["reasons"]]
            highest_sev = "HIGH" if "HIGH" in severities else "MEDIUM"
            reasons_summary = "; ".join([f"{r['label']} ({r['detail']})" for r in s["reasons"]])

            rows.append([
                s["student_id_number"],
                s["full_name"],
                s["batch_code"],
                s["branch"],
                s["attendance_percentage"],
                s["total_points"],
                s["submissions_count"],
                s["accepted_submissions_count"],
                highest_sev,
                reasons_summary,
            ])

        return headers, rows

    @classmethod
    def _build_college_summary_data(cls, tpo_user, filters: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
        summary = TPODashboardService.get_college_summary(tpo_user)

        headers = [
            "Metric Name",
            "Metric Value",
            "Institutional Details / Denominator",
        ]

        rows = [
            ["Institution Name", summary["college"]["name"], f"Code: {summary['college']['code']}"],
            ["Campus Location", f"{summary['college']['city']}, {summary['college']['state']}", "Assigned College"],
            ["Total Registered Students", summary["total_students"], "All enrolled roster profiles"],
            ["Active Students", summary["active_students"], "Active login access"],
            ["Suspended / Inactive Students", summary["inactive_students"], "Deactivated"],
            ["Average Attendance Percentage", f"{summary['average_attendance_percentage']}%", "College-wide average"],
            ["Students Meeting Attendance Policy (>=75%)", summary["students_above_75_attendance"], f"Of {summary['total_students']} total students"],
            ["Total Lab Submissions", summary["total_submissions"], "All student coding attempts"],
            ["Accepted Lab Submissions", summary["accepted_submissions"], "Passed all test cases"],
            ["Top Student High Score", f"{summary['top_performers'][0]['total_points']} pts" if summary["top_performers"] else "0 pts", summary["top_performers"][0]["full_name"] if summary["top_performers"] else "N/A"],
        ]

        return headers, rows

    @classmethod
    def generate_report_preview(
        cls, tpo_user, report_type: str, filters: dict[str, Any], ip_address: str | None = None
    ) -> dict[str, Any]:
        """Generate a preview representation (column headers and first 25 sample rows)."""
        college = TPODashboardService.get_assigned_college_or_fail(tpo_user)
        report_type_clean = report_type.strip().upper()

        if report_type_clean == "STUDENT_ROSTER":
            headers, rows = cls._build_student_roster_data(tpo_user, filters)
        elif report_type_clean == "ATTENDANCE_COMPLIANCE":
            headers, rows = cls._build_attendance_compliance_data(tpo_user, filters)
        elif report_type_clean == "LEARNING_PROGRESS":
            headers, rows = cls._build_learning_progress_data(tpo_user, filters)
        elif report_type_clean == "ASSIGNMENTS_LABS":
            headers, rows = cls._build_assignments_labs_data(tpo_user, filters)
        elif report_type_clean == "STUDENTS_NEEDING_SUPPORT":
            headers, rows = cls._build_students_needing_support_data(tpo_user, filters)
        elif report_type_clean == "COLLEGE_SUMMARY":
            headers, rows = cls._build_college_summary_data(tpo_user, filters)
        else:
            raise DomainException(
                detail=f"Unsupported report type '{report_type}'.",
                code="INVALID_REPORT_TYPE",
                status_code=400,
            )

        # Audit preview request
        AuditLog.objects.create(
            actor=tpo_user,
            action="TPO_REPORT_PREVIEW",
            target_model="College",
            target_id=str(college.id),
            ip_address=ip_address,
            payload={
                "report_type": report_type_clean,
                "college_id": str(college.id),
                "college_name": college.name,
                "total_rows": len(rows),
                "filters": filters,
            },
        )

        return {
            "report_type": report_type_clean,
            "college": {
                "id": str(college.id),
                "name": college.name,
                "code": college.code,
            },
            "total_rows": len(rows),
            "columns": headers,
            "preview_rows": rows[:25],
            "generated_at": timezone.now().isoformat(),
        }

    @classmethod
    def generate_report_export(
        cls,
        tpo_user,
        report_type: str,
        export_format: str = "CSV",
        filters: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> HttpResponse:
        """Stream secure, injection-sanitized CSV or JSON export artifact."""
        college = TPODashboardService.get_assigned_college_or_fail(tpo_user)
        report_type_clean = report_type.strip().upper()
        format_clean = export_format.strip().upper()
        filters_clean = filters or {}

        if report_type_clean == "STUDENT_ROSTER":
            headers, rows = cls._build_student_roster_data(tpo_user, filters_clean)
        elif report_type_clean == "ATTENDANCE_COMPLIANCE":
            headers, rows = cls._build_attendance_compliance_data(tpo_user, filters_clean)
        elif report_type_clean == "LEARNING_PROGRESS":
            headers, rows = cls._build_learning_progress_data(tpo_user, filters_clean)
        elif report_type_clean == "ASSIGNMENTS_LABS":
            headers, rows = cls._build_assignments_labs_data(tpo_user, filters_clean)
        elif report_type_clean == "STUDENTS_NEEDING_SUPPORT":
            headers, rows = cls._build_students_needing_support_data(tpo_user, filters_clean)
        elif report_type_clean == "COLLEGE_SUMMARY":
            headers, rows = cls._build_college_summary_data(tpo_user, filters_clean)
        else:
            raise DomainException(
                detail=f"Unsupported report type '{report_type}'.",
                code="INVALID_REPORT_TYPE",
                status_code=400,
            )

        timestamp_str = timezone.now().strftime("%Y%m%d_%H%M%S")
        college_code_safe = (college.code or college.name or "institution").lower().replace(" ", "_").replace("-", "_")
        report_name_safe = report_type_clean.lower()

        # Audit export action
        AuditLog.objects.create(
            actor=tpo_user,
            action="TPO_REPORT_EXPORT",
            target_model="College",
            target_id=str(college.id),
            ip_address=ip_address,
            payload={
                "report_type": report_type_clean,
                "format": format_clean,
                "college_id": str(college.id),
                "college_name": college.name,
                "row_count": len(rows),
                "filters": filters_clean,
            },
        )

        if format_clean == "JSON":
            # Format as JSON list of dicts
            json_records = []
            for row in rows:
                json_records.append(dict(zip(headers, row)))

            response = JsonResponse(
                {
                    "report_type": report_type_clean,
                    "college": {"name": college.name, "code": college.code},
                    "generated_at": timezone.now().isoformat(),
                    "total_rows": len(rows),
                    "data": json_records,
                },
                json_dumps_params={"indent": 2},
            )
            response["Content-Disposition"] = f'attachment; filename="{college_code_safe}_{report_name_safe}_{timestamp_str}.json"'
            return response

        elif format_clean == "CSV":
            buffer = io.StringIO()
            writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)

            # Write headers
            writer.writerow(headers)

            # Write sanitized rows
            for row in rows:
                sanitized_row = [sanitize_csv_cell(cell) for cell in row]
                writer.writerow(sanitized_row)

            # Encode as UTF-8 with BOM for Excel compatibility
            csv_content = buffer.getvalue().encode("utf-8-sig")

            response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = f'attachment; filename="{college_code_safe}_{report_name_safe}_{timestamp_str}.csv"'
            return response

        else:
            raise DomainException(
                detail=f"Unsupported format '{export_format}'. Supported formats: CSV, JSON.",
                code="INVALID_FORMAT",
                status_code=400,
            )
