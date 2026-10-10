"""Admin serializers for TPO management and college assignment."""

from rest_framework import serializers

from apps.accounts.models import AuditLog, TPOProfile, User
from apps.students.models import College
from apps.students.tpo_serializers import TPOCollegeBriefSerializer


class AdminTPOProvisionSerializer(serializers.Serializer):
    """Payload for an Administrator to invite/provision a new TPO account."""

    email = serializers.EmailField(required=True)
    full_name = serializers.CharField(max_length=150, required=True)
    college_id = serializers.UUIDField(required=True)
    designation = serializers.CharField(
        max_length=100, required=False, default="Training & Placement Officer"
    )
    department = serializers.CharField(
        max_length=100, required=False, default="Training & Placement Cell"
    )
    phone_number = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    bio = serializers.CharField(required=False, allow_blank=True, default="")


class AdminTPOListSerializer(serializers.ModelSerializer):
    """List representation of TPO officers for Admin table."""

    email = serializers.EmailField(source="user.email", read_only=True)
    mobile_number = serializers.CharField(source="user.mobile_number", read_only=True)
    user_is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    user_onboarding_status = serializers.CharField(
        source="user.onboarding_status", read_only=True
    )
    college = TPOCollegeBriefSerializer(read_only=True)
    assigned_by_email = serializers.EmailField(
        source="assigned_by.email", read_only=True, default=None
    )

    class Meta:
        model = TPOProfile
        fields = [
            "id",
            "email",
            "mobile_number",
            "user_is_active",
            "user_onboarding_status",
            "full_name",
            "designation",
            "department",
            "phone_number",
            "is_active",
            "college",
            "assigned_by_email",
            "assigned_at",
            "created_at",
            "updated_at",
        ]


class AdminTPODetailSerializer(AdminTPOListSerializer):
    """Detailed representation of a TPO officer including audit references."""

    user_id = serializers.UUIDField(source="user.id", read_only=True)
    revoked_by_email = serializers.EmailField(
        source="revoked_by.email", read_only=True, default=None
    )

    class Meta(AdminTPOListSerializer.Meta):
        fields = AdminTPOListSerializer.Meta.fields + [
            "user_id",
            "bio",
            "avatar_url",
            "revoked_by_email",
            "revoked_at",
        ]


class AdminTPOUpdateSerializer(serializers.ModelSerializer):
    """Authorized updates to TPO profile metadata by an Administrator."""

    full_name = serializers.CharField(max_length=150, required=False)
    designation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    avatar_url = serializers.CharField(max_length=500, required=False, allow_blank=True)

    class Meta:
        model = TPOProfile
        fields = [
            "full_name",
            "designation",
            "department",
            "phone_number",
            "bio",
            "avatar_url",
        ]


class AdminTPOApproveSerializer(serializers.Serializer):
    """Optional payload to approve/activate a TPO and specify or override college."""

    college_id = serializers.UUIDField(required=False, allow_null=True)


class AdminTPOReassignCollegeSerializer(serializers.Serializer):
    """Payload to atomically reassign a TPO to another existing college."""

    college_id = serializers.UUIDField(required=True)


class AdminTPOAuditLogSerializer(serializers.ModelSerializer):
    """Audit log history serializer for TPO lifecycle events."""

    actor_email = serializers.EmailField(source="actor.email", read_only=True, default="System")

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "action",
            "actor_email",
            "ip_address",
            "payload",
            "created_at",
        ]
