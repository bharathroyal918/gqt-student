"""Serializers for student project browsing and submission workflows."""

from rest_framework import serializers


class ProjectFileSerializer(serializers.Serializer):
    id = serializers.CharField()
    file_name = serializers.CharField()
    file_size_bytes = serializers.IntegerField()
    mime_type = serializers.CharField()
    download_url = serializers.CharField()
    uploaded_at = serializers.CharField()


class ProjectFeedbackSerializer(serializers.Serializer):
    id = serializers.CharField()
    reviewer_name = serializers.CharField()
    feedback_text = serializers.CharField()
    suggested_changes = serializers.CharField(allow_blank=True)
    rating = serializers.IntegerField(allow_null=True)
    created_at = serializers.CharField()


class StudentProjectSubmissionDetailSerializer(serializers.Serializer):
    id = serializers.CharField()
    github_repository_url = serializers.CharField(allow_blank=True)
    live_demo_url = serializers.CharField(allow_blank=True)
    notes = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    score = serializers.FloatField(allow_null=True)
    submitted_at = serializers.CharField()
    reviewed_at = serializers.CharField(allow_null=True)
    files = ProjectFileSerializer(many=True)
    feedbacks = ProjectFeedbackSerializer(many=True)


class StudentProjectListSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField()
    course_id = serializers.CharField(allow_null=True)
    course_title = serializers.CharField(allow_null=True)
    max_score = serializers.FloatField()
    due_date = serializers.CharField(allow_null=True)
    has_submitted = serializers.BooleanField()
    submission_id = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    score = serializers.FloatField(allow_null=True)
    submitted_at = serializers.CharField(allow_null=True)


class StudentProjectDetailSerializer(StudentProjectListSerializer):
    deliverables_instructions = serializers.CharField()
    submission_detail = StudentProjectSubmissionDetailSerializer(allow_null=True)


class StudentProjectSubmitSerializer(serializers.Serializer):
    github_repository_url = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Canonical GitHub repository URL (e.g. https://github.com/user/project)",
    )
    live_demo_url = serializers.URLField(
        required=False, allow_blank=True, default="", help_text="Optional live URL"
    )
    notes = serializers.CharField(
        required=False, allow_blank=True, default="", help_text="Optional student notes"
    )
