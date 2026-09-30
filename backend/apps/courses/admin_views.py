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
    CoursePublishSerializer,
)
from apps.courses.models import Course
from apps.courses.services import CourseAdminService


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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ["title", "slug", "description"]
    ordering_fields = ["order", "title", "created_at"]
    ordering = ["order", "title"]

    def get_queryset(self):
        return Course.objects.prefetch_related("modules", "enrollments").all()

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
