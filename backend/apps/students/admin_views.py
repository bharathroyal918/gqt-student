"""Admin views for managing students, enrollments, progress, scores, and rankings."""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.views import APIView

from apps.accounts.serializers import StudentProvisionSerializer
from apps.accounts.services import StudentProvisioningService
from apps.common.permissions import IsAdmin
from apps.common.responses import api_success
from apps.common.utils import get_client_ip
from apps.students.admin_serializers import (
    AdminScanStudentQRSerializer,
    AssignCoursesSerializer,
    BulkMarkAttendanceSerializer,
    GrantAccessByEmailSerializer,
    MarkAttendanceSerializer,
    StudentAdminDetailSerializer,
    StudentAdminListSerializer,
    StudentAdminUpdateSerializer,
    StudentEnrollmentBriefSerializer,
)
from apps.students.models import StudentProfile
from apps.students.services import StudentAdminService


class StudentFilter(django_filters.FilterSet):
    batch_code = django_filters.CharFilter(lookup_expr="iexact")
    is_active = django_filters.BooleanFilter(field_name="user__is_active")
    onboarding_status = django_filters.CharFilter(field_name="user__onboarding_status")

    class Meta:
        model = StudentProfile
        fields = ["batch_code", "is_active", "onboarding_status"]


class StudentAdminListCreateView(generics.ListCreateAPIView):
    """Admin endpoint to list students or provision a new student."""

    permission_classes = [IsAdmin]
    serializer_class = StudentAdminListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = StudentFilter
    search_fields = ["full_name", "student_id_number", "user__email", "batch_code", "college_name"]
    ordering_fields = [
        "created_at",
        "total_points",
        "full_name",
        "student_id_number",
        "current_streak_days",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        return StudentProfile.objects.select_related("user").prefetch_related("enrollments").all()

    @extend_schema(
        request=StudentProvisionSerializer,
        responses={201: StudentAdminDetailSerializer},
        summary="Admin Provision Student",
        tags=["Admin Student Management"],
    )
    def post(self, request, *args, **kwargs):
        serializer = StudentProvisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        user, profile = StudentProvisioningService.provision_student(
            admin_user=request.user,
            full_name=data["full_name"],
            student_id_number=data["student_id_number"],
            batch_code=data["batch_code"],
            email=data.get("email"),
            mobile_number=data.get("mobile_number"),
            password=data.get("password"),
            college_name=data.get("college_name", ""),
            graduation_year=data.get("graduation_year"),
            onboarding_status=data.get("onboarding_status", "ACTIVE"),
            ip_address=ip_address,
        )

        return api_success(
            data=StudentAdminDetailSerializer(profile).data,
            message="Student provisioned successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class StudentAdminDetailUpdateView(APIView):
    """Admin endpoint to retrieve or update an existing student profile and account settings."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: StudentAdminDetailSerializer},
        summary="Admin Retrieve Student Detail",
        tags=["Admin Student Management"],
    )
    def get(self, request, pk):
        student = StudentAdminService.get_student_detail(str(pk))
        return api_success(
            data=StudentAdminDetailSerializer(student).data,
            message="Student detail retrieved successfully.",
        )

    @extend_schema(
        request=StudentAdminUpdateSerializer,
        responses={200: StudentAdminDetailSerializer},
        summary="Admin Edit Student Profile",
        tags=["Admin Student Management"],
    )
    def patch(self, request, pk):
        serializer = StudentAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        updated_student = StudentAdminService.update_student(
            student_id=str(pk),
            admin_user=request.user,
            ip_address=ip_address,
            **serializer.validated_data,
        )
        return api_success(
            data=StudentAdminDetailSerializer(updated_student).data,
            message="Student profile updated successfully.",
        )


class StudentAdminCoursesView(APIView):
    """Admin endpoint to enroll/assign courses to a student."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=AssignCoursesSerializer,
        responses={200: StudentEnrollmentBriefSerializer(many=True)},
        summary="Admin Assign Courses to Student",
        tags=["Admin Student Management"],
    )
    def post(self, request, pk):
        serializer = AssignCoursesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        enrollments = StudentAdminService.assign_courses(
            student_id=str(pk),
            course_ids=serializer.validated_data["course_ids"],
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=StudentEnrollmentBriefSerializer(enrollments, many=True).data,
            message="Courses assigned successfully.",
        )


class StudentAdminProgressView(APIView):
    """Admin endpoint to inspect student curriculum, module, and question progress."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin View Student Progress",
        tags=["Admin Student Management"],
    )
    def get(self, request, pk):
        progress_data = StudentAdminService.get_student_progress(str(pk))
        return api_success(
            data=progress_data,
            message="Student progress retrieved successfully.",
        )


class StudentAdminScoresView(APIView):
    """Admin endpoint to view student scoring history and breakdown."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin View Student Scores",
        tags=["Admin Student Management"],
    )
    def get(self, request, pk):
        scores_data = StudentAdminService.get_student_scores(str(pk))
        return api_success(
            data=scores_data,
            message="Student scores retrieved successfully.",
        )


class StudentAdminRankView(APIView):
    """Admin endpoint to view student global and batch ranking metrics."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin View Student Rank",
        tags=["Admin Student Management"],
    )
    def get(self, request, pk):
        rank_data = StudentAdminService.get_student_rank(str(pk))
        return api_success(
            data=rank_data,
            message="Student rank metrics retrieved successfully.",
        )


class StudentAdminGrantAccessView(APIView):
    """Admin endpoint to grant full portal and course access to a specific student."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: StudentAdminDetailSerializer},
        summary="Admin Grant Student Access",
        tags=["Admin Student Management"],
    )
    def post(self, request, pk):
        ip_address = get_client_ip(request)
        student = StudentAdminService.grant_student_access(
            student_id=str(pk), admin_user=request.user, ip_address=ip_address
        )
        return api_success(
            data=StudentAdminDetailSerializer(student).data,
            message=f"Access successfully granted for {student.full_name}.",
        )


class StudentAdminRevokeAccessView(APIView):
    """Admin endpoint to suspend/revoke portal access for a specific student."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: StudentAdminDetailSerializer},
        summary="Admin Revoke Student Access",
        tags=["Admin Student Management"],
    )
    def post(self, request, pk):
        ip_address = get_client_ip(request)
        student = StudentAdminService.revoke_student_access(
            student_id=str(pk), admin_user=request.user, ip_address=ip_address
        )
        return api_success(
            data=StudentAdminDetailSerializer(student).data,
            message=f"Access suspended for {student.full_name}.",
        )


class StudentAdminGrantAccessByEmailView(APIView):
    """Admin grants access to a student by entering their registered institutional email."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=GrantAccessByEmailSerializer,
        responses={200: StudentAdminDetailSerializer},
        summary="Admin Authorize Student by Email",
        tags=["Admin Student Management"],
    )
    def post(self, request):
        serializer = GrantAccessByEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        student = StudentAdminService.grant_access_by_email(
            email=serializer.validated_data["email"],
            course_opted=serializer.validated_data.get("course_opted", "Full Stack Software & Assessment Track"),
            batch_code=serializer.validated_data.get("batch_code", "BATCH-2026-A"),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=StudentAdminDetailSerializer(student).data,
            message=f"Access successfully authorized for email {serializer.validated_data['email']}.",
        )


class StudentAdminAttendanceView(APIView):
    """Admin retrieves student attendance records or marks a new session attendance."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin View Student Attendance",
        tags=["Admin Student Management"],
    )
    def get(self, request, pk):
        attendance_data = StudentAdminService.get_student_attendance(str(pk))
        return api_success(
            data=attendance_data,
            message="Student attendance retrieved successfully.",
        )

    @extend_schema(
        request=MarkAttendanceSerializer,
        summary="Admin Mark Student Attendance",
        tags=["Admin Student Management"],
    )
    def post(self, request, pk):
        serializer = MarkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        record = StudentAdminService.mark_attendance(
            student_id=str(pk),
            date=serializer.validated_data["date"],
            status=serializer.validated_data["status"],
            technology=serializer.validated_data.get("technology", "Full Stack Development"),
            session_title=serializer.validated_data.get("session_title", "Daily Training & Coding Lab"),
            remarks=serializer.validated_data.get("remarks", ""),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data={
                "id": str(record.id),
                "date": str(record.date),
                "technology": record.technology,
                "status": record.status,
                "session_title": record.session_title,
            },
            message="Attendance recorded successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class StudentAdminAttendanceOverviewView(APIView):
    """Admin endpoint to inspect attendance across all students with multi-dimensional filtering."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin View Attendance Overview",
        tags=["Admin Student Management"],
    )
    def get(self, request):
        batch_code = request.query_params.get("batch_code")
        technology = request.query_params.get("technology")
        date_str = request.query_params.get("date")
        status_filter = request.query_params.get("status")
        search = request.query_params.get("search")

        overview_data = StudentAdminService.get_attendance_overview(
            batch_code=batch_code,
            technology=technology,
            date_str=date_str,
            status_filter=status_filter,
            search=search,
        )
        return api_success(
            data=overview_data,
            message="Attendance overview retrieved successfully.",
        )


class StudentAdminScanQRView(APIView):
    """Admin scans student attendance QR code to record attendance instantly."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=AdminScanStudentQRSerializer,
        summary="Admin Scan Student Attendance QR",
        tags=["Admin Student Management"],
    )
    def post(self, request):
        serializer = AdminScanStudentQRSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        result = StudentAdminService.scan_student_qr(
            qr_data=serializer.validated_data["qr_data"],
            session_title=serializer.validated_data.get("session_title"),
            technology=serializer.validated_data.get("technology", "Full Stack Development"),
            date=serializer.validated_data.get("date"),
            status=serializer.validated_data.get("status", "PRESENT"),
            remarks=serializer.validated_data.get("remarks"),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=result,
            message=result["message"],
            status_code=status.HTTP_200_OK,
        )


class StudentAdminBulkAttendanceView(APIView):
    """Admin bulk marks attendance for a whole batch or multiple students."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=BulkMarkAttendanceSerializer,
        summary="Admin Bulk Mark Batch Attendance",
        tags=["Admin Student Management"],
    )
    def post(self, request):
        serializer = BulkMarkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        result = StudentAdminService.bulk_mark_attendance(
            batch_code=serializer.validated_data.get("batch_code"),
            student_ids=serializer.validated_data.get("student_ids"),
            date=serializer.validated_data.get("date"),
            technology=serializer.validated_data.get("technology", "Full Stack Development"),
            session_title=serializer.validated_data.get("session_title"),
            status=serializer.validated_data.get("status", "PRESENT"),
            remarks=serializer.validated_data.get("remarks"),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=result,
            message=result["message"],
            status_code=status.HTTP_200_OK,
        )
