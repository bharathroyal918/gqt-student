from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.serializers import StudentProfileNestedSerializer
from apps.common.exceptions import DomainException
from apps.common.permissions import IsOwnerOrAdmin
from apps.common.responses import api_error, api_success
from apps.modules.services import StudentModuleService
from apps.students.models import College, StudentProfile
from apps.students.serializers import (
    CollegeSerializer,
    StudentAttendanceScanSerializer,
    StudentAttendanceSummarySerializer,
    StudentModuleCompleteSerializer,
    StudentProfileUpdateSerializer,
)
from apps.students.services import StudentDashboardService


class PublicCollegeListView(APIView):
    """List all active colleges configured by administrators for student registration and profile selection."""

    permission_classes = []

    @extend_schema(
        responses={200: CollegeSerializer(many=True)},
        summary="List Active Institutional Colleges",
        tags=["Students"],
    )
    def get(self, request):
        if not College.objects.exists():
            from apps.students.seeds import seed_default_colleges

            seed_default_colleges()

        search = request.query_params.get("search", "").strip()
        queryset = College.objects.filter(is_active=True).order_by("name")
        if search:
            queryset = queryset.filter(name__icontains=search)

        serializer = CollegeSerializer(queryset, many=True)
        return api_success(
            data=serializer.data,
            message="Institutional colleges retrieved successfully.",
        )


class StudentProfileSelfUpdateView(APIView):
    """Authenticated student views or updates their own allowed profile fields (DOB, branch, college, bio, URLs, avatar).

    Email, Name, Student ID, Course Opted, and Points cannot be altered by student.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = StudentProfileUpdateSerializer

    @extend_schema(
        responses={200: StudentProfileNestedSerializer},
        summary="Retrieve Authenticated Student Profile",
        tags=["Students"],
    )
    def get(self, request):
        profile = StudentProfile.objects.filter(user=request.user).first()
        if not profile:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="User does not have an active student profile.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return api_success(
            data=StudentProfileNestedSerializer(profile).data,
            message="Student profile retrieved successfully.",
        )

    @extend_schema(
        request=StudentProfileUpdateSerializer,
        responses={200: StudentProfileNestedSerializer},
        summary="Update Allowed Student Profile Fields",
        tags=["Students"],
    )
    def patch(self, request):
        serializer = StudentProfileUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_profile = StudentDashboardService.update_student_profile(
            user=request.user,
            **serializer.validated_data,
        )

        return api_success(
            data=StudentProfileNestedSerializer(updated_profile).data,
            message="Profile details updated successfully.",
        )


class StudentAttendanceSelfView(APIView):
    """Authenticated student retrieves their attendance summary and session logs."""

    permission_classes = [IsAuthenticated]
    serializer_class = StudentAttendanceSummarySerializer

    @extend_schema(
        responses={200: StudentAttendanceSummarySerializer},
        summary="Retrieve Student Attendance Telemetry",
        tags=["Students"],
    )
    def get(self, request):
        attendance_data = StudentDashboardService.get_student_attendance(request.user)
        return api_success(
            data=attendance_data,
            message="Attendance telemetry retrieved successfully.",
        )


class StudentAttendanceScanQRView(APIView):
    """Authenticated student submits a scanned QR code to record class attendance."""

    permission_classes = [IsAuthenticated]
    serializer_class = StudentAttendanceScanSerializer

    @extend_schema(
        request=StudentAttendanceScanSerializer,
        responses={200: OpenApiTypes.OBJECT},
        summary="Scan QR Code to Mark Daily / Session Attendance",
        tags=["Students"],
    )
    def post(self, request):
        qr_data = request.data.get("qr_data", "")
        session_code = request.data.get("session_code", "")

        try:
            result = StudentDashboardService.mark_qr_attendance(
                user=request.user, qr_data=qr_data, session_code=session_code
            )
            return api_success(
                data=result,
                message=result.get("message", "Attendance recorded successfully."),
                status_code=status.HTTP_200_OK,
            )
        except DomainException as e:
            return api_error(
                code="ATTENDANCE_SCAN_ERROR",
                message=str(e),
                status_code=getattr(e, "status_code", status.HTTP_400_BAD_REQUEST),
            )


class StudentDashboardView(APIView):
    """Aggregate real-time dashboard telemetry strictly for the authenticated student.

    CRITICAL SECURITY ENFORCEMENT:
    Identity and ownership are derived exclusively from request.user.
    No student ID parameter is accepted in URLs or query strings.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        summary="Retrieve Authenticated Student Dashboard",
        tags=["Students"],
    )
    def get(self, request):
        if (
            not hasattr(request.user, "student_profile")
            and not StudentProfile.objects.filter(user=request.user).exists()
        ):
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="Authenticated user does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        dashboard_data = StudentDashboardService.get_dashboard_data(request.user)
        return api_success(
            data=dashboard_data,
            message="Student dashboard telemetry retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentLeaderboardView(APIView):
    """Retrieve global leaderboard and authenticated student's relative rank."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        summary="Retrieve Global Leaderboard with Current Student Standing",
        tags=["Students"],
    )
    def get(self, request):
        if (
            not hasattr(request.user, "student_profile")
            and not StudentProfile.objects.filter(user=request.user).exists()
        ):
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="Authenticated user does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        dashboard_data = StudentDashboardService.get_dashboard_data(request.user)
        return api_success(
            data=dashboard_data["leaderboard"],
            message="Leaderboard retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentProfileDetailView(APIView):
    """Retrieve individual student profile protected by object-level permission."""

    permission_classes = [IsOwnerOrAdmin]
    serializer_class = StudentProfileNestedSerializer

    @extend_schema(
        responses={200: StudentProfileNestedSerializer},
        summary="Retrieve Student Profile",
        tags=["Students"],
    )
    def get(self, request, pk):
        profile = get_object_or_404(
            StudentProfile.objects.select_related("user"), id=pk
        )
        self.check_object_permissions(request, profile)
        return api_success(
            data=StudentProfileNestedSerializer(profile).data,
            message="Student profile retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentCourseListView(APIView):
    """Retrieve all curriculum courses with student-specific enrollment status and progress."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="student_courses_list",
        responses={200: OpenApiTypes.OBJECT},
        summary="List Enrolled and Available Courses for Student",
        tags=["Students"],
    )
    def get(self, request):
        if (
            not hasattr(request.user, "student_profile")
            and not StudentProfile.objects.filter(user=request.user).exists()
        ):
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="Authenticated user does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        student_profile = request.user.student_profile
        courses = StudentModuleService.get_student_courses(student_profile)
        return api_success(
            data={"courses": courses},
            message="Student courses retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentCourseDetailView(APIView):
    """Retrieve course details along with the full sequential roadmap of modules and access locks."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="student_course_detail",
        responses={200: OpenApiTypes.OBJECT},
        summary="Retrieve Course Detail and Sequential Module Roadmap",
        tags=["Students"],
    )
    def get(self, request, course_id):
        if (
            not hasattr(request.user, "student_profile")
            and not StudentProfile.objects.filter(user=request.user).exists()
        ):
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="Authenticated user does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        student_profile = request.user.student_profile
        detail = StudentModuleService.get_student_course_detail(
            student_profile, str(course_id)
        )
        return api_success(
            data=detail,
            message="Course curriculum roadmap retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentModuleDetailView(APIView):
    """Fetch individual module lecture notes and assessment details with backend sequential lock enforcement."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        summary="Retrieve Sequential Learning Module Detail",
        tags=["Students"],
    )
    def get(self, request, module_id):
        if (
            not hasattr(request.user, "student_profile")
            and not StudentProfile.objects.filter(user=request.user).exists()
        ):
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="Authenticated user does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        student_profile = request.user.student_profile
        detail = StudentModuleService.get_student_module_detail(
            student_profile, str(module_id)
        )
        return api_success(
            data=detail,
            message="Module detail retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentModuleCompleteView(APIView):
    """Mark a learning module as complete, sequentially unlock the next module, and recalculate course progress."""

    permission_classes = [IsAuthenticated]
    serializer_class = StudentModuleCompleteSerializer

    @extend_schema(
        request=StudentModuleCompleteSerializer,
        responses={200: OpenApiTypes.OBJECT},
        summary="Mark Module Completed and Trigger Sequential Unlock",
        tags=["Students"],
    )
    def post(self, request, module_id):
        if (
            not hasattr(request.user, "student_profile")
            and not StudentProfile.objects.filter(user=request.user).exists()
        ):
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="Authenticated user does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        student_profile = request.user.student_profile
        score_percentage = request.data.get("score_percentage")
        result = StudentModuleService.complete_module(
            student_profile, str(module_id), score_percentage=score_percentage
        )
        return api_success(
            data=result,
            message="Module marked as completed and next sequential module unlocked.",
            status_code=status.HTTP_200_OK,
        )


class StudentActivityHeatmapView(APIView):
    """Authenticated student retrieves their LeetCode-style 365-day problem-solving activity heatmap."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        summary="Retrieve Student 365-Day Problem Solving Activity Heatmap",
        tags=["Students"],
    )
    def get(self, request):
        data = StudentDashboardService.get_student_activity_heatmap(request.user)
        return api_success(
            data=data,
            message="Activity heatmap matrix retrieved successfully.",
        )
