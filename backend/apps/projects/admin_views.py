"""Admin views for capstone project management and submission review/grading."""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.views import APIView

from apps.common.permissions import IsAdmin
from apps.common.responses import api_success
from apps.common.utils import get_client_ip
from apps.projects.admin_serializers import (
    ProjectAdminCreateSerializer,
    ProjectAdminSerializer,
    ProjectAdminUpdateSerializer,
    ProjectFileAdminSerializer,
    ProjectReviewSerializer,
    ProjectSubmissionAdminDetailSerializer,
    ProjectSubmissionAdminListSerializer,
)
from apps.projects.models import Project, ProjectSubmission
from apps.projects.services import ProjectAdminService


class ProjectFilter(django_filters.FilterSet):
    course_id = django_filters.UUIDFilter(field_name="course__id")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Project
        fields = ["course_id", "is_active"]


class ProjectSubmissionFilter(django_filters.FilterSet):
    project_id = django_filters.UUIDFilter(field_name="project__id")
    student_id = django_filters.UUIDFilter(field_name="student__id")
    status = django_filters.ChoiceFilter(choices=ProjectSubmission.SubmissionStatus.choices)

    class Meta:
        model = ProjectSubmission
        fields = ["project_id", "student_id", "status"]


class ProjectAdminListCreateView(generics.ListCreateAPIView):
    """Admin endpoint to list capstone projects or create a new project."""

    permission_classes = [IsAdmin]
    serializer_class = ProjectAdminSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ["title", "slug", "description"]
    ordering_fields = ["due_date", "max_score", "created_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Project.objects.select_related("course").prefetch_related("submissions").all()

    @extend_schema(
        request=ProjectAdminCreateSerializer,
        responses={201: ProjectAdminSerializer},
        summary="Admin Create Capstone Project",
        tags=["Admin Project Management"],
    )
    def post(self, request, *args, **kwargs):
        serializer = ProjectAdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        course_id = str(data["course_id"]) if data.get("course_id") else None

        project = ProjectAdminService.create_project(
            admin_user=request.user,
            title=data["title"],
            description=data["description"],
            deliverables_instructions=data["deliverables_instructions"],
            course_id=course_id,
            max_score=data.get("max_score"),
            due_date=data.get("due_date"),
            is_active=data.get("is_active", True),
            slug=data.get("slug"),
            ip_address=ip_address,
        )
        return api_success(
            data=ProjectAdminSerializer(project).data,
            message="Capstone project created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class ProjectAdminDetailUpdateView(APIView):
    """Admin endpoint to retrieve or edit a capstone project."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: ProjectAdminSerializer},
        summary="Admin Retrieve Project Detail",
        tags=["Admin Project Management"],
    )
    def get(self, request, pk):
        project = ProjectAdminService.get_project(str(pk))
        return api_success(
            data=ProjectAdminSerializer(project).data,
            message="Project retrieved successfully.",
        )

    @extend_schema(
        request=ProjectAdminUpdateSerializer,
        responses={200: ProjectAdminSerializer},
        summary="Admin Update Project",
        tags=["Admin Project Management"],
    )
    def patch(self, request, pk):
        serializer = ProjectAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)
        c_id = None
        if "course_id" in data:
            c_id = str(data["course_id"]) if data["course_id"] else ""

        project = ProjectAdminService.update_project(
            project_id=str(pk),
            admin_user=request.user,
            title=data.get("title"),
            slug=data.get("slug"),
            description=data.get("description"),
            deliverables_instructions=data.get("deliverables_instructions"),
            course_id=c_id,
            max_score=data.get("max_score"),
            due_date=data.get("due_date"),
            is_active=data.get("is_active"),
            ip_address=ip_address,
        )
        return api_success(
            data=ProjectAdminSerializer(project).data,
            message="Project updated successfully.",
        )


class ProjectSubmissionAdminListView(generics.ListAPIView):
    """Admin endpoint to list all student capstone submissions with filtering."""

    permission_classes = [IsAdmin]
    serializer_class = ProjectSubmissionAdminListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectSubmissionFilter
    search_fields = ["student__full_name", "student__student_id_number", "project__title"]
    ordering_fields = ["submitted_at", "reviewed_at", "score"]
    ordering = ["-submitted_at"]

    def get_queryset(self):
        return ProjectSubmission.objects.select_related("project", "student", "reviewed_by").all()


class ProjectSubmissionAdminDetailReviewView(APIView):
    """Admin endpoint to inspect a student submission and evaluate/review/assign score."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: ProjectSubmissionAdminDetailSerializer},
        summary="Admin View Submission Detail",
        tags=["Admin Project Management"],
    )
    def get(self, request, pk):
        submission = ProjectAdminService.get_submission_detail(str(pk))
        return api_success(
            data=ProjectSubmissionAdminDetailSerializer(submission).data,
            message="Submission detail retrieved successfully.",
        )

    @extend_schema(
        request=ProjectReviewSerializer,
        responses={200: ProjectSubmissionAdminDetailSerializer},
        summary="Admin Review and Grade Project Submission",
        tags=["Admin Project Management"],
    )
    def post(self, request, pk):
        serializer = ProjectReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        submission = ProjectAdminService.review_submission(
            submission_id=str(pk),
            admin_user=request.user,
            status=data["status"],
            score=data.get("score"),
            feedback_text=data.get("feedback_text", ""),
            suggested_changes=data.get("suggested_changes", ""),
            rating=data.get("rating"),
            ip_address=ip_address,
        )
        return api_success(
            data=ProjectSubmissionAdminDetailSerializer(submission).data,
            message="Project submission reviewed successfully.",
        )


class ProjectSubmissionFilesView(APIView):
    """Admin endpoint to view uploaded project assets and download URLs."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: ProjectFileAdminSerializer(many=True)},
        summary="Admin View Submission Files",
        tags=["Admin Project Management"],
    )
    def get(self, request, pk):
        submission = ProjectAdminService.get_submission_detail(str(pk))
        return api_success(
            data=ProjectFileAdminSerializer(submission.files.all(), many=True).data,
            message="Submission files retrieved successfully.",
        )
