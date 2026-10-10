"""TPO views for self-profile management, college dashboard, roster, and student inspection."""

import logging
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.accounts.services import AuthService
from apps.common.pagination import StandardResultsSetPagination
from apps.common.permissions import IsTPO
from apps.common.responses import api_error, api_success
from apps.common.utils import get_client_ip
from apps.students.tpo_serializers import (
    TPOAssignmentsLabsResponseSerializer,
    TPOAttendanceAnalyticsResponseSerializer,
    TPOCollegeBriefSerializer,
    TPOCollegeSummarySerializer,
    TPOLeaderboardItemSerializer,
    TPOLearningProgressResponseSerializer,
    TPOLoginSerializer,
    TPOPerformanceTrendsResponseSerializer,
    TPOProfileDetailSerializer,
    TPOProfileUpdateSerializer,
    TPORegisterSerializer,
    TPOReportExportRequestSerializer,
    TPOReportPreviewRequestSerializer,
    TPOReportPreviewResponseSerializer,
    TPOReportTypeSerializer,
    TPOStudentDetailSerializer,
    TPOStudentNeedingSupportSerializer,
    TPOStudentRosterSerializer,
)
from apps.students.tpo_reports_services import TPOReportsService
from apps.students.tpo_services import TPOAnalyticsService, TPODashboardService

logger = logging.getLogger(__name__)


class TPORegisterView(APIView):
    """Dedicated registration endpoint for Training & Placement Officers."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=TPORegisterSerializer,
        summary="TPO Portal Registration",
        tags=["TPO Portal"],
    )
    def post(self, request):
        serializer = TPORegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        user, profile = AuthService.register_tpo(
            full_name=data["full_name"],
            email=data["email"],
            password=data["password"],
            college_id=str(data["college_id"]) if data.get("college_id") else None,
            college_name=data.get("college_name", ""),
            mobile_number=data.get("mobile_number", ""),
            designation=data.get("designation", "Training & Placement Officer"),
            department=data.get("department", "Training & Placement Cell"),
            phone_number=data.get("phone_number", ""),
            bio=data.get("bio", ""),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        college_name = profile.college.name if profile.college else "Selected College"
        return api_success(
            data={
                "id": str(profile.id),
                "email": user.email,
                "full_name": profile.full_name,
                "college": {
                    "id": str(profile.college.id),
                    "name": profile.college.name,
                    "code": profile.college.code,
                }
                if profile.college
                else None,
                "status": "PENDING_APPROVAL",
            },
            message=(
                f"TPO registration submitted for {college_name}. "
                "Your account is pending administrator approval before student access is activated."
            ),
            status_code=status.HTTP_201_CREATED,
        )


class TPOLoginView(APIView):
    """Dedicated authentication endpoint for Training & Placement Officers."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=TPOLoginSerializer,
        summary="TPO Portal Login",
        tags=["TPO Portal"],
    )
    def post(self, request):
        serializer = TPOLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        _user, access_token, refresh_token, user_data = AuthService.login_as_tpo(
            email=email,
            password=password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return api_success(
            data={
                "access": access_token,
                "refresh": refresh_token,
                "user": user_data,
            },
            message="TPO authentication successful.",
            status_code=status.HTTP_200_OK,
        )


class TPOProfileMeView(APIView):
    """Retrieve or update the authenticated TPO's own profile and college assignment."""

    permission_classes = [IsTPO]

    @extend_schema(
        responses={200: TPOProfileDetailSerializer},
        summary="Get Current TPO Profile",
        tags=["TPO Portal"],
    )
    def get(self, request):
        tpo_profile = request.user.tpo_profile
        serializer = TPOProfileDetailSerializer(tpo_profile)
        return api_success(
            data=serializer.data,
            message="TPO profile retrieved successfully.",
        )

    @extend_schema(
        request=TPOProfileUpdateSerializer,
        responses={200: TPOProfileDetailSerializer},
        summary="Update Current TPO Profile",
        tags=["TPO Portal"],
    )
    def patch(self, request):
        tpo_profile = request.user.tpo_profile
        serializer = TPOProfileUpdateSerializer(
            tpo_profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Re-serialize full profile representation
        detail_serializer = TPOProfileDetailSerializer(tpo_profile)
        return api_success(
            data=detail_serializer.data,
            message="TPO profile updated successfully.",
        )


class TPOCollegeDetailView(APIView):
    """Retrieve basic details of the authenticated TPO's assigned college."""

    permission_classes = [IsTPO]

    @extend_schema(
        responses={200: TPOCollegeBriefSerializer},
        summary="Get Assigned College Details",
        tags=["TPO Portal"],
    )
    def get(self, request):
        college = AuthService.get_tpo_assigned_college(request.user)
        serializer = TPOCollegeBriefSerializer(college)
        return api_success(
            data=serializer.data,
            message="Assigned college details retrieved successfully.",
        )


class TPOCollegeSummaryView(APIView):
    """Aggregated academic and placement performance telemetry for the assigned college."""

    permission_classes = [IsTPO]

    @extend_schema(
        responses={200: TPOCollegeSummarySerializer},
        summary="Get Assigned College Dashboard Summary",
        tags=["TPO Portal"],
    )
    def get(self, request):
        summary_data = TPODashboardService.get_college_summary(request.user)
        serializer = TPOCollegeSummarySerializer(summary_data)
        return api_success(
            data=serializer.data,
            message="College dashboard summary retrieved successfully.",
        )


class TPOStudentRosterView(APIView):
    """Paginated, searchable, and filterable list of students enrolled in the assigned college."""

    permission_classes = [IsTPO]
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        parameters=[
            OpenApiParameter("search", str, description="Search by name, student ID, or email"),
            OpenApiParameter("batch_code", str, description="Filter by batch code"),
            OpenApiParameter("course_opted", str, description="Filter by track/course opted"),
            OpenApiParameter("is_active", bool, description="Filter by active status"),
            OpenApiParameter("ordering", str, description="Ordering field (e.g. -total_points, full_name)"),
        ],
        responses={200: TPOStudentRosterSerializer(many=True)},
        summary="List Enrolled Students in Assigned College",
        tags=["TPO Portal"],
    )
    def get(self, request):
        qs = TPODashboardService.get_college_students_queryset(request.user)

        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(full_name__icontains=search)
                | Q(student_id_number__icontains=search)
                | Q(user__email__icontains=search)
            )

        batch_code = request.query_params.get("batch_code", "").strip()
        if batch_code and batch_code != "ALL":
            qs = qs.filter(batch_code=batch_code)

        course_opted = request.query_params.get("course_opted", "").strip()
        if course_opted and course_opted != "ALL":
            qs = qs.filter(course_opted__icontains=course_opted)

        is_active_param = request.query_params.get("is_active")
        if is_active_param is not None and is_active_param != "" and is_active_param != "ALL":
            is_act = is_active_param.lower() in ("true", "1", "yes")
            qs = qs.filter(user__is_active=is_act)

        ordering = request.query_params.get("ordering", "-total_points").strip()
        allowed_orderings = [
            "-total_points",
            "total_points",
            "full_name",
            "-full_name",
            "student_id_number",
            "-student_id_number",
            "-attendance_percentage",
            "attendance_percentage",
            "-created_at",
            "created_at",
        ]
        if ordering in allowed_orderings:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-total_points")

        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(qs, request, view=self)
        serializer = TPOStudentRosterSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class TPOStudentDetailView(APIView):
    """Read-only detailed performance profile for a specific student in the assigned college."""

    permission_classes = [IsTPO]

    @extend_schema(
        responses={200: TPOStudentDetailSerializer},
        summary="Get Student Detail in Assigned College",
        tags=["TPO Portal"],
    )
    def get(self, request, pk):
        student_data = TPODashboardService.get_student_detail(request.user, pk)
        serializer = TPOStudentDetailSerializer(student_data)
        return api_success(
            data=serializer.data,
            message="Student details retrieved successfully.",
        )


class TPOLearningProgressView(APIView):
    """Curriculum and module progression metrics for students in the assigned college."""

    permission_classes = [IsTPO]

    @extend_schema(
        parameters=[
            OpenApiParameter("course_id", str, description="Filter by Course UUID", required=False),
        ],
        responses={200: TPOLearningProgressResponseSerializer},
        summary="Get College-Scoped Learning Progress Analytics",
        tags=["TPO Portal - Analytics"],
    )
    def get(self, request):
        course_id = request.query_params.get("course_id", "").strip() or None
        data = TPOAnalyticsService.get_learning_progress(request.user, course_id=course_id)
        serializer = TPOLearningProgressResponseSerializer(data)
        return api_success(
            data=serializer.data,
            message="Learning progress analytics retrieved successfully.",
        )


class TPOAssignmentsLabsView(APIView):
    """Coding challenge and lab submission performance metrics for the assigned college."""

    permission_classes = [IsTPO]

    @extend_schema(
        parameters=[
            OpenApiParameter("date_from", str, description="Filter submissions from YYYY-MM-DD", required=False),
            OpenApiParameter("date_to", str, description="Filter submissions to YYYY-MM-DD", required=False),
        ],
        responses={200: TPOAssignmentsLabsResponseSerializer},
        summary="Get College-Scoped Assignments & Labs Analytics",
        tags=["TPO Portal - Analytics"],
    )
    def get(self, request):
        date_from = request.query_params.get("date_from", "").strip() or None
        date_to = request.query_params.get("date_to", "").strip() or None
        data = TPOAnalyticsService.get_assignments_labs(
            request.user, date_from=date_from, date_to=date_to
        )
        serializer = TPOAssignmentsLabsResponseSerializer(data)
        return api_success(
            data=serializer.data,
            message="Assignments & Labs analytics retrieved successfully.",
        )


class TPOAttendanceAnalyticsView(APIView):
    """Institutional attendance distributions and compliance metrics for the assigned college."""

    permission_classes = [IsTPO]

    @extend_schema(
        parameters=[
            OpenApiParameter("batch_code", str, description="Filter by batch code", required=False),
        ],
        responses={200: TPOAttendanceAnalyticsResponseSerializer},
        summary="Get College-Scoped Attendance Analytics",
        tags=["TPO Portal - Analytics"],
    )
    def get(self, request):
        batch_code = request.query_params.get("batch_code", "").strip() or None
        data = TPOAnalyticsService.get_attendance_analytics(
            request.user, batch_code=batch_code
        )
        serializer = TPOAttendanceAnalyticsResponseSerializer(data)
        return api_success(
            data=serializer.data,
            message="Attendance analytics retrieved successfully.",
        )


class TPOPerformanceTrendsView(APIView):
    """Verified historical monthly score and submission trend lines."""

    permission_classes = [IsTPO]

    @extend_schema(
        responses={200: TPOPerformanceTrendsResponseSerializer},
        summary="Get College-Scoped Performance Trends",
        tags=["TPO Portal - Analytics"],
    )
    def get(self, request):
        data = TPOAnalyticsService.get_performance_trends(request.user)
        serializer = TPOPerformanceTrendsResponseSerializer(data)
        return api_success(
            data=serializer.data,
            message="Performance trends retrieved successfully.",
        )


class TPOStudentsNeedingSupportView(APIView):
    """Identifies students needing academic or attendance support with explicit criteria."""

    permission_classes = [IsTPO]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "risk_type",
                str,
                description="Filter by risk type (LOW_ATTENDANCE, ZERO_SUBMISSIONS, HIGH_FAILURE_RATE, STALLED_PROGRESS)",
                required=False,
            ),
        ],
        responses={200: TPOStudentNeedingSupportSerializer(many=True)},
        summary="Get Students Needing Academic Support",
        tags=["TPO Portal - Analytics"],
    )
    def get(self, request):
        risk_type = request.query_params.get("risk_type", "").strip() or None
        data = TPOAnalyticsService.get_students_needing_support(
            request.user, risk_type=risk_type
        )
        serializer = TPOStudentNeedingSupportSerializer(data, many=True)
        return api_success(
            data=serializer.data,
            message="Students needing support retrieved successfully.",
        )


class TPOLeaderboardView(APIView):
    """College-scoped leaderboard ranking students within the assigned institution."""

    permission_classes = [IsTPO]

    @extend_schema(
        parameters=[
            OpenApiParameter("limit", int, description="Number of students to return (max 100)", required=False),
        ],
        responses={200: TPOLeaderboardItemSerializer(many=True)},
        summary="Get College-Scoped Student Leaderboard",
        tags=["TPO Portal - Analytics"],
    )
    def get(self, request):
        limit_param = request.query_params.get("limit", "50").strip()
        try:
            limit = min(int(limit_param), 100)
        except (ValueError, TypeError):
            limit = 50

        data = TPOAnalyticsService.get_college_leaderboard(request.user, limit=limit)
        serializer = TPOLeaderboardItemSerializer(data, many=True)
        return api_success(
            data=serializer.data,
            message="College leaderboard retrieved successfully.",
        )


class TPOReportTypesListView(APIView):
    """List available report templates, supported export formats, and filter options."""

    permission_classes = [IsTPO]

    @extend_schema(
        responses={200: TPOReportTypeSerializer(many=True)},
        summary="List Available TPO Report Types",
        tags=["TPO Portal - Reports"],
    )
    def get(self, request):
        report_types = TPOReportsService.get_supported_reports()
        serializer = TPOReportTypeSerializer(report_types, many=True)
        return api_success(
            data=serializer.data,
            message="Supported report types retrieved successfully.",
        )


class TPOReportPreviewView(APIView):
    """Preview report headers and first sample records before exporting."""

    permission_classes = [IsTPO]

    @extend_schema(
        request=TPOReportPreviewRequestSerializer,
        responses={200: TPOReportPreviewResponseSerializer},
        summary="Generate TPO Report Preview",
        tags=["TPO Portal - Reports"],
    )
    def post(self, request):
        serializer = TPOReportPreviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report_type = serializer.validated_data["report_type"]
        filters = serializer.validated_data.get("filters", {})
        ip_address = get_client_ip(request)

        preview_data = TPOReportsService.generate_report_preview(
            tpo_user=request.user,
            report_type=report_type,
            filters=filters,
            ip_address=ip_address,
        )

        return api_success(
            data=preview_data,
            message=f"{preview_data['report_type']} report preview generated successfully.",
        )


class TPOReportExportView(APIView):
    """Generate and stream secure, injection-mitigated CSV or JSON export artifact."""

    permission_classes = [IsTPO]

    @extend_schema(
        request=TPOReportExportRequestSerializer,
        summary="Export College-Scoped Report (CSV/JSON)",
        tags=["TPO Portal - Reports"],
    )
    def post(self, request):
        serializer = TPOReportExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report_type = serializer.validated_data["report_type"]
        export_format = serializer.validated_data.get("format", "CSV")
        filters = serializer.validated_data.get("filters", {})
        ip_address = get_client_ip(request)

        return TPOReportsService.generate_report_export(
            tpo_user=request.user,
            report_type=report_type,
            export_format=export_format,
            filters=filters,
            ip_address=ip_address,
        )


