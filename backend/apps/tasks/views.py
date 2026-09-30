"""Student views for browsing, inspecting, and completing daily practice tasks."""

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import api_error, api_success
from apps.students.models import StudentProfile
from apps.tasks.serializers import (
    StudentTaskCompleteSerializer,
    StudentTaskCompletionResponseSerializer,
    StudentTaskDetailSerializer,
    StudentTaskListSerializer,
)
from apps.tasks.services import StudentTaskService


class StudentTaskListView(APIView):
    """Retrieve daily practice tasks assigned to the authenticated student with live status filtering."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Student Daily Tasks",
        description="Retrieve tasks assigned to the authenticated student, with completion & deadline status.",
        parameters=[
            OpenApiParameter(
                name="status",
                type=str,
                description="Filter by task status ('all', 'pending', 'completed', 'overdue', 'due_soon')",
                required=False,
            ),
        ],
        responses={200: StudentTaskListSerializer(many=True)},
        tags=["Student Tasks"],
    )
    def get(self, request):
        student = getattr(request.user, "student_profile", None)
        if not student:
            student = StudentProfile.objects.filter(user=request.user).first()

        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required to view daily tasks.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        status_filter = request.query_params.get("status")
        tasks = StudentTaskService.get_student_tasks(student=student, status_filter=status_filter)

        return api_success(
            data={"tasks": tasks, "count": len(tasks)},
            message="Daily tasks retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentTaskDetailView(APIView):
    """Retrieve detailed specifications and completion telemetry for an assigned task."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Task Detail",
        description="Fetch task challenge instructions, deadline, and student completion record.",
        responses={200: StudentTaskDetailSerializer},
        tags=["Student Tasks"],
    )
    def get(self, request, task_id):
        student = getattr(request.user, "student_profile", None)
        if not student:
            student = StudentProfile.objects.filter(user=request.user).first()

        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required to view task details.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        task_detail = StudentTaskService.get_student_task_detail(student=student, task_id=str(task_id))
        return api_success(
            data=task_detail,
            message="Task detail retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentTaskCompleteView(APIView):
    """Mark a daily practice task complete and award practice points."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=StudentTaskCompleteSerializer,
        responses={200: StudentTaskCompletionResponseSerializer},
        summary="Mark Task Complete",
        description="Mark a practice task as completed, submit optional notes, and claim points.",
        tags=["Student Tasks"],
    )
    def post(self, request, task_id):
        student = getattr(request.user, "student_profile", None)
        if not student:
            student = StudentProfile.objects.filter(user=request.user).first()

        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required to complete tasks.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = StudentTaskCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notes = serializer.validated_data.get("submission_notes", "")

        result = StudentTaskService.mark_task_complete(
            student=student, task_id=str(task_id), submission_notes=notes
        )

        return api_success(
            data=result,
            message="Daily task marked as completed successfully.",
            status_code=status.HTTP_200_OK,
        )
