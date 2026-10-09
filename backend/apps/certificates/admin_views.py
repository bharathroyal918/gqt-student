"""Admin views for certificate oversight and revocation."""

import uuid

from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView

from apps.certificates.serializers import AdminCertificateSerializer
from apps.certificates.services import CertificateService
from apps.common.permissions import IsAdmin
from apps.common.responses import api_error, api_success
from apps.common.utils import get_client_ip


class AdminCertificateListView(APIView):
    """Admin endpoint to list all issued certificates with search and filter capabilities."""

    permission_classes = [IsAdmin]

    @extend_schema(
        summary="Admin List Certificates",
        description="Search and filter all institutional completion certificate records.",
        parameters=[
            OpenApiParameter(
                "search", str, description="Search by student name, ID, or cert ID"
            ),
            OpenApiParameter("course_id", str, description="Filter by course UUID"),
            OpenApiParameter(
                "is_revoked", bool, description="Filter by revocation status"
            ),
        ],
        responses={200: AdminCertificateSerializer(many=True)},
        tags=["Admin Certificates"],
    )
    def get(self, request):
        search = request.query_params.get("search")
        course_id_str = request.query_params.get("course_id")
        course_id = uuid.UUID(course_id_str) if course_id_str else None

        is_revoked_param = request.query_params.get("is_revoked")
        is_revoked = None
        if is_revoked_param is not None:
            is_revoked = is_revoked_param.lower() in ["true", "1"]

        certificates = CertificateService.list_admin_certificates(
            search=search,
            course_id=course_id,
            is_revoked=is_revoked,
        )
        serializer = AdminCertificateSerializer(certificates, many=True)

        return api_success(
            data={"certificates": serializer.data, "count": len(serializer.data)},
            message="Certificates retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class AdminCertificateRevokeView(APIView):
    """Admin endpoint to revoke an issued certificate."""

    permission_classes = [IsAdmin]
    serializer_class = AdminCertificateSerializer

    @extend_schema(
        summary="Admin Revoke Certificate",
        description="Revoke an issued certificate with an institutional audit note.",
        responses={200: AdminCertificateSerializer},
        tags=["Admin Certificates"],
    )
    def post(self, request, certificate_id: uuid.UUID):
        reason = request.data.get("reason", "Administrative revocation")
        ip_address = get_client_ip(request)

        try:
            cert = CertificateService.revoke_certificate(
                certificate_id=certificate_id,
                admin_user=request.user,
                reason=reason,
                ip_address=ip_address,
            )
            serializer = AdminCertificateSerializer(cert)
            return api_success(
                data=serializer.data,
                message="Certificate successfully revoked.",
                status_code=status.HTTP_200_OK,
            )
        except (Http404, NotFound) as exc:
            return api_error(
                code="NOT_FOUND",
                message=str(exc),
                status_code=status.HTTP_404_NOT_FOUND,
            )
