"""Serializers for Student-Facing Daily Practice Tasks."""

from rest_framework import serializers


class StudentTaskListSerializer(serializers.Serializer):
    """Sanitized student task list entry with live completion and deadline status."""

    id = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    scheduled_date = serializers.DateField(allow_null=True)
    deadline = serializers.DateTimeField(allow_null=True)
    points = serializers.FloatField()
    question_id = serializers.CharField(allow_null=True)
    question_title = serializers.CharField(allow_null=True)
    course_id = serializers.CharField(allow_null=True)
    course_title = serializers.CharField(allow_null=True)
    status = serializers.CharField()
    deadline_status = serializers.CharField()
    is_completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    score_awarded = serializers.FloatField()
    submission_notes = serializers.CharField(allow_blank=True)


class StudentTaskDetailSerializer(StudentTaskListSerializer):
    """Detailed task payload for student workspace."""
    pass


class StudentTaskCompleteSerializer(serializers.Serializer):
    """Request payload for marking a daily task completed."""

    submission_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional student solution notes or GitHub link",
    )


class StudentTaskCompletionResponseSerializer(serializers.Serializer):
    """Response payload returned when a task is completed."""

    id = serializers.CharField()
    task_id = serializers.CharField()
    student_id = serializers.CharField()
    is_completed = serializers.BooleanField()
    score_awarded = serializers.FloatField()
    completed_at = serializers.DateTimeField()
    submission_notes = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
