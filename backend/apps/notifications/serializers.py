"""Serializers for student notifications and announcements."""

from rest_framework import serializers

from apps.notifications.models import Announcement, Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for student notifications."""

    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "title",
            "body",
            "notification_type",
            "notification_type_display",
            "is_read",
            "read_at",
            "action_url",
            "created_at",
            "metadata",
        ]


class StudentAnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for student-visible announcements."""

    published_by_name = serializers.CharField(
        source="published_by.email", default="Administrator", read_only=True
    )

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "content",
            "priority",
            "published_by_name",
            "published_at",
            "created_at",
            "expires_at",
        ]
