"""Admin views for platform analytics, executive reports, and asynchronous export jobs."""

import os
import uuid
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.views import APIView

from apps.analytics.models import ExportJob
from apps.analytics.serializers import ExportJobCreateSerializer, ExportJobSerializer
from apps.analytics.services import AnalyticsAdminService
from apps.analytics.tasks import _process_export_job_worker
from apps.common.permissions import IsAdmin
from apps.common.responses import api_error, api_success
from apps.common.utils import safe_int


class AnalyticsDashboardView(APIView):
    """Admin dashboard overview metric aggregator with caching and multi-dimensional filters."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin Analytics Dashboard",
        description="Fetch top-level KPI metrics, score distribution buckets, activity timelines, and stats.",
        parameters=[
            OpenApiParameter(name="course_id", description="Filter metrics by specific course UUID", required=False, type=str),
            OpenApiParameter(name="batch_code", description="Filter metrics by student batch code", required=False, type=str),
            OpenApiParameter(name="days", description="Timeline day span (default 7)", required=False, type=int),
        ],
        tags=["Admin Analytics & Reports"],
    )
    def get(self, request):
        course_id = request.query_params.get("course_id")
        batch_code = request.query_params.get("batch_code")
        days = safe_int(request.query_params.get("days", 7), default=7)

        data = AnalyticsAdminService.get_dashboard_analytics(
            course_id=course_id,
            batch_code=batch_code,
            days=days,
        )
        return api_success(
            data=data,
            message="Analytics dashboard metrics retrieved successfully.",
        )


class ReportPerformanceView(APIView):
    """Admin cohort/batch student performance summary report."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin Performance Report",
        parameters=[
            OpenApiParameter(name="batch_code", description="Batch filter", required=False, type=str),
            OpenApiParameter(name="start_date", description="Start date (YYYY-MM-DD)", required=False, type=str),
            OpenApiParameter(name="end_date", description="End date (YYYY-MM-DD)", required=False, type=str),
        ],
        tags=["Admin Analytics & Reports"],
    )
    def get(self, request):
        batch_code = request.query_params.get("batch_code")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        data = AnalyticsAdminService.get_performance_report(
            batch_code=batch_code,
            start_date=start_date,
            end_date=end_date,
        )
        return api_success(
            data=data,
            message="Performance report generated successfully.",
        )


class ReportCompletionView(APIView):
    """Admin course and module completion percentage report."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin Completion Report",
        parameters=[
            OpenApiParameter(name="course_id", description="Course UUID filter", required=False, type=str),
        ],
        tags=["Admin Analytics & Reports"],
    )
    def get(self, request):
        course_id = request.query_params.get("course_id")
        data = AnalyticsAdminService.get_completion_report(course_id=course_id)
        return api_success(
            data=data,
            message="Curriculum completion report generated successfully.",
        )


class ReportAssignmentView(APIView):
    """Admin coding question solve rates and execution statistics report."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin Assignment Statistics Report",
        parameters=[
            OpenApiParameter(name="module_id", description="Module UUID filter", required=False, type=str),
            OpenApiParameter(name="course_id", description="Course UUID filter", required=False, type=str),
        ],
        tags=["Admin Analytics & Reports"],
    )
    def get(self, request):
        module_id = request.query_params.get("module_id")
        course_id = request.query_params.get("course_id")
        data = AnalyticsAdminService.get_assignment_report(module_id=module_id, course_id=course_id)
        return api_success(
            data=data,
            message="Assignment statistics report generated successfully.",
        )


class ReportProjectView(APIView):
    """Admin capstone project submissions and evaluation grades report."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin Project Evaluation Report",
        parameters=[
            OpenApiParameter(name="course_id", description="Course UUID filter", required=False, type=str),
        ],
        tags=["Admin Analytics & Reports"],
    )
    def get(self, request):
        course_id = request.query_params.get("course_id")
        data = AnalyticsAdminService.get_project_report(course_id=course_id)
        return api_success(
            data=data,
            message="Project report generated successfully.",
        )


class ReportMonthlyActivityView(APIView):
    """Admin daily timeline and monthly active user activity trend report."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin Monthly Activity Trend Report",
        parameters=[
            OpenApiParameter(name="days", description="Days analyzed (default 30)", required=False, type=int),
        ],
        tags=["Admin Analytics & Reports"],
    )
    def get(self, request):
        days = safe_int(request.query_params.get("days", 30), default=30)
        data = AnalyticsAdminService.get_monthly_activity_report(days=days)
        return api_success(
            data=data,
            message="Monthly activity report generated successfully.",
        )


class ReportExportCreateView(APIView):
    """Initiate an asynchronous background report export job."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Create Report Export Job",
        request=ExportJobCreateSerializer,
        responses={202: ExportJobSerializer},
        tags=["Admin Analytics & Reports"],
    )
    def post(self, request):
        serializer = ExportJobCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Invalid export parameters.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        job = AnalyticsAdminService.create_export_job(
            user=request.user,
            report_type=serializer.validated_data["report_type"],
            export_format=serializer.validated_data.get("format", "CSV"),
            filters=serializer.validated_data.get("filters", {}),
        )

        output_serializer = ExportJobSerializer(job)
        return api_success(
            data=output_serializer.data,
            message="Export job initiated in background worker pool.",
            status_code=status.HTTP_202_ACCEPTED,
        )


class ReportExportListView(APIView):
    """List historical report export jobs and download links."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="List Report Export Jobs",
        responses={200: ExportJobSerializer(many=True)},
        tags=["Admin Analytics & Reports"],
    )
    def get(self, request):
        jobs = AnalyticsAdminService.list_export_jobs(user=request.user)
        serializer = ExportJobSerializer(jobs, many=True)
        return api_success(
            data={"jobs": serializer.data, "count": len(serializer.data)},
            message="Export jobs retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class ReportExportDetailView(APIView):
    """Retrieve status and details of a single export job."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Get Export Job Status",
        tags=["Admin Analytics & Reports"],
    )
    def get(self, request, job_id: uuid.UUID):
        try:
            job = ExportJob.objects.select_related("user").get(id=job_id)
        except ExportJob.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Export job not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = ExportJobSerializer(job)
        return api_success(
            data=serializer.data,
            message="Export job status retrieved.",
            status_code=status.HTTP_200_OK,
        )


class ReportExportDownloadView(APIView):
    """Stream generated report export document (CSV / JSON)."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Download Report Export File",
        tags=["Admin Analytics & Reports"],
    )
    def get(self, request, job_id: uuid.UUID):
        try:
            job = ExportJob.objects.select_related("user").get(id=job_id)
        except ExportJob.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Export job not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if job.status == ExportJob.JobStatus.FAILED:
            return api_error(
                code="EXPORT_FAILED",
                message=f"Export job failed: {job.error_message}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # If not finished yet, process on demand if needed
        if job.status in [ExportJob.JobStatus.PENDING, ExportJob.JobStatus.PROCESSING] or not job.file_path:
            _process_export_job_worker(str(job.id))
            job.refresh_from_db()

        if not job.file_path or not default_storage.exists(job.file_path):
            return api_error(
                code="FILE_NOT_READY",
                message="Export file is currently processing. Please try again shortly.",
                status_code=status.HTTP_202_ACCEPTED,
            )

        content_type = "application/json" if job.format == "JSON" else "text/csv"
        response = FileResponse(
            default_storage.open(job.file_path, "rb"),
            content_type=content_type,
        )
        response["Content-Disposition"] = f'attachment; filename="{job.file_name}"'
        return response
