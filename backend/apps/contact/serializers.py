"""Serializers for Contact Inquiries, Company Information, and Admin Ticket Resolution."""

from rest_framework import serializers

from apps.contact.models import ContactInquiry


class ContactInquiryCreateSerializer(serializers.Serializer):
    """Payload serializer for submitting contact inquiries with validation and honeypot."""

    name = serializers.CharField(
        min_length=2,
        max_length=150,
        trim_whitespace=True,
        error_messages={"min_length": "Name must be at least 2 characters long."},
    )
    email = serializers.EmailField(
        max_length=255,
        error_messages={"invalid": "Please provide a valid email address."},
    )
    subject = serializers.CharField(
        min_length=3,
        max_length=200,
        trim_whitespace=True,
        error_messages={"min_length": "Subject must be at least 3 characters long."},
    )
    category = serializers.ChoiceField(
        choices=ContactInquiry.CategoryChoices.choices,
        default=ContactInquiry.CategoryChoices.TECHNICAL_SUPPORT,
    )
    message = serializers.CharField(
        min_length=10,
        max_length=2000,
        trim_whitespace=True,
        error_messages={"min_length": "Message must be at least 10 characters long."},
    )
    # Anti-spam honeypot field: invisible to users, populated by automated scrapers/bots
    website = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        write_only=True,
    )


class ContactInquiryResponseSerializer(serializers.ModelSerializer):
    """Sanitized student-facing response serializer (does not leak private admin notes)."""

    class Meta:
        model = ContactInquiry
        fields = [
            "id",
            "name",
            "email",
            "subject",
            "category",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class ContactInquiryAdminSerializer(serializers.ModelSerializer):
    """Full administrative serializer for support staff inspection."""

    user_email = serializers.CharField(source="user.email", read_only=True)
    resolved_by_email = serializers.CharField(source="resolved_by.email", read_only=True)

    class Meta:
        model = ContactInquiry
        fields = [
            "id",
            "user",
            "user_email",
            "name",
            "email",
            "subject",
            "category",
            "message",
            "status",
            "admin_notes",
            "ip_address",
            "user_agent",
            "resolved_by_email",
            "resolved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "user_email",
            "name",
            "email",
            "subject",
            "category",
            "message",
            "ip_address",
            "user_agent",
            "resolved_by_email",
            "resolved_at",
            "created_at",
            "updated_at",
        ]


class ContactInquiryAdminUpdateSerializer(serializers.Serializer):
    """Payload serializer for admin updating inquiry ticket status and notes."""

    status = serializers.ChoiceField(choices=ContactInquiry.InquiryStatus.choices)
    admin_notes = serializers.CharField(required=False, allow_blank=True)
