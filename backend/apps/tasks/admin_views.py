"""Admin views for daily practice task management and completion audits."""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.views import APIView

from apps.common.permissions import IsAdmin
from apps.common.responses import api_success
from apps.common.utils import get_client_ip
from apps.tasks.admin_serializers import (
    TaskAdminCreateSerializer,
    TaskAdminDetailSerializer,
    TaskAdminListSerializer,
    TaskAdminUpdateSerializer,
    TaskCompletionAdminSerializer,
)
from apps.tasks.models import Task
from apps.tasks.services import TaskAdminService


class TaskFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter()
    batch_code = django_filters.CharFilter(lookup_expr="iexact")
    scheduled_date = django_filters.DateFilter()
    date_from = django_filters.DateFilter(
        field_name="scheduled_date", lookup_expr="gte"
    )
    date_to = django_filters.DateFilter(field_name="scheduled_date", lookup_expr="lte")

    class Meta:
        model = Task
        fields = ["is_active", "batch_code", "scheduled_date"]


class TaskAdminListCreateView(generics.ListCreateAPIView):
    """Admin endpoint to list daily practice tasks or create a new challenge."""

    permission_classes = [IsAdmin]
    serializer_class = TaskAdminListSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = TaskFilter
    search_fields = ["title", "description", "batch_code"]
    ordering_fields = ["scheduled_date", "deadline", "points", "created_at"]
    ordering = ["-scheduled_date", "-created_at"]

    def get_queryset(self):
        return (
            Task.objects.select_related("question", "course", "assigned_student")
            .prefetch_related("completions")
            .all()
        )

    @extend_schema(
        request=TaskAdminCreateSerializer,
        responses={201: TaskAdminDetailSerializer},
        summary="Admin Create Daily Task",
        tags=["Admin Task Management"],
    )
    def post(self, request, *args, **kwargs):
        serializer = TaskAdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        q_id = str(data["question_id"]) if data.get("question_id") else None
        c_id = str(data["course_id"]) if data.get("course_id") else None
        s_id = (
            str(data["assigned_student_id"])
            if data.get("assigned_student_id")
            else None
        )

        task = TaskAdminService.create_task(
            admin_user=request.user,
            title=data["title"],
            description=data["description"],
            scheduled_date=data.get("scheduled_date"),
            deadline=data.get("deadline"),
            question_id=q_id,
            points=data.get("points", 20.00),
            batch_code=data.get("batch_code"),
            course_id=c_id,
            assigned_student_id=s_id,
            is_active=data.get("is_active", True),
            ip_address=ip_address,
        )
        return api_success(
            data=TaskAdminDetailSerializer(task).data,
            message="Daily task created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class TaskAdminDetailUpdateDeleteView(APIView):
    """Admin endpoint to retrieve, edit, or delete a daily practice task."""

    permission_classes = [IsAdmin]
    serializer_class = TaskAdminDetailSerializer

    @extend_schema(
        responses={200: TaskAdminDetailSerializer},
        summary="Admin Retrieve Task Detail",
        tags=["Admin Task Management"],
    )
    def get(self, request, pk):
        task = TaskAdminService.get_task(str(pk))
        return api_success(
            data=TaskAdminDetailSerializer(task).data,
            message="Task retrieved successfully.",
        )

    @extend_schema(
        request=TaskAdminUpdateSerializer,
        responses={200: TaskAdminDetailSerializer},
        summary="Admin Update Task",
        tags=["Admin Task Management"],
    )
    def patch(self, request, pk):
        serializer = TaskAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        q_id = str(data["question_id"]) if data.get("question_id") is not None else None
        c_id = str(data["course_id"]) if data.get("course_id") is not None else None
        s_id = (
            str(data["assigned_student_id"])
            if data.get("assigned_student_id") is not None
            else None
        )

        task = TaskAdminService.update_task(
            task_id=str(pk),
            admin_user=request.user,
            title=data.get("title"),
            description=data.get("description"),
            scheduled_date=data.get("scheduled_date"),
            deadline=data.get("deadline"),
            question_id=q_id,
            points=data.get("points"),
            batch_code=data.get("batch_code"),
            course_id=c_id,
            assigned_student_id=s_id,
            is_active=data.get("is_active"),
            ip_address=ip_address,
        )
        return api_success(
            data=TaskAdminDetailSerializer(task).data,
            message="Task updated successfully.",
        )

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        summary="Admin Delete Task",
        tags=["Admin Task Management"],
    )
    def delete(self, request, pk):
        ip_address = get_client_ip(request)
        TaskAdminService.delete_task(
            task_id=str(pk),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data={},
            message="Task deleted successfully.",
        )


class TaskAdminCompletionsView(APIView):
    """Admin endpoint to view student completion records for a task."""

    permission_classes = [IsAdmin]
    serializer_class = TaskCompletionAdminSerializer

    @extend_schema(
        responses={200: TaskCompletionAdminSerializer(many=True)},
        summary="Admin View Task Completions",
        description="Retrieve all student completion submissions and timestamps for a task.",
        tags=["Admin Task Management"],
    )
    def get(self, request, pk):
        completions = TaskAdminService.get_task_completions(str(pk))
        return api_success(
            data={"completions": completions, "count": len(completions)},
            message="Task completions retrieved successfully.",
        )
