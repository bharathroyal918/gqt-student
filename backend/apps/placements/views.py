import os
import logging
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import IsAdmin, IsStudent
from apps.common.responses import api_error, api_success
from apps.placements.models import PlacementApplication, PlacementDrive
from apps.placements.serializers import (
    PlacementApplicationSerializer,
    PlacementDriveCreateUpdateSerializer,
    PlacementDriveSerializer,
    StudentApplyPlacementSerializer,
    UpdateApplicationStatusSerializer,
)
from apps.placements.services import PlacementService

logger = logging.getLogger(__name__)


# ==============================================================================
# ADMIN VIEWS
# ==============================================================================

class AdminPlacementDriveListCreateView(APIView):
    """Admin endpoint to list all placement drives or create a new placement drive."""

    permission_classes = [IsAdmin]

    def get(self, request):
        status_filter = request.query_params.get("status")
        work_mode = request.query_params.get("mode_of_work")
        search = request.query_params.get("search", "").strip()

        queryset = PlacementDrive.objects.all().order_by("-created_at")

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if work_mode:
            queryset = queryset.filter(mode_of_work=work_mode)
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search)
                | Q(role__icontains=search)
                | Q(company_code__icontains=search)
                | Q(skills__icontains=search)
                | Q(location__icontains=search)
            )

        serializer = PlacementDriveSerializer(queryset, many=True, context={"request": request})
        metrics = PlacementService.get_admin_metrics()

        return api_success(
            data={"drives": serializer.data, "metrics": metrics},
            message="Placement drives retrieved successfully.",
        )

    def post(self, request):
        serializer = PlacementDriveCreateUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Invalid placement drive data.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        drive = serializer.save(created_by=request.user)
        # Mirror to Supabase if configured
        PlacementService.sync_drive_to_supabase(drive)

        return api_success(
            data=PlacementDriveSerializer(drive, context={"request": request}).data,
            message="Placement drive created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class AdminPlacementDriveDetailView(APIView):
    """Admin endpoint to view, update, or delete a placement drive."""

    permission_classes = [IsAdmin]

    def get_object(self, drive_id):
        try:
            return PlacementDrive.objects.get(id=drive_id)
        except (PlacementDrive.DoesNotExist, ValueError):
            return None

    def get(self, request, drive_id):
        drive = self.get_object(drive_id)
        if not drive:
            return api_error("NOT_FOUND", "Placement drive not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = PlacementDriveSerializer(drive, context={"request": request})
        stats = PlacementService.get_drive_stats(drive)
        return api_success(
            data={"drive": serializer.data, "stats": stats},
            message="Placement drive retrieved.",
        )

    def put(self, request, drive_id):
        return self.patch(request, drive_id)

    def patch(self, request, drive_id):
        drive = self.get_object(drive_id)
        if not drive:
            return api_error("NOT_FOUND", "Placement drive not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = PlacementDriveCreateUpdateSerializer(drive, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Invalid update data.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        updated_drive = serializer.save()
        PlacementService.sync_drive_to_supabase(updated_drive)

        return api_success(
            data=PlacementDriveSerializer(updated_drive, context={"request": request}).data,
            message="Placement drive updated successfully.",
        )

    def delete(self, request, drive_id):
        drive = self.get_object(drive_id)
        if not drive:
            return api_error("NOT_FOUND", "Placement drive not found.", status_code=status.HTTP_404_NOT_FOUND)

        drive.delete()
        return api_success(message="Placement drive removed successfully.")


class AdminPlacementApplicationListView(APIView):
    """Admin endpoint to list all applications or filter by drive, status, and search."""

    permission_classes = [IsAdmin]

    def get(self, request, drive_id=None):
        queryset = PlacementApplication.objects.select_related("drive", "student", "student__user").all()

        target_drive_id = drive_id or request.query_params.get("drive_id")
        if target_drive_id and target_drive_id not in ["all", "applicants"]:
            queryset = queryset.filter(drive_id=target_drive_id)

        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(student_name__icontains=search)
                | Q(student_id_number__icontains=search)
                | Q(email__icontains=search)
                | Q(branch__icontains=search)
                | Q(college_name__icontains=search)
                | Q(skills_summary__icontains=search)
            )

        queryset = queryset.order_by("-submitted_at")
        serializer = PlacementApplicationSerializer(queryset, many=True)

        # Aggregate counts for filter tabs
        all_for_counts = PlacementApplication.objects.all()
        if target_drive_id and target_drive_id not in ["all", "applicants"]:
            all_for_counts = all_for_counts.filter(drive_id=target_drive_id)

        stats = {
            "total": all_for_counts.count(),
            "applied": all_for_counts.filter(status=PlacementApplication.ApplicationStatus.APPLIED).count(),
            "under_review": all_for_counts.filter(status=PlacementApplication.ApplicationStatus.UNDER_REVIEW).count(),
            "shortlisted": all_for_counts.filter(status=PlacementApplication.ApplicationStatus.SHORTLISTED).count(),
            "selected": all_for_counts.filter(status=PlacementApplication.ApplicationStatus.SELECTED).count(),
            "rejected": all_for_counts.filter(status=PlacementApplication.ApplicationStatus.REJECTED).count(),
        }

        return api_success(
            data={"applications": serializer.data, "stats": stats},
            message="Applications retrieved successfully.",
        )


class AdminPlacementApplicationStatusUpdateView(APIView):
    """Admin endpoint to select, reject, shortlist, or change student application status."""

    permission_classes = [IsAdmin]

    def post(self, request, application_id):
        try:
            application = PlacementApplication.objects.get(id=application_id)
        except (PlacementApplication.DoesNotExist, ValueError):
            return api_error("NOT_FOUND", "Application not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = UpdateApplicationStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Invalid status update payload.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        new_status = serializer.validated_data["status"]
        application.status = new_status
        application.reviewed_at = timezone.now()
        application.reviewed_by = request.user

        if "admin_notes" in serializer.validated_data:
            application.admin_notes = serializer.validated_data["admin_notes"]
        if "rejection_reason" in serializer.validated_data:
            application.rejection_reason = serializer.validated_data["rejection_reason"]

        application.save()

        # Sync update to Supabase
        PlacementService.sync_application_to_supabase(application)

        return api_success(
            data=PlacementApplicationSerializer(application).data,
            message=f"Application status successfully changed to {new_status}.",
        )


class AdminPlacementStatsView(APIView):
    """Admin global overview statistics for placements."""

    permission_classes = [IsAdmin]

    def get(self, request):
        metrics = PlacementService.get_admin_metrics()
        return api_success(data=metrics, message="Placement metrics retrieved.")


# ==============================================================================
# STUDENT VIEWS
# ==============================================================================

class StudentPlacementDriveListView(APIView):
    """Student endpoint to explore active / upcoming placement drives."""

    permission_classes = [IsStudent]

    def get(self, request):
        work_mode = request.query_params.get("mode_of_work")
        search = request.query_params.get("search", "").strip()

        queryset = PlacementDrive.objects.filter(is_active=True).exclude(
            status=PlacementDrive.DriveStatus.CANCELLED
        ).order_by("-created_at")

        if work_mode:
            queryset = queryset.filter(mode_of_work=work_mode)
        if search:
            queryset = queryset.filter(
                Q(company_name__icontains=search)
                | Q(role__icontains=search)
                | Q(skills__icontains=search)
                | Q(location__icontains=search)
            )

        serializer = PlacementDriveSerializer(queryset, many=True, context={"request": request})

        # Also get student's application count summary
        student_profile = getattr(request.user, "student_profile", None)
        my_apps_count = 0
        my_selected_count = 0
        my_shortlisted_count = 0

        if student_profile:
            my_apps = PlacementApplication.objects.filter(student=student_profile)
            my_apps_count = my_apps.count()
            my_selected_count = my_apps.filter(status=PlacementApplication.ApplicationStatus.SELECTED).count()
            my_shortlisted_count = my_apps.filter(status=PlacementApplication.ApplicationStatus.SHORTLISTED).count()

        return api_success(
            data={
                "drives": serializer.data,
                "summary": {
                    "total_available_drives": queryset.count(),
                    "my_applications_count": my_apps_count,
                    "my_shortlisted_count": my_shortlisted_count,
                    "my_selected_count": my_selected_count,
                },
            },
            message="Available placement drives retrieved.",
        )


class StudentPlacementDriveDetailView(APIView):
    """Student endpoint to view full details of a specific placement drive."""

    permission_classes = [IsStudent]

    def get(self, request, drive_id):
        try:
            drive = PlacementDrive.objects.get(id=drive_id, is_active=True)
        except (PlacementDrive.DoesNotExist, ValueError):
            return api_error("NOT_FOUND", "Placement drive not found.", status_code=status.HTTP_404_NOT_FOUND)

        serializer = PlacementDriveSerializer(drive, context={"request": request})
        return api_success(data=serializer.data, message="Placement drive details retrieved.")


class StudentPlacementApplyView(APIView):
    """Student endpoint to submit application for a placement drive with resume upload."""

    permission_classes = [IsStudent]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, drive_id):
        try:
            drive = PlacementDrive.objects.get(id=drive_id, is_active=True)
        except (PlacementDrive.DoesNotExist, ValueError):
            return api_error("NOT_FOUND", "Placement drive not found.", status_code=status.HTTP_404_NOT_FOUND)

        # Check drive is still accepting applications
        if drive.status in [PlacementDrive.DriveStatus.CLOSED, PlacementDrive.DriveStatus.CANCELLED]:
            return api_error(
                "DRIVE_CLOSED",
                "This placement drive is closed and no longer accepting applications.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if drive.application_deadline and timezone.now() > drive.application_deadline:
            return api_error(
                "DEADLINE_EXPIRED",
                "The application deadline for this drive has passed.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        student_profile = getattr(request.user, "student_profile", None)
        if not student_profile:
            return api_error(
                "PROFILE_NOT_FOUND",
                "Student profile is missing. Please complete your profile first.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Check if already applied
        if PlacementApplication.objects.filter(drive=drive, student=student_profile).exists():
            return api_error(
                "ALREADY_APPLIED",
                "You have already submitted an application for this placement drive.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        serializer = StudentApplyPlacementSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Please correct the application errors.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        validated = serializer.validated_data
        uploaded_resume_file = validated.get("resume_file") or request.FILES.get("resume_file")

        # Snapshot student profile and form submission data
        application = PlacementApplication.objects.create(
            drive=drive,
            student=student_profile,
            status=PlacementApplication.ApplicationStatus.APPLIED,
            student_name=student_profile.full_name or request.user.email,
            student_id_number=student_profile.student_id_number,
            email=request.user.email,
            phone_number=validated.get("phone_number") or getattr(request.user, "mobile_number", "") or "",
            college_name=validated.get("college_name") or student_profile.college_name or "GQT College of Tech",
            branch=validated.get("branch") or "Computer Science",
            graduation_year=validated.get("graduation_year") or student_profile.graduation_year or 2026,
            cgpa_or_percentage=validated.get("cgpa_or_percentage") or "",
            resume_file=uploaded_resume_file,
            resume_filename=uploaded_resume_file.name if uploaded_resume_file else "",
            resume_url=validated.get("resume_url") or "",
            portfolio_url=validated.get("portfolio_url") or "",
            github_url=validated.get("github_url") or "",
            linkedin_url=validated.get("linkedin_url") or "",
            skills_summary=validated.get("skills_summary") or "",
            cover_note=validated.get("cover_note") or "",
        )

        # Sync to Supabase Database
        PlacementService.sync_application_to_supabase(application)

        return api_success(
            data=PlacementApplicationSerializer(application).data,
            message="Application submitted successfully for this placement drive!",
            status_code=status.HTTP_201_CREATED,
        )


class StudentMyApplicationsView(APIView):
    """Student endpoint to list all drives applied by the logged-in student."""

    permission_classes = [IsStudent]

    def get(self, request):
        student_profile = getattr(request.user, "student_profile", None)
        if not student_profile:
            return api_success(data={"applications": []}, message="No student profile found.")

        queryset = (
            PlacementApplication.objects.filter(student=student_profile)
            .select_related("drive")
            .order_by("-submitted_at")
        )

        serializer = PlacementApplicationSerializer(queryset, many=True)
        return api_success(
            data={"applications": serializer.data},
            message="My placement applications retrieved.",
        )


@method_decorator(xframe_options_exempt, name="dispatch")
class PlacementResumeDownloadView(APIView):
    """Secure endpoint to view or download uploaded student resume."""

    permission_classes = [AllowAny]

    def get(self, request, application_id):
        try:
            application = PlacementApplication.objects.get(id=application_id)
        except (PlacementApplication.DoesNotExist, ValueError):
            raise Http404("Application not found.")

        # Determine download vs inline preview mode
        is_download = request.query_params.get("download") in ["1", "true", "True"]

        if application.resume_file:
            try:
                file_handle = application.resume_file.open("rb")
                file_path = application.resume_file.name
                _, file_ext = os.path.splitext(file_path)
                file_ext = file_ext.lower()

                content_type = (
                    "application/pdf"
                    if file_ext == ".pdf"
                    else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    if file_ext == ".docx"
                    else "application/msword"
                    if file_ext == ".doc"
                    else "application/octet-stream"
                )

                # Clean and ensure proper extension on filename
                raw_filename = application.resume_filename or os.path.basename(file_path)
                if not raw_filename.lower().endswith(file_ext):
                    raw_filename = f"{raw_filename}{file_ext}"

                response = FileResponse(
                    file_handle,
                    content_type=content_type,
                    as_attachment=is_download,
                    filename=raw_filename,
                )
                response["Access-Control-Expose-Headers"] = "Content-Disposition"
                return response
            except FileNotFoundError:
                raise Http404("Resume file not found on storage backend.")

        if application.resume_url:
            return HttpResponseRedirect(application.resume_url)

        raise Http404("No resume found for this application.")
