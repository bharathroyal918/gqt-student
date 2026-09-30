"""Student views for browsing projects, uploading deliverables, and inspecting review feedback."""

import os
from django.http import FileResponse, Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import api_error, api_success
from apps.common.utils import get_client_ip
from apps.projects.serializers import (
    StudentProjectDetailSerializer,
    StudentProjectListSerializer,
    StudentProjectSubmitSerializer,
)
from apps.projects.services import ProjectAdminService, StudentProjectService
from apps.students.models import StudentProfile


class StudentProjectListView(APIView):
    """Retrieve curriculum capstone projects assigned to the authenticated student."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Student Projects",
        description="Retrieve enrolled capstone and milestone projects with live submission status & marks.",
        responses={200: StudentProjectListSerializer(many=True)},
        tags=["Student Projects"],
    )
    def get(self, request):
        student = getattr(request.user, "student_profile", None)
        if not student:
            student = StudentProfile.objects.filter(user=request.user).first()

        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required to view assigned projects.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        projects = StudentProjectService.get_assigned_projects(student)
        return api_success(
            data={"projects": projects, "count": len(projects)},
            message="Student projects retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentProjectDetailView(APIView):
    """Retrieve project specifications, deliverables instructions, and submission history."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Project Detail",
        description="Fetch project instructions, due dates, uploaded files, and rubric feedback.",
        responses={200: StudentProjectDetailSerializer},
        tags=["Student Projects"],
    )
    def get(self, request, project_id):
        student = getattr(request.user, "student_profile", None)
        if not student:
            student = StudentProfile.objects.filter(user=request.user).first()

        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required to view project details.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        detail = StudentProjectService.get_project_detail(student, str(project_id))
        return api_success(
            data=detail,
            message="Project details retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentProjectSubmitView(APIView):
    """Submit project deliverables including validated GitHub repo link and uploaded assets."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        request=StudentProjectSubmitSerializer,
        summary="Submit Project Deliverables",
        description="Upload project files, validated GitHub URL, live demo link, and notes.",
        tags=["Student Projects"],
    )
    def post(self, request, project_id):
        student = getattr(request.user, "student_profile", None)
        if not student:
            student = StudentProfile.objects.filter(user=request.user).first()

        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required to submit projects.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = StudentProjectSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        uploaded_files = request.FILES.getlist("files")
        ip_address = get_client_ip(request)

        submission = StudentProjectService.submit_project(
            student=student,
            project_id=str(project_id),
            github_repository_url=data.get("github_repository_url", ""),
            live_demo_url=data.get("live_demo_url", ""),
            notes=data.get("notes", ""),
            uploaded_files=uploaded_files,
            ip_address=ip_address,
        )

        return api_success(
            data={
                "submission_id": str(submission.id),
                "project_id": str(submission.project.id),
                "status": submission.status,
                "github_repository_url": submission.github_repository_url,
                "files_count": submission.files.count(),
                "submitted_at": submission.submitted_at.isoformat(),
            },
            message="Project submitted successfully for institutional review.",
            status_code=status.HTTP_200_OK,
        )


class ProjectFileDownloadView(APIView):
    """Secure endpoint to stream uploaded project deliverables without exposing internal filesystem paths."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Download Project Deliverable",
        description="Secure authenticated download for project files.",
        tags=["Project Files"],
    )
    def get(self, request, file_id):
        project_file = ProjectAdminService.get_file_for_download(str(file_id), request.user)

        try:
            file_handle = project_file.file.open("rb")
            response = FileResponse(
                file_handle,
                content_type=project_file.mime_type or "application/octet-stream",
                as_attachment=True,
                filename=project_file.file_name,
            )
            return response
        except FileNotFoundError:
            raise Http404("Requested deliverable file was not found on storage backend.")
