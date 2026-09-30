"""Student views for notifications and institutional announcements."""

import uuid
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses import api_error, api_success
from apps.notifications.serializers import (
    NotificationSerializer,
    StudentAnnouncementSerializer,
)
from apps.notifications.services import AnnouncementAdminService, NotificationService


class StudentNotificationListView(APIView):
    """Retrieve notifications belonging to the authenticated student."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Student Notifications",
        description="Fetch chronological in-app alerts and notifications with optional filtering.",
        parameters=[
            OpenApiParameter("is_read", bool, description="Filter by read/unread status"),
            OpenApiParameter("notification_type", str, description="Filter by event type"),
        ],
        responses={200: NotificationSerializer(many=True)},
        tags=["Student Notifications"],
    )
    def get(self, request):
        is_read_param = request.query_params.get("is_read")
        is_read = None
        if is_read_param is not None:
            is_read = is_read_param.lower() in ["true", "1"]

        notif_type = request.query_params.get("notification_type")

        notifications = NotificationService.list_user_notifications(
            user=request.user,
            is_read=is_read,
            notification_type=notif_type,
        )
        serializer = NotificationSerializer(notifications, many=True)
        unread_count = NotificationService.get_unread_count(request.user)

        return api_success(
            data={
                "notifications": serializer.data,
                "count": len(serializer.data),
                "unread_count": unread_count,
            },
            message="Notifications retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentNotificationUnreadCountView(APIView):
    """Retrieve live unread notification badge counter."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get Unread Notification Count",
        description="Return current count of unread notifications for badge rendering.",
        responses={200: None},
        tags=["Student Notifications"],
    )
    def get(self, request):
        unread_count = NotificationService.get_unread_count(request.user)
        return api_success(
            data={"unread_count": unread_count},
            message="Unread count retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentNotificationMarkReadView(APIView):
    """Mark a single notification as read."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark Notification Read",
        description="Update read status of a specific user notification.",
        responses={200: NotificationSerializer},
        tags=["Student Notifications"],
    )
    def post(self, request, notification_id: uuid.UUID):
        try:
            notification = NotificationService.mark_as_read(request.user, notification_id)
            serializer = NotificationSerializer(notification)
            unread_count = NotificationService.get_unread_count(request.user)
            return api_success(
                data={"notification": serializer.data, "unread_count": unread_count},
                message="Notification marked as read.",
                status_code=status.HTTP_200_OK,
            )
        except NotFound as exc:
            return api_error(
                code="NOT_FOUND",
                message=str(exc.detail),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except PermissionDenied as exc:
            return api_error(
                code="PERMISSION_DENIED",
                message=str(exc),
                status_code=status.HTTP_403_FORBIDDEN,
            )


class StudentNotificationMarkAllReadView(APIView):
    """Mark all user notifications as read."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark All Notifications Read",
        description="Mark all unread notifications for the authenticated user as read.",
        responses={200: None},
        tags=["Student Notifications"],
    )
    def post(self, request):
        updated_count = NotificationService.mark_all_as_read(request.user)
        return api_success(
            data={"updated_count": updated_count, "unread_count": 0},
            message=f"{updated_count} notifications marked as read.",
            status_code=status.HTTP_200_OK,
        )


class StudentNotificationDeleteView(APIView):
    """Dismiss/delete a specific notification."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Delete Notification",
        description="Delete a notification belonging to the student.",
        responses={200: None},
        tags=["Student Notifications"],
    )
    def delete(self, request, notification_id: uuid.UUID):
        try:
            NotificationService.delete_notification(request.user, notification_id)
            unread_count = NotificationService.get_unread_count(request.user)
            return api_success(
                data={"unread_count": unread_count},
                message="Notification dismissed successfully.",
                status_code=status.HTTP_200_OK,
            )
        except NotFound as exc:
            return api_error(
                code="NOT_FOUND",
                message=str(exc.detail),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except PermissionDenied as exc:
            return api_error(
                code="PERMISSION_DENIED",
                message=str(exc),
                status_code=status.HTTP_403_FORBIDDEN,
            )


class StudentAnnouncementListView(APIView):
    """Retrieve active announcements targeted to the student."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Student Announcements",
        description="Fetch published platform and cohort-specific announcements.",
        responses={200: StudentAnnouncementSerializer(many=True)},
        tags=["Student Notifications"],
    )
    def get(self, request):
        announcements = AnnouncementAdminService.get_student_announcements(request.user)
        serializer = StudentAnnouncementSerializer(announcements, many=True)
        return api_success(
            data={"announcements": serializer.data, "count": len(serializer.data)},
            message="Announcements retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )
