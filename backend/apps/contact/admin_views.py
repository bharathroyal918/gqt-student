"""Admin views for managing student contact inquiries and support tickets."""

import uuid
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.views import APIView

from apps.common.permissions import IsAdmin
from apps.common.responses import api_error, api_success
from apps.common.utils import get_client_ip
from apps.contact.models import ContactInquiry
from apps.contact.serializers import (
    ContactInquiryAdminSerializer,
    ContactInquiryAdminUpdateSerializer,
)
from apps.contact.services import ContactService


class AdminContactInquiryListView(APIView):
    """Admin endpoint to list, filter, and search contact inquiries."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="List Contact Inquiries",
        description="Fetch all submitted inquiries with filtering by status, category, and search keyword.",
        parameters=[
            OpenApiParameter(name="status", description="Inquiry status filter", required=False, type=str),
            OpenApiParameter(name="category", description="Category filter", required=False, type=str),
            OpenApiParameter(name="search", description="Search by name, email, subject, or message", required=False, type=str),
        ],
        responses={200: ContactInquiryAdminSerializer(many=True)},
        tags=["Admin Contact & Support"],
    )
    def get(self, request):
        status_filter = request.query_params.get("status")
        category_filter = request.query_params.get("category")
        search = request.query_params.get("search")

        inquiries = ContactService.list_admin_inquiries(
            status_filter=status_filter,
            category_filter=category_filter,
            search=search,
        )
        serializer = ContactInquiryAdminSerializer(inquiries, many=True)
        return api_success(
            data={"inquiries": serializer.data, "count": len(serializer.data)},
            message="Contact inquiries retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class AdminContactInquiryDetailView(APIView):
    """Admin endpoint to view ticket details and update status/resolution notes."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Get Contact Inquiry Detail",
        responses={200: ContactInquiryAdminSerializer},
        tags=["Admin Contact & Support"],
    )
    def get(self, request, inquiry_id: uuid.UUID):
        try:
            inquiry = ContactInquiry.objects.select_related("user", "resolved_by").get(id=inquiry_id)
        except ContactInquiry.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Contact inquiry not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        serializer = ContactInquiryAdminSerializer(inquiry)
        return api_success(
            data=serializer.data,
            message="Inquiry detail retrieved.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Update Contact Inquiry Status",
        request=ContactInquiryAdminUpdateSerializer,
        responses={200: ContactInquiryAdminSerializer},
        tags=["Admin Contact & Support"],
    )
    def patch(self, request, inquiry_id: uuid.UUID):
        serializer = ContactInquiryAdminUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Invalid update payload.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        client_ip = get_client_ip(request)
        try:
            inquiry = ContactService.update_inquiry_status(
                inquiry_id=inquiry_id,
                admin_user=request.user,
                status_val=serializer.validated_data["status"],
                admin_notes=serializer.validated_data.get("admin_notes"),
                ip_address=client_ip,
            )
        except Exception as exc:
            return api_error(
                code="UPDATE_FAILED",
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        output_serializer = ContactInquiryAdminSerializer(inquiry)
        return api_success(
            data=output_serializer.data,
            message="Inquiry status updated successfully.",
            status_code=status.HTTP_200_OK,
        )
