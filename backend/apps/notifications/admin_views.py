"""Admin views for announcement broadcast management."""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.views import APIView

from apps.accounts.models import AuditLog
from apps.common.permissions import IsAdmin
from apps.common.responses import api_success
from apps.common.utils import get_client_ip
from apps.notifications.admin_serializers import (
    AnnouncementAdminCreateSerializer,
    AnnouncementAdminSerializer,
    AnnouncementAdminUpdateSerializer,
)
from apps.notifications.models import Announcement
from apps.notifications.services import AnnouncementAdminService


class AnnouncementFilter(django_filters.FilterSet):
    target_audience = django_filters.ChoiceFilter(choices=Announcement.TargetAudienceChoices.choices)
    target_batch = django_filters.CharFilter(lookup_expr="iexact")
    priority = django_filters.ChoiceFilter(choices=Announcement.PriorityChoices.choices)
    is_active = django_filters.BooleanFilter()
    is_published = django_filters.BooleanFilter()

    class Meta:
        model = Announcement
        fields = ["target_audience", "target_batch", "priority", "is_active", "is_published"]


class AnnouncementAdminListCreateView(generics.ListCreateAPIView):
    """Admin endpoint to list broadcasts or create a new announcement."""

    permission_classes = [IsAdmin]
    serializer_class = AnnouncementAdminSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AnnouncementFilter
    search_fields = ["title", "content", "target_batch"]
    ordering_fields = ["priority", "created_at", "expires_at", "published_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Announcement.objects.select_related("published_by", "target_course").all()

    @extend_schema(
        request=AnnouncementAdminCreateSerializer,
        responses={201: AnnouncementAdminSerializer},
        summary="Admin Create Announcement",
        tags=["Admin Announcement Management"],
    )
    def post(self, request, *args, **kwargs):
        serializer = AnnouncementAdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        announcement = AnnouncementAdminService.create_announcement(
            admin_user=request.user,
            title=data["title"],
            content=data["content"],
            target_audience=data.get("target_audience", Announcement.TargetAudienceChoices.ALL),
            target_batch=data.get("target_batch", ""),
            target_course_id=data.get("target_course_id"),
            priority=data.get("priority", "NORMAL"),
            is_published=data.get("is_published", True),
            expires_at=data.get("expires_at"),
            send_email=data.get("send_email", False),
            ip_address=ip_address,
        )
        return api_success(
            data=AnnouncementAdminSerializer(announcement).data,
            message="Announcement created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class AnnouncementAdminDetailUpdateDeleteView(APIView):
    """Admin endpoint to retrieve, edit, or deactivate an announcement."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: AnnouncementAdminSerializer},
        summary="Admin Retrieve Announcement Detail",
        tags=["Admin Announcement Management"],
    )
    def get(self, request, pk):
        announcement = AnnouncementAdminService.get_announcement(str(pk))
        return api_success(
            data=AnnouncementAdminSerializer(announcement).data,
            message="Announcement retrieved successfully.",
        )

    @extend_schema(
        request=AnnouncementAdminUpdateSerializer,
        responses={200: AnnouncementAdminSerializer},
        summary="Admin Update Announcement",
        tags=["Admin Announcement Management"],
    )
    def patch(self, request, pk):
        serializer = AnnouncementAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        announcement = AnnouncementAdminService.update_announcement(
            announcement_id=str(pk),
            admin_user=request.user,
            title=data.get("title"),
            content=data.get("content"),
            target_audience=data.get("target_audience"),
            target_batch=data.get("target_batch"),
            target_course_id=data.get("target_course_id"),
            priority=data.get("priority"),
            expires_at=data.get("expires_at"),
            is_active=data.get("is_active"),
            ip_address=ip_address,
        )
        return api_success(
            data=AnnouncementAdminSerializer(announcement).data,
            message="Announcement updated successfully.",
        )

    @extend_schema(
        summary="Admin Deactivate Announcement",
        tags=["Admin Announcement Management"],
    )
    def delete(self, request, pk):
        ip_address = get_client_ip(request)
        AnnouncementAdminService.delete_announcement(
            announcement_id=str(pk),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data={},
            message="Announcement deactivated successfully.",
        )


class AnnouncementAdminPublishView(APIView):
    """Admin endpoint to publish and fan out an existing announcement."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin Publish Announcement",
        description="Fan out in-app alerts and optional async email notifications for this announcement.",
        responses={200: AnnouncementAdminSerializer},
        tags=["Admin Announcement Management"],
    )
    def post(self, request, pk):
        send_email = request.data.get("send_email", False)
        ip_address = get_client_ip(request)
        announcement = AnnouncementAdminService.get_announcement(str(pk))

        delivery_count = AnnouncementAdminService.publish_announcement(
            announcement=announcement,
            admin_user=request.user,
            send_email=send_email,
            ip_address=ip_address,
        )
        return api_success(
            data=AnnouncementAdminSerializer(announcement).data,
            message=f"Announcement published and dispatched to {delivery_count} students.",
            status_code=status.HTTP_200_OK,
        )


class AnnouncementAdminAuditHistoryView(APIView):
    """Admin endpoint to view audit trail for an announcement."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin Announcement Audit History",
        description="Retrieve history of creation, modification, and publishing events.",
        tags=["Admin Announcement Management"],
    )
    def get(self, request, pk):
        logs = AuditLog.objects.filter(
            target_model="Announcement", target_id=str(pk)
        ).select_related("actor").order_by("-created_at")

        log_data = [
            {
                "id": str(log.id),
                "action": log.action,
                "actor_email": log.actor.email if log.actor else "System",
                "ip_address": log.ip_address,
                "payload": log.payload,
                "created_at": log.created_at,
            }
            for log in logs
        ]
        return api_success(
            data={"audit_logs": log_data, "count": len(log_data)},
            message="Audit history retrieved successfully.",
        )
