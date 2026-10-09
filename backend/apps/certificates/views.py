"""Student and Public views for Badges, Achievements, and Certificate verification."""

import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.http import FileResponse, Http404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.certificates.models import Certificate
from apps.certificates.serializers import (
    BadgeSummarySerializer,
    CertificateSerializer,
    CertificateVerificationSerializer,
)
from apps.certificates.services import AchievementService, CertificateService
from apps.certificates.tasks import _generate_certificate_pdf_worker
from apps.common.responses import api_error, api_success
from apps.students.models import StudentProfile


def _get_student(request):
    student = getattr(request.user, "student_profile", None)
    if not student:
        student = StudentProfile.objects.filter(user=request.user).first()
    return student


class StudentBadgeListView(APIView):
    """Retrieve all curriculum achievement badges annotated with student unlock status."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Student Achievement Badges",
        description="Fetch all system badges with unlock state, criteria thresholds, and completion percentages.",
        responses={200: BadgeSummarySerializer(many=True)},
        tags=["Student Achievements"],
    )
    def get(self, request):
        student = _get_student(request)
        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        # Trigger live evaluation before returning summary
        AchievementService.evaluate_achievements(student)
        badges_data = AchievementService.get_student_badges_summary(student)
        serializer = BadgeSummarySerializer(badges_data, many=True)

        return api_success(
            data={"badges": serializer.data, "count": len(serializer.data)},
            message="Achievement badges retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class StudentCertificateListView(APIView):
    """Retrieve verified completion certificates issued to the authenticated student."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Student Certificates",
        description="Fetch verified institutional certificates earned by the student.",
        responses={200: CertificateSerializer(many=True)},
        tags=["Student Certificates"],
    )
    def get(self, request):
        student = _get_student(request)
        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        certificates = CertificateService.list_student_certificates(student)
        serializer = CertificateSerializer(certificates, many=True)

        return api_success(
            data={"certificates": serializer.data, "count": len(serializer.data)},
            message="Certificates retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


from drf_spectacular.types import OpenApiTypes


class StudentCertificateDownloadView(APIView):
    """Download official PDF completion certificate document."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Download Certificate PDF",
        description="Stream the signed PDF document for the certificate.",
        responses={200: OpenApiTypes.BINARY},
        tags=["Student Certificates"],
    )
    def get(self, request, certificate_id: uuid.UUID):
        student = _get_student(request)
        try:
            cert = Certificate.objects.select_related("student").get(id=certificate_id)
        except Certificate.DoesNotExist:
            return api_error(
                code="NOT_FOUND",
                message="Certificate not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Authorization: Only the owner student or staff/admin can download
        is_owner = student and cert.student_id == student.id
        is_staff = request.user.is_staff or getattr(request.user, "role", "") == "ADMIN"
        if not (is_owner or is_staff):
            return api_error(
                code="PERMISSION_DENIED",
                message="You do not have authorization to download this certificate.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if cert.is_revoked:
            return api_error(
                code="CERTIFICATE_REVOKED",
                message="This certificate has been revoked.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # If PDF file is not generated yet, generate synchronously on-demand
        if not cert.pdf_file:
            _generate_certificate_pdf_worker(str(cert.id))
            cert.refresh_from_db()

        if not cert.pdf_file or not cert.pdf_file.storage.exists(cert.pdf_file.name):
            return api_error(
                code="PDF_UNAVAILABLE",
                message="Certificate PDF document is being generated. Please retry shortly.",
                status_code=status.HTTP_202_ACCEPTED,
            )

        response = FileResponse(
            cert.pdf_file.open("rb"),
            content_type="application/pdf",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="{cert.certificate_id}.pdf"'
        )
        return response


class PublicCertificateVerifyView(APIView):
    """Public verification endpoint for employers, institutions, and students."""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Verify Certificate Publicly",
        description="Verify authenticity of an issued certificate using its identifier or SHA-256 hash.",
        responses={200: CertificateVerificationSerializer},
        tags=["Public Verification"],
    )
    def get(self, request, identifier: str):
        try:
            result = CertificateService.verify_certificate(identifier)
            if not result.get("is_valid"):
                return api_error(
                    code="CERTIFICATE_REVOKED",
                    message=result.get(
                        "message", "This certificate has been officially revoked."
                    ),
                    details=result,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            return api_success(
                data=result,
                message="Certificate authenticity verified.",
                status_code=status.HTTP_200_OK,
            )
        except (NotFound, Http404, ObjectDoesNotExist):
            return api_error(
                code="NOT_FOUND",
                message="Certificate not found. Please verify the ID or hash.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
