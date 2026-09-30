"""Admin views for curriculum module management, reordering, and publishing."""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.views import APIView

from apps.common.permissions import IsAdmin
from apps.common.responses import api_success
from apps.common.utils import get_client_ip
from apps.modules.admin_serializers import (
    ModuleAdminCreateSerializer,
    ModuleAdminSerializer,
    ModuleAdminUpdateSerializer,
    ModulePublishSerializer,
    ModuleReorderSerializer,
)
from apps.modules.models import Module
from apps.modules.services import ModuleAdminService


class ModuleFilter(django_filters.FilterSet):
    course_id = django_filters.UUIDFilter(field_name="course__id")
    is_published = django_filters.BooleanFilter()

    class Meta:
        model = Module
        fields = ["course_id", "is_published"]


class ModuleAdminListCreateView(generics.ListCreateAPIView):
    """Admin endpoint to list curriculum modules or create a new sequential learning unit."""

    permission_classes = [IsAdmin]
    serializer_class = ModuleAdminSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ModuleFilter
    search_fields = ["title", "slug", "summary"]
    ordering_fields = ["order_index", "title", "created_at"]
    ordering = ["order_index"]

    def get_queryset(self):
        return (
            Module.objects.select_related("course")
            .prefetch_related("prerequisites__prerequisite_module", "questions")
            .all()
        )

    @extend_schema(
        request=ModuleAdminCreateSerializer,
        responses={201: ModuleAdminSerializer},
        summary="Admin Create Curriculum Module",
        tags=["Admin Module Management"],
    )
    def post(self, request, *args, **kwargs):
        serializer = ModuleAdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        module = ModuleAdminService.create_module(
            admin_user=request.user,
            course_id=str(data["course_id"]),
            title=data["title"],
            summary=data.get("summary", ""),
            lecture_content=data.get("lecture_content", ""),
            slug=data.get("slug"),
            order_index=data.get("order_index"),
            passing_percentage=data.get("passing_percentage"),
            is_published=data.get("is_published", True),
            prerequisite_ids=[str(pid) for pid in data.get("prerequisite_ids", [])],
            ip_address=ip_address,
        )
        return api_success(
            data=ModuleAdminSerializer(module).data,
            message="Curriculum module created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class ModuleAdminDetailUpdateView(APIView):
    """Admin endpoint to retrieve or update an existing learning module."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: ModuleAdminSerializer},
        summary="Admin Retrieve Module Detail",
        tags=["Admin Module Management"],
    )
    def get(self, request, pk):
        module = ModuleAdminService.get_module(str(pk))
        return api_success(
            data=ModuleAdminSerializer(module).data,
            message="Module detail retrieved successfully.",
        )

    @extend_schema(
        request=ModuleAdminUpdateSerializer,
        responses={200: ModuleAdminSerializer},
        summary="Admin Update Module",
        tags=["Admin Module Management"],
    )
    def patch(self, request, pk):
        serializer = ModuleAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        prereqs = (
            [str(pid) for pid in data["prerequisite_ids"]] if "prerequisite_ids" in data else None
        )

        module = ModuleAdminService.update_module(
            module_id=str(pk),
            admin_user=request.user,
            title=data.get("title"),
            slug=data.get("slug"),
            order_index=data.get("order_index"),
            summary=data.get("summary"),
            lecture_content=data.get("lecture_content"),
            passing_percentage=data.get("passing_percentage"),
            is_published=data.get("is_published"),
            prerequisite_ids=prereqs,
            ip_address=ip_address,
        )
        return api_success(
            data=ModuleAdminSerializer(module).data,
            message="Module updated successfully.",
        )


class ModuleAdminReorderView(APIView):
    """Admin endpoint to atomically reorder learning modules within a course."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=ModuleReorderSerializer,
        responses={200: ModuleAdminSerializer(many=True)},
        summary="Admin Reorder Modules",
        tags=["Admin Module Management"],
    )
    def post(self, request):
        serializer = ModuleReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        updated_modules = ModuleAdminService.reorder_modules(
            course_id=str(data["course_id"]),
            order_mappings=[
                {"id": str(item["id"]), "order_index": item["order_index"]}
                for item in data["orders"]
            ],
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=ModuleAdminSerializer(updated_modules, many=True).data,
            message="Modules reordered successfully.",
        )


class ModuleAdminPublishView(APIView):
    """Admin endpoint to publish or unpublish a learning module."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=ModulePublishSerializer,
        responses={200: ModuleAdminSerializer},
        summary="Admin Publish/Unpublish Module",
        tags=["Admin Module Management"],
    )
    def post(self, request, pk):
        serializer = ModulePublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        module = ModuleAdminService.set_publish_status(
            module_id=str(pk),
            is_published=serializer.validated_data["is_published"],
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=ModuleAdminSerializer(module).data,
            message="Module publish status updated successfully.",
        )
