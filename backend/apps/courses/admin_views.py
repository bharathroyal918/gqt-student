"""Admin views for course creation, updating, safe archival, and publishing."""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.views import APIView

from apps.common.permissions import IsAdmin
from apps.common.responses import api_success
from apps.common.utils import get_client_ip
from apps.courses.admin_serializers import (
    CourseAdminCreateSerializer,
    CourseAdminSerializer,
    CourseAdminUpdateSerializer,
    CourseEnrollmentAdminSerializer,
    CourseEnrollmentAllocateSerializer,
    CoursePublishSerializer,
    RecordedClassAdminCreateUpdateSerializer,
    RecordedClassAdminSerializer,
    RecordedClassesReorderSerializer,
)
from apps.courses.models import Course, CourseEnrollment, RecordedClass
from apps.courses.services import (
    CourseAdminService,
    CourseEnrollmentService,
    RecordedClassAdminService,
)


class CourseFilter(django_filters.FilterSet):
    is_published = django_filters.BooleanFilter()
    is_deleted = django_filters.BooleanFilter()

    class Meta:
        model = Course
        fields = ["is_published", "is_deleted"]


class CourseAdminListCreateView(generics.ListCreateAPIView):
    """Admin endpoint to list courses with filtering or create a new curriculum course."""

    permission_classes = [IsAdmin]
    serializer_class = CourseAdminSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = CourseFilter
    search_fields = ["title", "slug", "description"]
    ordering_fields = ["order", "title", "created_at"]
    ordering = ["order", "title"]

    def get_queryset(self):
        return Course.objects.prefetch_related(
            "modules", "enrollments", "recorded_classes"
        ).all()

    @extend_schema(
        request=CourseAdminCreateSerializer,
        responses={201: CourseAdminSerializer},
        summary="Admin Create Course",
        tags=["Admin Course Management"],
    )
    def post(self, request, *args, **kwargs):
        serializer = CourseAdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        course = CourseAdminService.create_course(
            admin_user=request.user,
            ip_address=ip_address,
            **serializer.validated_data,
        )
        return api_success(
            data=CourseAdminSerializer(course).data,
            message="Course created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class CourseAdminDetailUpdateDeleteView(APIView):
    """Admin endpoint to retrieve, edit, or safely archive a course."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: CourseAdminSerializer},
        summary="Admin Retrieve Course Detail",
        tags=["Admin Course Management"],
    )
    def get(self, request, pk):
        course = CourseAdminService.get_course(str(pk))
        return api_success(
            data=CourseAdminSerializer(course).data,
            message="Course retrieved successfully.",
        )

    @extend_schema(
        request=CourseAdminUpdateSerializer,
        responses={200: CourseAdminSerializer},
        summary="Admin Update Course",
        tags=["Admin Course Management"],
    )
    def patch(self, request, pk):
        serializer = CourseAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        course = CourseAdminService.update_course(
            course_id=str(pk),
            admin_user=request.user,
            ip_address=ip_address,
            **serializer.validated_data,
        )
        return api_success(
            data=CourseAdminSerializer(course).data,
            message="Course updated successfully.",
        )

    @extend_schema(
        responses={200: CourseAdminSerializer},
        summary="Admin Safely Archive Course",
        tags=["Admin Course Management"],
    )
    def delete(self, request, pk):
        ip_address = get_client_ip(request)
        course = CourseAdminService.archive_course(
            course_id=str(pk),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=CourseAdminSerializer(course).data,
            message="Course safely archived.",
        )


class CourseAdminPublishView(APIView):
    """Admin endpoint to publish or unpublish a course."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=CoursePublishSerializer,
        responses={200: CourseAdminSerializer},
        summary="Admin Publish/Unpublish Course",
        tags=["Admin Course Management"],
    )
    def post(self, request, pk):
        serializer = CoursePublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        course = CourseAdminService.set_publish_status(
            course_id=str(pk),
            is_published=serializer.validated_data["is_published"],
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=CourseAdminSerializer(course).data,
            message="Course publish status updated successfully.",
        )


# ==============================================================================
# RECORDED CLASSES ADMIN VIEWS
# ==============================================================================


class CourseRecordedClassAdminListCreateView(APIView):
    """Admin endpoint to list all recorded classes for a course or add a new video lecture."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: RecordedClassAdminSerializer(many=True)},
        summary="Admin List Recorded Classes for Course",
        tags=["Admin Recorded Classes"],
    )
    def get(self, request, course_id):
        classes = (
            RecordedClass.objects.filter(course_id=course_id)
            .select_related("module")
            .order_by("order_index", "created_at")
        )
        return api_success(
            data=RecordedClassAdminSerializer(classes, many=True).data,
            message="Recorded classes retrieved successfully.",
        )

    @extend_schema(
        request=RecordedClassAdminCreateUpdateSerializer,
        responses={201: RecordedClassAdminSerializer},
        summary="Admin Create/Upload Recorded Class Video",
        tags=["Admin Recorded Classes"],
    )
    def post(self, request, course_id):
        # Support both JSON payload and multipart form data for video files
        serializer = RecordedClassAdminCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        # Handle video file from request.FILES if uploaded
        video_file = request.FILES.get("video_file") or serializer.validated_data.get(
            "video_file"
        )

        data = serializer.validated_data.copy()
        data["video_file"] = video_file

        recorded_class = RecordedClassAdminService.create_recorded_class(
            admin_user=request.user,
            course_id=str(course_id),
            ip_address=ip_address,
            **data,
        )
        return api_success(
            data=RecordedClassAdminSerializer(recorded_class).data,
            message="Recorded class video created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class CourseRecordedClassAdminDetailView(APIView):
    """Admin endpoint to retrieve, edit, or delete an individual recorded class."""

    permission_classes = [IsAdmin]
    serializer_class = RecordedClassAdminSerializer

    @extend_schema(
        responses={200: RecordedClassAdminSerializer},
        summary="Admin Retrieve Recorded Class Detail",
        tags=["Admin Recorded Classes"],
    )
    def get(self, request, course_id, video_id):
        video = RecordedClassAdminService.get_recorded_class(str(video_id))
        return api_success(
            data=RecordedClassAdminSerializer(video).data,
            message="Recorded class retrieved successfully.",
        )

    @extend_schema(
        request=RecordedClassAdminCreateUpdateSerializer,
        responses={200: RecordedClassAdminSerializer},
        summary="Admin Update Recorded Class Video",
        tags=["Admin Recorded Classes"],
    )
    def patch(self, request, course_id, video_id):
        serializer = RecordedClassAdminCreateUpdateSerializer(
            data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        video_file = request.FILES.get("video_file") or serializer.validated_data.get(
            "video_file"
        )
        data = serializer.validated_data.copy()
        if video_file:
            data["video_file"] = video_file

        video = RecordedClassAdminService.update_recorded_class(
            class_id=str(video_id),
            admin_user=request.user,
            ip_address=ip_address,
            **data,
        )
        return api_success(
            data=RecordedClassAdminSerializer(video).data,
            message="Recorded class updated successfully.",
        )

    @extend_schema(
        summary="Admin Delete Recorded Class Video",
        responses={200: RecordedClassAdminSerializer},
        tags=["Admin Recorded Classes"],
    )
    def delete(self, request, course_id, video_id):
        ip_address = get_client_ip(request)
        RecordedClassAdminService.delete_recorded_class(
            class_id=str(video_id),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            message="Recorded class video deleted successfully.",
        )


class CourseRecordedClassReorderView(APIView):
    """Admin endpoint to bulk reorder recorded classes sequence."""

    permission_classes = [IsAdmin]
    serializer_class = RecordedClassesReorderSerializer

    @extend_schema(
        request=RecordedClassesReorderSerializer,
        responses={200: RecordedClassesReorderSerializer},
        summary="Admin Bulk Reorder Recorded Classes",
        tags=["Admin Recorded Classes"],
    )
    def post(self, request, course_id):
        serializer = RecordedClassesReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        RecordedClassAdminService.reorder_recorded_classes(
            course_id=str(course_id),
            order_items=serializer.validated_data["order_items"],
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            message="Recorded classes sequence updated successfully.",
        )


# ==============================================================================
# COURSE ENROLLMENT / STUDENT ALLOCATION ADMIN VIEWS
# ==============================================================================


class CourseEnrollmentAdminListView(APIView):
    """Admin endpoint to list all enrolled students for a specific course."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: CourseEnrollmentAdminSerializer(many=True)},
        summary="Admin List Enrolled Students for Course",
        tags=["Admin Course Enrollment"],
    )
    def get(self, request, course_id):
        enrollments = CourseEnrollmentService.get_course_enrollments(str(course_id))
        return api_success(
            data=CourseEnrollmentAdminSerializer(enrollments, many=True).data,
            message="Course enrollments retrieved successfully.",
        )


class CourseEnrollmentAdminAllocateView(APIView):
    """Admin endpoint to allocate / approve course enrollment for a student."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=CourseEnrollmentAllocateSerializer,
        responses={201: CourseEnrollmentAdminSerializer},
        summary="Admin Allocate Student to Course",
        tags=["Admin Course Enrollment"],
    )
    def post(self, request, course_id):
        serializer = CourseEnrollmentAllocateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        enrollment = CourseEnrollmentService.allocate_enrollment(
            admin_user=request.user,
            course_id=str(course_id),
            student_id=str(serializer.validated_data["student_id"]),
            status=serializer.validated_data.get(
                "status", CourseEnrollment.EnrollmentStatus.ACTIVE
            ),
            ip_address=ip_address,
        )
        return api_success(
            data=CourseEnrollmentAdminSerializer(enrollment).data,
            message="Student successfully allocated to course.",
            status_code=status.HTTP_201_CREATED,
        )


class CourseEnrollmentAdminRevokeView(APIView):
    """Admin endpoint to revoke / suspend course access for a student."""

    permission_classes = [IsAdmin]
    serializer_class = CourseEnrollmentAdminSerializer

    @extend_schema(
        summary="Admin Revoke Student Course Access",
        responses={200: CourseEnrollmentAdminSerializer},
        tags=["Admin Course Enrollment"],
    )
    def post(self, request, course_id, student_id):
        ip_address = get_client_ip(request)
        enrollment = CourseEnrollmentService.revoke_enrollment(
            admin_user=request.user,
            course_id=str(course_id),
            student_id=str(student_id),
            ip_address=ip_address,
        )
        return api_success(
            data=CourseEnrollmentAdminSerializer(enrollment).data,
            message="Student course enrollment revoked successfully.",
        )
