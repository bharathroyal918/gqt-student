"""Views for Public and Student-Specific Leaderboard APIs."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import api_error, api_success
from apps.leaderboard.serializers import (
    PublicLeaderboardEntrySerializer,
    StudentLeaderboardResponseSerializer,
)
from apps.leaderboard.services import LeaderboardService
from apps.students.models import StudentProfile


class LeaderboardListView(APIView):
    """Retrieve top performers, authenticated student standing, and deterministic tie-breaking details."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Top 10 Leaderboard with Current Student Standing",
        description=(
            "Returns the Top 10 leaderboard entries with Top 3 highlighting, "
            "the authenticated student's exact ranking and surrounding nearby competitors, "
            "and active tie-breaking specification rules."
        ),
        parameters=[
            OpenApiParameter(
                name="batch_code",
                type=str,
                description="Optional batch code filter (e.g., 'BATCH-2026-A')",
                required=False,
            ),
            OpenApiParameter(
                name="course_id",
                type=str,
                description="Optional course UUID filter",
                required=False,
            ),
        ],
        responses={200: StudentLeaderboardResponseSerializer},
        tags=["Leaderboard"],
    )
    def get(self, request):
        batch_code = request.query_params.get("batch_code")
        course_id = request.query_params.get("course_id")

        student_profile = getattr(request.user, "student_profile", None)
        if (
            not student_profile
            and hasattr(request.user, "is_student")
            and request.user.is_student
        ):
            student_profile = StudentProfile.objects.filter(user=request.user).first()

        if student_profile:
            data = LeaderboardService.get_full_leaderboard_for_student(
                student=student_profile,
                batch_code=batch_code,
                course_id=course_id,
            )
        else:
            # Fallback for staff/admin browsing without a student profile
            top_10 = LeaderboardService.get_top_performers(
                limit=10, batch_code=batch_code, course_id=course_id
            )
            base_qs = LeaderboardService.get_base_queryset(
                batch_code=batch_code, course_id=course_id
            )
            data = {
                "top_10": top_10,
                "current_student": None,
                "nearby_students": [],
                "total_participants": base_qs.count(),
                "tie_breaking_rules": [
                    "1. Total Points (Highest score first)",
                    "2. Solved Challenges Count (More problems solved first)",
                    "3. Continuous Streak Days (Higher active streak first)",
                    "4. Registration Date (Earlier account registration first)",
                ],
            }

        return api_success(
            data=data,
            message="Leaderboard data retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class LeaderboardMeView(APIView):
    """Retrieve authenticated student's exact standing, rank, points, and streak."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Authenticated Student Rank & Standing",
        description="Returns the exact ranking and performance telemetry of the authenticated student.",
        parameters=[
            OpenApiParameter(
                name="batch_code",
                type=str,
                description="Optional batch code filter",
                required=False,
            ),
            OpenApiParameter(
                name="course_id",
                type=str,
                description="Optional course UUID filter",
                required=False,
            ),
        ],
        responses={200: PublicLeaderboardEntrySerializer},
        tags=["Leaderboard"],
    )
    def get(self, request):
        student_profile = getattr(request.user, "student_profile", None)
        if not student_profile:
            student_profile = StudentProfile.objects.filter(user=request.user).first()

        if not student_profile:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required to calculate student rank.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        batch_code = request.query_params.get("batch_code")
        course_id = request.query_params.get("course_id")

        standing = LeaderboardService.calculate_exact_student_rank(
            student=student_profile,
            batch_code=batch_code,
            course_id=course_id,
        )

        return api_success(
            data=standing,
            message="Student rank retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )
