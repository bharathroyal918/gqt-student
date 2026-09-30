"""Asynchronous background worker tasks for large report exports and analytics pre-aggregation."""

from concurrent.futures import ThreadPoolExecutor
import csv
import io
import json
import logging
import os
import uuid
from typing import Any, Dict

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone

logger = logging.getLogger(__name__)

# Dedicated thread pool for async export processing to prevent blocking the web server
_EXPORT_WORKER_POOL = ThreadPoolExecutor(max_workers=3, thread_name_prefix="export_worker_")


def dispatch_async_export(export_job_id: str) -> None:
    """Submit export job to asynchronous thread pool worker."""
    _EXPORT_WORKER_POOL.submit(_process_export_job_worker, export_job_id)


def _process_export_job_worker(export_job_id: str) -> bool:
    """Worker task executing heavy report compilation and writing result file."""
    from apps.analytics.models import ExportJob
    from apps.analytics.services import AnalyticsAdminService

    try:
        job = ExportJob.objects.select_related("user").get(id=export_job_id)
    except ExportJob.DoesNotExist:
        logger.error("ExportJob %s does not exist.", export_job_id)
        return False

    job.status = ExportJob.JobStatus.PROCESSING
    job.save(update_fields=["status", "updated_at"])

    try:
        filters = job.filters or {}
        report_type = job.report_type
        export_format = job.format.upper()

        data: Dict[str, Any] = {}
        rows = []
        headers = []

        if report_type == ExportJob.ReportType.STUDENT_PERFORMANCE:
            data = AnalyticsAdminService.get_performance_report(
                batch_code=filters.get("batch_code"),
                start_date=filters.get("start_date"),
                end_date=filters.get("end_date"),
            )
            headers = ["Student ID", "Full Name", "Batch Code", "Total Points", "Streak Days", "Status"]
            raw_students = data.get("students", [])
            for s in raw_students:
                rows.append([
                    s.get("student_id_number", ""),
                    s.get("full_name", ""),
                    s.get("batch_code", ""),
                    s.get("total_points", 0),
                    s.get("current_streak_days", 0),
                    s.get("status", "ACTIVE"),
                ])

        elif report_type == ExportJob.ReportType.COURSE_STATISTICS:
            data = AnalyticsAdminService.get_completion_report(
                course_id=filters.get("course_id"),
            )
            headers = ["Course Title", "Active Enrollments", "Completed Enrollments", "Module Title", "Order", "Completed Students", "Completion Rate %"]
            for c in data.get("courses", []):
                for m in c.get("modules", []):
                    rows.append([
                        c.get("course_title", ""),
                        c.get("active_enrollments", 0),
                        c.get("completed_enrollments", 0),
                        m.get("module_title", ""),
                        m.get("order_index", 0),
                        m.get("completed_students", 0),
                        m.get("completion_rate", 0),
                    ])

        elif report_type == ExportJob.ReportType.ASSIGNMENT_COMPLETION:
            data = AnalyticsAdminService.get_assignment_report(
                module_id=filters.get("module_id"),
                course_id=filters.get("course_id"),
            )
            headers = ["Question Title", "Course", "Module", "Difficulty", "Points", "Total Submissions", "Accepted Submissions", "Pass Rate %", "Unique Solved"]
            for q in data.get("questions", []):
                rows.append([
                    q.get("title", ""),
                    q.get("course_title", ""),
                    q.get("module_title", ""),
                    q.get("difficulty", ""),
                    q.get("points", 0),
                    q.get("total_submissions", 0),
                    q.get("accepted_submissions", 0),
                    q.get("pass_rate", 0),
                    q.get("unique_students_solved", 0),
                ])

        elif report_type == ExportJob.ReportType.PROJECT_PERFORMANCE:
            data = AnalyticsAdminService.get_project_report(
                course_id=filters.get("course_id"),
            )
            headers = ["Project Title", "Course", "Max Score", "Total Submissions", "Approved", "Under Review", "Rejected", "Average Score"]
            for p in data.get("projects", []):
                rows.append([
                    p.get("title", ""),
                    p.get("course_title", "N/A"),
                    p.get("max_score", 0),
                    p.get("total_submissions", 0),
                    p.get("approved_submissions", 0),
                    p.get("under_review_submissions", 0),
                    p.get("rejected_submissions", 0),
                    p.get("average_score", 0),
                ])

        elif report_type == ExportJob.ReportType.MONTHLY_ACTIVITY:
            data = AnalyticsAdminService.get_monthly_activity_report(
                days=int(filters.get("days", 30))
            )
            headers = ["Date", "Submissions Count", "Active Students"]
            for t in data.get("timeline", []):
                rows.append([
                    t.get("date", ""),
                    t.get("submissions_count", 0),
                    t.get("active_students", 0),
                ])

        else:
            # Full Executive Overview
            data = AnalyticsAdminService.get_dashboard_analytics()
            headers = ["Metric", "Value"]
            rows = [
                ["Total Students", data.get("total_students", 0)],
                ["Active Students", data.get("active_students", 0)],
                ["Module Completion Rate %", data.get("module_completion_rate", 0)],
                ["Total Submissions", data.get("assignment_statistics", {}).get("total_submissions", 0)],
                ["Accepted Submissions", data.get("assignment_statistics", {}).get("accepted_submissions", 0)],
                ["Overall Acceptance Rate %", data.get("assignment_statistics", {}).get("acceptance_rate", 0)],
                ["Today Submissions", data.get("today_activity", {}).get("submissions_count", 0)],
                ["Today Active Students", data.get("today_activity", {}).get("active_students_count", 0)],
            ]

        # Generate output content
        timestamp_str = timezone.now().strftime("%Y%m%d_%H%M%S")
        if export_format == "JSON":
            file_name = f"{report_type.lower()}_{timestamp_str}.json"
            content = json.dumps({"report_type": report_type, "generated_at": timezone.now().isoformat(), "data": data, "rows": rows}, indent=2).encode("utf-8")
        else:
            file_name = f"{report_type.lower()}_{timestamp_str}.csv"
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(headers)
            writer.writerows(rows)
            content = output.getvalue().encode("utf-8")

        storage_path = f"exports/{file_name}"
        saved_path = default_storage.save(storage_path, ContentFile(content))

        job.status = ExportJob.JobStatus.COMPLETED
        job.file_name = file_name
        job.file_path = saved_path
        job.file_size_bytes = len(content)
        job.row_count = len(rows)
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "file_name", "file_path", "file_size_bytes", "row_count", "completed_at", "updated_at"])

        logger.info("ExportJob %s completed successfully (%d bytes, %d rows)", export_job_id, len(content), len(rows))
        return True

    except Exception as exc:
        logger.exception("ExportJob %s failed: %s", export_job_id, exc)
        job.status = ExportJob.JobStatus.FAILED
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        return False
