"""Student serializers for Recorded Classes viewing and streaming."""

from rest_framework import serializers


class StudentRecordedCourseItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField()
    thumbnail_url = serializers.CharField()
    is_enrolled = serializers.BooleanField()
    enrollment_status = serializers.CharField()
    total_videos = serializers.IntegerField()
    preview_videos_count = serializers.IntegerField()
    completed_videos = serializers.IntegerField()
    progress_percentage = serializers.IntegerField()
    has_full_access = serializers.BooleanField()
    free_preview_unrestricted = serializers.BooleanField()


class StudentRecordedClassPlaylistItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    course_id = serializers.UUIDField()
    course_title = serializers.CharField()
    module_id = serializers.UUIDField(allow_null=True)
    module_title = serializers.CharField(allow_null=True)
    title = serializers.CharField()
    slug = serializers.CharField()
    order_index = serializers.IntegerField()
    duration_seconds = serializers.IntegerField()
    duration_formatted = serializers.CharField()
    thumbnail_url = serializers.CharField()
    is_preview = serializers.BooleanField()
    is_locked = serializers.BooleanField()
    is_completed = serializers.BooleanField()
    last_position_seconds = serializers.IntegerField()
    lock_reason = serializers.CharField(allow_null=True)
    description = serializers.CharField()
    video_source_type = serializers.CharField()
    youtube_video_id = serializers.CharField(allow_blank=True)
    youtube_url = serializers.CharField(allow_blank=True)
    video_url = serializers.CharField(allow_blank=True)
    video_file_url = serializers.CharField(allow_blank=True)
    notes = serializers.CharField(allow_blank=True)
    resources_url = serializers.CharField(allow_blank=True)


class StudentRecordedClassStreamSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    course_id = serializers.UUIDField()
    course_title = serializers.CharField()
    title = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField()
    order_index = serializers.IntegerField()
    video_source_type = serializers.CharField()
    youtube_url = serializers.CharField(allow_blank=True)
    youtube_video_id = serializers.CharField(allow_blank=True)
    video_url = serializers.CharField(allow_blank=True)
    video_file_url = serializers.CharField(allow_blank=True)
    duration_seconds = serializers.IntegerField()
    duration_formatted = serializers.CharField()
    thumbnail_url = serializers.CharField(allow_blank=True)
    is_preview = serializers.BooleanField()
    is_locked = serializers.BooleanField()
    notes = serializers.CharField(allow_blank=True)
    resources_url = serializers.CharField(allow_blank=True)
    is_completed = serializers.BooleanField()
    last_position_seconds = serializers.IntegerField()


class StudentRecordedClassProgressUpdateSerializer(serializers.Serializer):
    last_position_seconds = serializers.IntegerField(required=False, default=0, min_value=0)
    is_completed = serializers.BooleanField(required=False, allow_null=True)
