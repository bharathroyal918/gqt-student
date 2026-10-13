import csv
import datetime
import io
import logging
import re
import uuid
from decimal import Decimal
from typing import Any

from django.db import models
from django.db.models import Avg, Count, Q
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework import serializers

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


REPORT_FILENAME_MAP = {
    "STUDENT_ROSTER": "student_roster",
    "ATTENDANCE_COMPLIANCE": "attendance_compliance",
    "LEARNING_PROGRESS": "learning_progress",
    "ASSIGNMENTS_LABS": "assignments_labs",
    "STUDENTS_NEEDING_SUPPORT": "students_needing_support",
    "COLLEGE_SUMMARY": "college_summary",
}


def sanitize_college_identifier(name_or_code: str | None) -> str:
    """Normalize college identifier to safe ASCII alphanumeric and underscore characters."""
    if not name_or_code:
        return "institution"
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", str(name_or_code)).strip("_").lower()
    return clean[:50] if clean else "institution"


def generate_safe_report_filename(
    college: College, report_type: str, extension: str
) -> str:
    """Build secure filename preventing header injection, path traversal, and control chars."""
    timestamp_str = timezone.now().strftime("%Y%m%d_%H%M%S")
    raw_college_id = (getattr(college, "code", "") or "").strip() or (
        getattr(college, "name", "") or ""
    ).strip()
    safe_college_code = sanitize_college_identifier(raw_college_id)
    report_type_clean = report_type.strip().upper()
    safe_report_name = REPORT_FILENAME_MAP.get(report_type_clean, "report")
    safe_extension = "csv" if extension.lower() == "csv" else "json"
    filename = f"{safe_college_code}_{safe_report_name}_{timestamp_str}.{safe_extension}"
    if any(c in filename for c in ("\r", "\n", '"', "'", "/", "\\")):
        return f"institution_{safe_report_name}_{timestamp_str}.{safe_extension}"
    return filename


DATE_EXACT_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_strict_date(val: Any, field_name: str) -> datetime.date:
    """Strictly validate date string in exact YYYY-MM-DD format. Rejects whitespace, compact, timestamps, and invalid calendar dates."""
    if not isinstance(val, str):
        raise serializers.ValidationError(
            f"Invalid {field_name} format. Expected string in exact YYYY-MM-DD format.",
            code="INVALID_DATE_FORMAT",
        )
    if not DATE_EXACT_REGEX.match(val):
        raise serializers.ValidationError(
            f"Invalid {field_name} format '{val}'. Expected exact format YYYY-MM-DD without whitespace.",
            code="INVALID_DATE_FORMAT",
        )
    try:
        parsed = datetime.datetime.strptime(val, "%Y-%m-%d").date()
    except ValueError:
        raise serializers.ValidationError(
            f"Invalid calendar date for {field_name} '{val}'.",
            code="INVALID_DATE_FORMAT",
        )
    return parsed


class TPOReportsService:
    """Production reporting service generating strictly college-scoped, secure report artifacts."""

    SUPPORTED_REPORTS = [
        {
            "id": "STUDENT_ROSTER",
            "name": "College Student Roster",
            "description": "Comprehensive enrollment roster of all students in your assigned institution.",
            "supported_formats": ["CSV", "JSON"],
            "supported_filters": ["batch_code", "graduation_year", "course_opted", "is_active"],
        },
        {
            "id": "ATTENDANCE_COMPLIANCE",
            "name": "Attendance Compliance Report",
            "description": "Student-level attendance percentages, 75% policy threshold status, and placement eligibility.",
            "supported_formats": ["CSV", "JSON"],
            "supported_filters": ["batch_code", "graduation_year"],
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
            "supported_filters": ["date_from", "date_to", "graduation_year"],
        },
        {
            "id": "STUDENTS_NEEDING_SUPPORT",
            "name": "Students Needing Academic Support Report",
            "description": "Actionable list of students flagged for attendance deficit, lab inaction, or stalled progress.",
            "supported_formats": ["CSV", "JSON"],
            "supported_filters": ["risk_type", "graduation_year"],
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
    def validate_report_filters(
        cls, report_type: str | None, filters: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Strictly validate and normalize filters according to the report's registry schema."""
        if not report_type or not str(report_type).strip():
            raise serializers.ValidationError(
                "report_type is required.", code="INVALID_REPORT_TYPE"
            )

        report_type_clean = str(report_type).strip().upper()
        matching_report = next(
            (r for r in cls.SUPPORTED_REPORTS if r["id"] == report_type_clean),
            None,
        )
        if not matching_report:
            supported_ids = ", ".join(r["id"] for r in cls.SUPPORTED_REPORTS)
            raise serializers.ValidationError(
                f"Unsupported report type '{report_type}'. Supported report types: {supported_ids}.",
                code="INVALID_REPORT_TYPE",
            )

        if filters is None:
            filters = {}

        if not isinstance(filters, dict):
            raise serializers.ValidationError(
                "Filters payload must be a dictionary.", code="INVALID_FILTER_PAYLOAD"
            )

        if len(filters) > 10:
            raise serializers.ValidationError(
                "Too many filter parameters. Maximum allowed is 10.",
                code="FILTER_PAYLOAD_TOO_LARGE",
            )

        # 1. Key and value safety constraints (validate key types and length limits first)
        # Must execute before computing unknown keys to prevent TypeErrors on non-string keys
        for key, val in filters.items():
            if not isinstance(key, str) or len(key) > 50:
                raise serializers.ValidationError(
                    f"Filter key '{key}' is invalid or exceeds 50 characters. All filter keys must be strings.",
                    code="INVALID_FILTER_KEY",
                )
            if isinstance(val, str) and len(val) > 200:
                raise serializers.ValidationError(
                    f"Filter value for '{key}' exceeds maximum length of 200 characters.",
                    code="FILTER_VALUE_TOO_LONG",
                )

        # 2. Unknown filter keys validation
        supported_filters = set(matching_report["supported_filters"])
        provided_keys = set(filters.keys())
        unknown_keys = provided_keys - supported_filters
        if unknown_keys:
            supported_str = ", ".join(sorted(str(k) for k in supported_filters)) or "None"
            unknown_str = ", ".join(sorted(str(k) for k in unknown_keys))
            raise serializers.ValidationError(
                f"Unknown filter key(s) for report '{report_type_clean}': {unknown_str}. "
                f"Supported filters: {supported_str}.",
                code="UNKNOWN_FILTER",
            )

        cleaned: dict[str, Any] = {}

        # 3. Per-filter semantic validation
        # is_active
        if "is_active" in filters:
            val = filters["is_active"]
            if val is not None and val != "":
                if isinstance(val, str) and val.strip().upper() == "ALL":
                    cleaned["is_active"] = "ALL"
                elif isinstance(val, bool):
                    cleaned["is_active"] = val
                elif isinstance(val, str) and val.strip().lower() in ("true", "1", "yes"):
                    cleaned["is_active"] = True
                elif isinstance(val, str) and val.strip().lower() in ("false", "0", "no"):
                    cleaned["is_active"] = False
                elif isinstance(val, int) and not isinstance(val, bool) and val in (0, 1):
                    cleaned["is_active"] = bool(val)
                else:
                    raise serializers.ValidationError(
                        f"Invalid is_active value '{val}'. Accepted values are true, false, or 'ALL'.",
                        code="INVALID_FILTER_VALUE",
                    )

        # graduation_year
        if "graduation_year" in filters:
            val = filters["graduation_year"]
            if val is not None and val != "":
                if isinstance(val, str) and val.strip().upper() == "ALL":
                    cleaned["graduation_year"] = "ALL"
                else:
                    try:
                        val_str = str(val).strip()
                        if not val_str.isdigit() and not (val_str.startswith("-") and val_str[1:].isdigit()):
                            raise ValueError()
                        gy_int = int(val_str)
                    except (ValueError, TypeError):
                        raise serializers.ValidationError(
                            f"Invalid graduation_year '{val}'. Expected an integer between 1990 and 2100, or 'ALL'.",
                            code="INVALID_FILTER_VALUE",
                        )
                    if gy_int < 1990 or gy_int > 2100:
                        raise serializers.ValidationError(
                            f"Graduation year {gy_int} is out of allowable domain bounds (1990-2100).",
                            code="INVALID_FILTER_VALUE",
                        )
                    cleaned["graduation_year"] = gy_int

        # course_id
        if "course_id" in filters:
            val = filters["course_id"]
            if val is not None and val != "":
                if isinstance(val, str) and val.strip().upper() == "ALL":
                    cleaned["course_id"] = "ALL"
                else:
                    try:
                        cid_uuid = uuid.UUID(str(val).strip())
                    except (ValueError, TypeError, AttributeError):
                        raise serializers.ValidationError(
                            f"Invalid course_id '{val}'. Must be a valid UUID or 'ALL'.",
                            code="INVALID_COURSE_ID",
                        )
                    if not Course.objects.filter(id=cid_uuid, is_deleted=False).exists():
                        raise serializers.ValidationError(
                            f"Course with id '{val}' does not exist.",
                            code="COURSE_NOT_FOUND",
                        )
                    cleaned["course_id"] = str(cid_uuid)

        # status
        if "status" in filters:
            val = filters["status"]
            if val is not None and val != "":
                val_upper = str(val).strip().upper()
                valid_statuses = {"COMPLETED", "ON_TRACK", "NOT_STARTED", "ALL"}
                if val_upper not in valid_statuses:
                    raise serializers.ValidationError(
                        f"Invalid status '{val}'. Allowed values: {', '.join(sorted(valid_statuses))}.",
                        code="INVALID_FILTER_VALUE",
                    )
                cleaned["status"] = val_upper

        # risk_type
        if "risk_type" in filters:
            val = filters["risk_type"]
            if val is not None and val != "":
                val_upper = str(val).strip().upper()
                valid_risks = {
                    "LOW_ATTENDANCE",
                    "ZERO_SUBMISSIONS",
                    "HIGH_FAILURE_RATE",
                    "STALLED_PROGRESS",
                    "ALL",
                }
                if val_upper not in valid_risks:
                    raise serializers.ValidationError(
                        f"Invalid risk_type '{val}'. Allowed values: {', '.join(sorted(valid_risks))}.",
                        code="INVALID_FILTER_VALUE",
                    )
                cleaned["risk_type"] = val_upper

        # batch_code
        if "batch_code" in filters:
            val = filters["batch_code"]
            if val is not None and val != "":
                if not isinstance(val, str):
                    raise serializers.ValidationError(
                        "batch_code must be a string.", code="INVALID_FILTER_VALUE"
                    )
                val_clean = val.strip()
                if len(val_clean) > 100:
                    raise serializers.ValidationError(
                        "batch_code exceeds maximum length of 100 characters.",
                        code="FILTER_VALUE_TOO_LONG",
                    )
                if val_clean.upper() == "ALL":
                    cleaned["batch_code"] = "ALL"
                else:
                    cleaned["batch_code"] = val_clean

        # course_opted
        if "course_opted" in filters:
            val = filters["course_opted"]
            if val is not None and val != "":
                if not isinstance(val, str):
                    raise serializers.ValidationError(
                        "course_opted must be a string.", code="INVALID_FILTER_VALUE"
                    )
                val_clean = val.strip()
                if len(val_clean) > 100:
                    raise serializers.ValidationError(
                        "course_opted exceeds maximum length of 100 characters.",
                        code="FILTER_VALUE_TOO_LONG",
                    )
                if val_clean.upper() == "ALL":
                    cleaned["course_opted"] = "ALL"
                else:
                    cleaned["course_opted"] = val_clean

        # date_from and date_to
        parsed_df = None
        parsed_dt = None

        if "date_from" in filters:
            parsed_df = parse_strict_date(filters["date_from"], "date_from")
            cleaned["date_from"] = parsed_df.strftime("%Y-%m-%d")

        if "date_to" in filters:
            parsed_dt = parse_strict_date(filters["date_to"], "date_to")
            cleaned["date_to"] = parsed_dt.strftime("%Y-%m-%d")

        if parsed_df and parsed_dt:
            if parsed_df > parsed_dt:
                raise serializers.ValidationError(
                    f"date_from ({parsed_df.strftime('%Y-%m-%d')}) cannot be later than date_to ({parsed_dt.strftime('%Y-%m-%d')}).",
                    code="INVALID_DATE_RANGE",
                )
            if (parsed_dt - parsed_df).days > 1826:
                raise serializers.ValidationError(
                    "Date range cannot exceed 5 years (1826 days).",
                    code="DATE_RANGE_EXCEEDED",
                )

        return cleaned

    @classmethod
    def _build_student_roster_data(cls, tpo_user, filters: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
        qs = TPODashboardService.get_college_students_queryset(tpo_user)

        batch_code = filters.get("batch_code")
        if batch_code and str(batch_code).strip().upper() != "ALL":
            qs = qs.filter(batch_code=batch_code)

        grad_year = filters.get("graduation_year")
        if grad_year is not None and str(grad_year).strip().upper() != "ALL":
            qs = qs.filter(graduation_year=int(grad_year))

        course_opted = filters.get("course_opted")
        if course_opted and str(course_opted).strip().upper() != "ALL":
            qs = qs.filter(course_opted__icontains=course_opted)

        is_active = filters.get("is_active")
        if is_active in (True, False):
            qs = qs.filter(user__is_active=is_active)

        headers = [
            "Student ID",
            "Full Name",
            "Email",
            "Mobile Number",
            "Batch Code",
            "Branch",
            "Graduation Year",
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
                s.graduation_year or "N/A",
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
        if batch_code and str(batch_code).strip().upper() != "ALL":
            qs = qs.filter(batch_code=batch_code)

        grad_year = filters.get("graduation_year")
        if grad_year is not None and str(grad_year).strip().upper() != "ALL":
            qs = qs.filter(graduation_year=int(grad_year))

        headers = [
            "Student ID",
            "Full Name",
            "Batch Code",
            "Branch",
            "Graduation Year",
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
                s.graduation_year or "N/A",
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
        if course_id and str(course_id).strip().upper() == "ALL":
            course_id = None
        progress_data = TPOAnalyticsService.get_learning_progress(tpo_user, course_id=course_id)

        headers = [
            "Student ID",
            "Full Name",
            "Batch Code",
            "Branch",
            "Graduation Year",
            "Track Opted",
            "Completed Modules",
            "Total Applicable Modules",
            "Completion %",
            "Progression Status",
        ]

        status_filter = filters.get("status")
        rows = []
        for s in progress_data["student_progress"]:
            if status_filter and str(status_filter).strip().upper() != "ALL" and s["status"] != status_filter:
                continue
            rows.append([
                s["student_id_number"],
                s["full_name"],
                s["batch_code"],
                s["branch"],
                s.get("graduation_year") or "N/A",
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

        grad_year = filters.get("graduation_year")
        if grad_year is not None and str(grad_year).strip().upper() != "ALL":
            students_qs = students_qs.filter(graduation_year=int(grad_year))

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
            "Graduation Year",
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
                s.graduation_year or "N/A",
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
        if risk_type and str(risk_type).strip().upper() == "ALL":
            risk_type = None
        flagged_students = TPOAnalyticsService.get_students_needing_support(tpo_user, risk_type=risk_type)

        grad_year = filters.get("graduation_year")
        if grad_year is not None and str(grad_year).strip().upper() != "ALL":
            gy_int = int(grad_year)
            flagged_students = [s for s in flagged_students if s.get("graduation_year") == gy_int]

        headers = [
            "Student ID",
            "Full Name",
            "Batch Code",
            "Branch",
            "Graduation Year",
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
                s.get("graduation_year") or "N/A",
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
        cls, tpo_user, report_type: str, filters: dict[str, Any] | None = None, ip_address: str | None = None
    ) -> dict[str, Any]:
        """Generate a preview representation (column headers and first 25 sample rows)."""
        college = TPODashboardService.get_assigned_college_or_fail(tpo_user)
        report_type_clean = str(report_type).strip().upper()
        clean_filters = cls.validate_report_filters(report_type_clean, filters)

        if report_type_clean == "STUDENT_ROSTER":
            headers, rows = cls._build_student_roster_data(tpo_user, clean_filters)
        elif report_type_clean == "ATTENDANCE_COMPLIANCE":
            headers, rows = cls._build_attendance_compliance_data(tpo_user, clean_filters)
        elif report_type_clean == "LEARNING_PROGRESS":
            headers, rows = cls._build_learning_progress_data(tpo_user, clean_filters)
        elif report_type_clean == "ASSIGNMENTS_LABS":
            headers, rows = cls._build_assignments_labs_data(tpo_user, clean_filters)
        elif report_type_clean == "STUDENTS_NEEDING_SUPPORT":
            headers, rows = cls._build_students_needing_support_data(tpo_user, clean_filters)
        elif report_type_clean == "COLLEGE_SUMMARY":
            headers, rows = cls._build_college_summary_data(tpo_user, clean_filters)
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
                "filters": clean_filters,
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
        report_type_clean = str(report_type).strip().upper()
        format_clean = str(export_format).strip().upper()
        clean_filters = cls.validate_report_filters(report_type_clean, filters)

        if format_clean not in ("CSV", "JSON"):
            raise serializers.ValidationError(
                f"Unsupported format '{export_format}'. Supported formats: CSV, JSON.",
                code="INVALID_FORMAT",
            )

        if report_type_clean == "STUDENT_ROSTER":
            headers, rows = cls._build_student_roster_data(tpo_user, clean_filters)
        elif report_type_clean == "ATTENDANCE_COMPLIANCE":
            headers, rows = cls._build_attendance_compliance_data(tpo_user, clean_filters)
        elif report_type_clean == "LEARNING_PROGRESS":
            headers, rows = cls._build_learning_progress_data(tpo_user, clean_filters)
        elif report_type_clean == "ASSIGNMENTS_LABS":
            headers, rows = cls._build_assignments_labs_data(tpo_user, clean_filters)
        elif report_type_clean == "STUDENTS_NEEDING_SUPPORT":
            headers, rows = cls._build_students_needing_support_data(tpo_user, clean_filters)
        elif report_type_clean == "COLLEGE_SUMMARY":
            headers, rows = cls._build_college_summary_data(tpo_user, clean_filters)
        else:
            raise DomainException(
                detail=f"Unsupported report type '{report_type}'.",
                code="INVALID_REPORT_TYPE",
                status_code=400,
            )

        safe_filename = generate_safe_report_filename(college, report_type_clean, format_clean)

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
                "filters": clean_filters,
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
            response["Content-Disposition"] = f'attachment; filename="{safe_filename}"'
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
            response["Content-Disposition"] = f'attachment; filename="{safe_filename}"'
            return response
