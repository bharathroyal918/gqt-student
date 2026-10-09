"""Admin views for querying and filtering the full institutional leaderboard."""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, generics

from apps.common.permissions import IsAdmin
from apps.leaderboard.serializers import AdminLeaderboardSerializer
from apps.leaderboard.services import LeaderboardService


class AdminLeaderboardListView(generics.ListAPIView):
    """Administrative endpoint to query full leaderboard with deep filtering and student information."""

    permission_classes = [IsAdmin]
    serializer_class = AdminLeaderboardSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["full_name", "student_id_number", "user__email", "batch_code"]

    def get_queryset(self):
        batch_code = self.request.query_params.get("batch_code")
        course_id = self.request.query_params.get("course_id")
        search = self.request.query_params.get("search")
        return LeaderboardService.get_admin_leaderboard_queryset(
            batch_code=batch_code,
            course_id=course_id,
            search=search,
        )

    @extend_schema(
        summary="Admin Full Leaderboard",
        description="Retrieve full ranked student leaderboard with batch, course, and search filtering.",
        parameters=[
            OpenApiParameter(
                name="batch_code",
                type=str,
                description="Filter by batch code (e.g., 'BATCH-2026-A')",
                required=False,
            ),
            OpenApiParameter(
                name="course_id",
                type=str,
                description="Filter by course UUID",
                required=False,
            ),
            OpenApiParameter(
                name="search",
                type=str,
                description="Search by name, student ID, email, or batch",
                required=False,
            ),
        ],
        tags=["Admin Leaderboard"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
