"""Admin serializers for institutional announcements."""

from rest_framework import serializers

from apps.notifications.models import Announcement


class AnnouncementAdminSerializer(serializers.ModelSerializer):
    published_by_email = serializers.EmailField(source="published_by.email", allow_null=True)
    target_course_title = serializers.CharField(source="target_course.title", allow_null=True, read_only=True)

    class Meta:
        model = Announcement
        fields = [
            "id",
            "title",
            "content",
            "target_audience",
            "target_batch",
            "target_course",
            "target_course_title",
            "priority",
            "published_by_email",
            "is_active",
            "is_published",
            "published_at",
            "expires_at",
            "delivery_count",
            "email_sent_count",
            "created_at",
            "updated_at",
        ]


class AnnouncementAdminCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    target_audience = serializers.ChoiceField(
        choices=Announcement.TargetAudienceChoices.choices,
        default=Announcement.TargetAudienceChoices.ALL,
        required=False,
    )
    target_batch = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=""
    )
    target_course_id = serializers.UUIDField(required=False, allow_null=True)
    priority = serializers.ChoiceField(
        choices=Announcement.PriorityChoices.choices, default=Announcement.PriorityChoices.NORMAL
    )
    is_published = serializers.BooleanField(required=False, default=True)
    send_email = serializers.BooleanField(required=False, default=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)


class AnnouncementAdminUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    content = serializers.CharField(required=False)
    target_audience = serializers.ChoiceField(
        choices=Announcement.TargetAudienceChoices.choices, required=False
    )
    target_batch = serializers.CharField(max_length=50, required=False, allow_blank=True)
    target_course_id = serializers.UUIDField(required=False, allow_null=True)
    priority = serializers.ChoiceField(choices=Announcement.PriorityChoices.choices, required=False)
    is_active = serializers.BooleanField(required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
