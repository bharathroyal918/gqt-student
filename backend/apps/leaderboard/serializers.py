"""Serializers for Leaderboard API."""

from rest_framework import serializers

from apps.students.models import StudentProfile


class PublicLeaderboardEntrySerializer(serializers.Serializer):
    """Sanitized public leaderboard entry exposing zero private info of other students."""

    rank = serializers.IntegerField()
    student_id = serializers.CharField()
    student_id_number = serializers.CharField()
    full_name = serializers.CharField()
    avatar_url = serializers.CharField(allow_blank=True, default="")
    batch_code = serializers.CharField(allow_blank=True, default="")
    total_points = serializers.FloatField()
    current_streak_days = serializers.IntegerField()
    solved_questions_count = serializers.IntegerField(default=0)
    is_current_student = serializers.BooleanField(default=False)
    is_top_3 = serializers.BooleanField(default=False)
    is_in_top_10 = serializers.BooleanField(required=False)
    total_participants = serializers.IntegerField(required=False)


class StudentLeaderboardResponseSerializer(serializers.Serializer):
    """Combined response payload for student leaderboard view."""

    top_10 = PublicLeaderboardEntrySerializer(many=True)
    current_student = PublicLeaderboardEntrySerializer()
    nearby_students = PublicLeaderboardEntrySerializer(many=True)
    total_participants = serializers.IntegerField()
    tie_breaking_rules = serializers.ListField(child=serializers.CharField())


class AdminLeaderboardSerializer(serializers.ModelSerializer):
    """Rich administrative leaderboard entry including contact details and institutional metadata."""

    email = serializers.EmailField(source="user.email", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    total_points = serializers.FloatField(read_only=True)
    solved_questions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "student_id_number",
            "full_name",
            "email",
            "batch_code",
            "total_points",
            "current_streak_days",
            "solved_questions_count",
            "is_active",
            "created_at",
        ]
