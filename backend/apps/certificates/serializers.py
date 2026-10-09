"""Serializers for Badges, Achievements, and Certificates."""

from rest_framework import serializers

from apps.certificates.models import Certificate


class BadgeSummarySerializer(serializers.Serializer):
    """Serializer for badge criteria and student progress status."""

    id = serializers.CharField()
    slug = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    icon_url = serializers.CharField(allow_blank=True)
    criteria_type = serializers.CharField()
    criteria_threshold = serializers.IntegerField()
    points_reward = serializers.IntegerField()
    is_unlocked = serializers.BooleanField()
    awarded_at = serializers.DateTimeField(allow_null=True)
    progress_percentage = serializers.FloatField()


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for student earned certificates."""

    course_id = serializers.UUIDField(source="course.id")
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            "id",
            "certificate_id",
            "student_name",
            "course_id",
            "course_title",
            "title",
            "issued_at",
            "verification_hash",
            "download_url",
            "is_revoked",
        ]

    def get_download_url(self, obj) -> str:
        return f"/api/v1/students/certificates/{obj.id}/download/"


class CertificateVerificationSerializer(serializers.Serializer):
    """Serializer for public verification response."""

    is_valid = serializers.BooleanField()
    status = serializers.CharField()
    certificate_id = serializers.CharField()
    title = serializers.CharField(required=False)
    student_name = serializers.CharField(required=False)
    student_id_number = serializers.CharField(required=False)
    course_title = serializers.CharField(required=False)
    issued_at = serializers.DateTimeField(required=False)
    verification_hash = serializers.CharField(required=False)
    download_url = serializers.CharField(required=False)
    message = serializers.CharField(required=False)


class AdminCertificateSerializer(serializers.ModelSerializer):
    """Serializer for admin certificate management view."""

    student_id = serializers.UUIDField(source="student.id")
    student_id_number = serializers.CharField(source="student.student_id_number")
    course_id = serializers.UUIDField(source="course.id")
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = [
            "id",
            "certificate_id",
            "student_id",
            "student_name",
            "student_id_number",
            "course_id",
            "course_title",
            "title",
            "issued_at",
            "verification_hash",
            "is_revoked",
            "download_url",
        ]

    def get_download_url(self, obj) -> str:
        return f"/api/v1/students/certificates/{obj.id}/download/"
