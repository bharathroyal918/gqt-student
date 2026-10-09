"""Student and public views for company information and contact inquiries."""

from django.core.exceptions import ValidationError
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.common.responses import api_error, api_success
from apps.common.utils import get_client_ip
from apps.contact.serializers import (
    ContactInquiryCreateSerializer,
    ContactInquiryResponseSerializer,
)
from apps.contact.services import ContactService


class CompanyInfoView(APIView):
    """Retrieve official institutional contact, support telephone, and social links."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Get Institutional Company & Support Info",
        description="Fetch verified telephone hotlines, support emails, office addresses, and social links.",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Contact & Institutional Info"],
    )
    def get(self, request):
        info = ContactService.get_company_info()
        return api_success(
            data=info,
            message="Company contact information retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class ContactInquirySubmitView(APIView):
    """Submit a support inquiry or general feedback with rate limiting and anti-spam verification."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Submit Contact Inquiry",
        description="Submit a support ticket or curriculum doubt with strict rate limiting and honeypot validation.",
        request=ContactInquiryCreateSerializer,
        responses={201: ContactInquiryResponseSerializer},
        tags=["Contact & Institutional Info"],
    )
    def post(self, request):
        serializer = ContactInquiryCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Please correct the errors in the contact form.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        client_ip = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        try:
            inquiry = ContactService.submit_inquiry(
                name=serializer.validated_data["name"],
                email=serializer.validated_data["email"],
                subject=serializer.validated_data["subject"],
                message=serializer.validated_data["message"],
                category=serializer.validated_data.get("category"),
                user=request.user if request.user.is_authenticated else None,
                ip_address=client_ip,
                user_agent=user_agent,
                honeypot=serializer.validated_data.get("website", ""),
            )
        except ValidationError as val_err:
            return api_error(
                code="SUBMISSION_BLOCKED",
                message=str(
                    val_err.message if hasattr(val_err, "message") else val_err
                ),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        output_serializer = ContactInquiryResponseSerializer(inquiry)
        return api_success(
            data=output_serializer.data,
            message="Thank you! Your inquiry has been submitted and assigned to our support staff.",
            status_code=status.HTTP_201_CREATED,
        )
