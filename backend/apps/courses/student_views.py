from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.exceptions import DomainException
from apps.common.responses import api_error, api_success
from apps.courses.services import RecordedClassStudentService
from apps.courses.student_serializers import (
    StudentRecordedClassProgressUpdateSerializer,
    StudentRecordedClassStreamSerializer,
    StudentRecordedCourseItemSerializer,
)
from apps.students.models import StudentProfile


def _get_student_profile(request):
    """Helper to retrieve active student profile or None."""
    if hasattr(request.user, "student_profile"):
        return request.user.student_profile
    return StudentProfile.objects.filter(user=request.user).first()


class StudentRecordedCoursesCatalogView(APIView):
    """Lists all available curriculum courses with recorded class counts, free preview availability, and student enrollment status."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="student_recorded_courses_list",
        responses={200: StudentRecordedCourseItemSerializer(many=True)},
        summary="Student List All Recorded Course Tracks",
        tags=["Student Recorded Classes"],
    )
    def get(self, request):
        student_profile = _get_student_profile(request)
        courses_catalog = RecordedClassStudentService.get_all_courses_catalog(
            student_profile
        )
        return api_success(
            data={"courses": courses_catalog},
            message="Recorded class courses catalog retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentRecordedCoursePlaylistView(APIView):
    """Retrieves full recorded classes playlist for a course with robust lock boundaries (First 5 free, remaining locked for non-enrolled students)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="student_recorded_course_detail",
        summary="Student Retrieve Recorded Classes Playlist for Course",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Student Recorded Classes"],
    )
    def get(self, request, course_id):
        student_profile = _get_student_profile(request)
        try:
            playlist_data = (
                RecordedClassStudentService.get_course_recorded_classes_playlist(
                    student_profile, str(course_id)
                )
            )
            return api_success(
                data=playlist_data,
                message="Course recorded classes playlist retrieved successfully.",
                status_code=status.HTTP_200_OK,
            )
        except (Http404, NotFound, ObjectDoesNotExist, DomainException) as e:
            return api_error(
                code="PLAYLIST_LOAD_FAILED",
                message=str(e),
                status_code=status.HTTP_404_NOT_FOUND,
            )


class StudentRecordedClassStreamView(APIView):
    """Fetches full video streaming source and lecture notes, strictly enforcing lock access on video 6+ for unauthorized students."""

    permission_classes = [IsAuthenticated]
    serializer_class = StudentRecordedClassStreamSerializer

    @extend_schema(
        responses={200: StudentRecordedClassStreamSerializer},
        summary="Student Stream Recorded Class Video",
        tags=["Student Recorded Classes"],
    )
    def get(self, request, course_id, video_id):
        student_profile = _get_student_profile(request)
        try:
            stream_data = RecordedClassStudentService.get_recorded_class_stream(
                student_profile, str(course_id), str(video_id)
            )
            return api_success(
                data=stream_data,
                message="Video stream authorized.",
                status_code=status.HTTP_200_OK,
            )
        except DomainException as exc:
            return api_error(
                code="COURSE_ENROLLMENT_REQUIRED",
                message=str(exc),
                status_code=status.HTTP_403_FORBIDDEN,
            )
        except (Http404, NotFound, ObjectDoesNotExist) as exc:
            return api_error(
                code="VIDEO_NOT_FOUND",
                message=str(exc),
                status_code=status.HTTP_404_NOT_FOUND,
            )


class StudentRecordedClassProgressUpdateView(APIView):
    """Records viewing position or marks video completed for student."""

    permission_classes = [IsAuthenticated]
    serializer_class = StudentRecordedClassProgressUpdateSerializer

    @extend_schema(
        request=StudentRecordedClassProgressUpdateSerializer,
        responses={200: OpenApiTypes.OBJECT},
        summary="Student Update Video Viewing Progress",
        tags=["Student Recorded Classes"],
    )
    def post(self, request, course_id, video_id):
        student_profile = _get_student_profile(request)
        if not student_profile:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="Authenticated user must possess a valid student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = StudentRecordedClassProgressUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = RecordedClassStudentService.record_video_progress(
            student_profile=student_profile,
            video_id=str(video_id),
            last_position_seconds=serializer.validated_data.get(
                "last_position_seconds", 0
            ),
            is_completed=serializer.validated_data.get("is_completed"),
        )
        return api_success(
            data=result,
            message="Progress recorded successfully.",
            status_code=status.HTTP_200_OK,
        )
