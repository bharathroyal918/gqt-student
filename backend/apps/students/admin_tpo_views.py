"""Admin views for managing TPO accounts, college assignments, and access lifecycle."""

import logging
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.views import APIView

from apps.common.permissions import IsAdmin
from apps.common.responses import api_success
from apps.common.utils import get_client_ip
from apps.students.admin_tpo_serializers import (
    AdminTPOAuditLogSerializer,
    AdminTPODetailSerializer,
    AdminTPOListSerializer,
    AdminTPOProvisionSerializer,
    AdminTPOReassignCollegeSerializer,
    AdminTPOUpdateSerializer,
)
from apps.students.admin_tpo_services import AdminTPOService

logger = logging.getLogger(__name__)


class AdminTPOListCreateView(generics.ListAPIView):
    """Admin endpoint to list all TPO accounts or provision a new TPO officer."""

    permission_classes = [IsAdmin]
    serializer_class = AdminTPOListSerializer

    def get_queryset(self):
        search = self.request.query_params.get("search")
        college_id = self.request.query_params.get("college_id")
        is_active_param = self.request.query_params.get("is_active")

        is_active = None
        if is_active_param is not None:
            if is_active_param.lower() in ["true", "1"]:
                is_active = True
            elif is_active_param.lower() in ["false", "0"]:
                is_active = False

        return AdminTPOService.list_tpos(
            search=search, college_id=college_id, is_active=is_active
        )

    @extend_schema(
        request=AdminTPOProvisionSerializer,
        responses={201: AdminTPODetailSerializer},
        summary="Admin Provision / Invite TPO",
        tags=["Admin TPO Management"],
    )
    def post(self, request, *args, **kwargs):
        serializer = AdminTPOProvisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        user, profile, setup_token = AdminTPOService.provision_tpo(
            admin_user=request.user,
            email=data["email"],
            full_name=data["full_name"],
            college_id=str(data["college_id"]),
            designation=data.get("designation", "Training & Placement Officer"),
            department=data.get("department", "Training & Placement Cell"),
            phone_number=data.get("phone_number", ""),
            bio=data.get("bio", ""),
            ip_address=ip_address,
        )

        return api_success(
            data=AdminTPODetailSerializer(profile).data,
            message=f"TPO account for '{profile.full_name}' created and assigned to {profile.college.name} successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class AdminTPODetailUpdateView(APIView):
    """Admin endpoint to view or update a specific TPO officer profile."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: AdminTPODetailSerializer},
        summary="Admin Retrieve TPO Detail",
        tags=["Admin TPO Management"],
    )
    def get(self, request, pk):
        tpo = AdminTPOService.get_tpo_detail(str(pk))
        return api_success(
            data=AdminTPODetailSerializer(tpo).data,
            message="TPO details retrieved successfully.",
        )

    @extend_schema(
        request=AdminTPOUpdateSerializer,
        responses={200: AdminTPODetailSerializer},
        summary="Admin Update TPO Metadata",
        tags=["Admin TPO Management"],
    )
    def patch(self, request, pk):
        serializer = AdminTPOUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        updated_tpo = AdminTPOService.update_tpo(
            tpo_id=str(pk),
            admin_user=request.user,
            ip_address=ip_address,
            **serializer.validated_data,
        )
        return api_success(
            data=AdminTPODetailSerializer(updated_tpo).data,
            message=f"TPO '{updated_tpo.full_name}' updated successfully.",
        )


class AdminTPOReassignCollegeView(APIView):
    """Admin endpoint to atomically reassign a TPO to another existing college."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=AdminTPOReassignCollegeSerializer,
        responses={200: AdminTPODetailSerializer},
        summary="Admin Reassign TPO College",
        tags=["Admin TPO Management"],
    )
    def post(self, request, pk):
        serializer = AdminTPOReassignCollegeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        tpo = AdminTPOService.reassign_college(
            tpo_id=str(pk),
            new_college_id=str(serializer.validated_data["college_id"]),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=AdminTPODetailSerializer(tpo).data,
            message=f"TPO '{tpo.full_name}' successfully reassigned to {tpo.college.name}.",
        )


class AdminTPODeactivateView(APIView):
    """Admin endpoint to suspend/deactivate a TPO and revoke active sessions."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=None,
        responses={200: AdminTPODetailSerializer},
        summary="Admin Deactivate TPO Access",
        tags=["Admin TPO Management"],
    )
    def post(self, request, pk):
        ip_address = get_client_ip(request)
        tpo = AdminTPOService.deactivate_tpo(
            tpo_id=str(pk), admin_user=request.user, ip_address=ip_address
        )
        return api_success(
            data=AdminTPODetailSerializer(tpo).data,
            message=f"TPO '{tpo.full_name}' has been deactivated.",
        )


class AdminTPOReactivateView(APIView):
    """Admin endpoint to reactivate a suspended TPO account."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=None,
        responses={200: AdminTPODetailSerializer},
        summary="Admin Reactivate TPO Access",
        tags=["Admin TPO Management"],
    )
    def post(self, request, pk):
        ip_address = get_client_ip(request)
        tpo = AdminTPOService.reactivate_tpo(
            tpo_id=str(pk), admin_user=request.user, ip_address=ip_address
        )
        return api_success(
            data=AdminTPODetailSerializer(tpo).data,
            message=f"TPO '{tpo.full_name}' has been reactivated.",
        )


class AdminTPOAuditHistoryView(APIView):
    """Admin endpoint to inspect audit history for a specific TPO."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: AdminTPOAuditLogSerializer(many=True)},
        summary="Admin View TPO Audit History",
        tags=["Admin TPO Management"],
    )
    def get(self, request, pk):
        audit_logs = AdminTPOService.get_tpo_audit_history(str(pk))
        return api_success(
            data=AdminTPOAuditLogSerializer(audit_logs, many=True).data,
            message="TPO audit history retrieved successfully.",
        )
