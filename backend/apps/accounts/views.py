"""Views for authentication, password lifecycle, user identity, and student provisioning."""

import logging
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.serializers import (
    EmailLoginSerializer,
    ForgotPasswordSerializer,
    LogoutSerializer,
    RefreshTokenSerializer,
    RequestOTPSerializer,
    ResetPasswordSerializer,
    StudentProfileNestedSerializer,
    StudentProvisionSerializer,
    StudentStatusUpdateSerializer,
    UserProfileSerializer,
    VerifyOTPSerializer,
)
from apps.accounts.services import AuthService, StudentProvisioningService
from apps.common.permissions import IsAdmin
from apps.common.responses import api_success
from apps.common.utils import get_client_ip, mask_email, mask_phone

logger = logging.getLogger(__name__)


class EmailLoginView(APIView):
    """Authenticate a student or admin user using email and password."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=EmailLoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful"),
            401: OpenApiResponse(description="Invalid credentials"),
            403: OpenApiResponse(description="Account inactive or unapproved"),
        },
        summary="Email/Password Authentication",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        user, access_token, refresh_token, user_data = AuthService.login_with_email(
            email=email,
            password=password,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return api_success(
            data={
                "access": access_token,
                "refresh": refresh_token,
                "user": user_data,
            },
            message="Authentication successful.",
            status_code=status.HTTP_200_OK,
        )


class RequestOTPView(APIView):
    """Request a one-time password (OTP) sent to an approved student mobile number."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=RequestOTPSerializer,
        responses={
            200: OpenApiResponse(
                description="OTP requested (generic response to prevent enumeration)"
            ),
            429: OpenApiResponse(description="Cooldown active or rate limit exceeded"),
        },
        summary="Request Login OTP",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile_number = serializer.validated_data["mobile_number"].strip()
        ip_address = get_client_ip(request)

        AuthService.request_otp(mobile_number=mobile_number, ip_address=ip_address)

        return api_success(
            data={"mobile_number": mask_phone(mobile_number)},
            message="If this mobile number is registered and approved, an OTP has been sent.",
            status_code=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    """Verify numeric OTP and issue JWT access/refresh token pair for student."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(description="OTP verified successfully"),
            400: OpenApiResponse(description="Invalid, expired, or maximum attempts exceeded"),
            403: OpenApiResponse(description="Account inactive or unapproved"),
        },
        summary="Verify Login OTP",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile_number = serializer.validated_data["mobile_number"].strip()
        otp = serializer.validated_data["otp"].strip()
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        user, access_token, refresh_token, user_data = AuthService.verify_otp_and_login(
            mobile_number=mobile_number,
            otp=otp,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return api_success(
            data={
                "access": access_token,
                "refresh": refresh_token,
                "user": user_data,
            },
            message="OTP verified successfully.",
            status_code=status.HTTP_200_OK,
        )


class RefreshTokenView(APIView):
    """Rotate JWT refresh token and issue a fresh access and refresh token pair."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=RefreshTokenSerializer,
        responses={
            200: OpenApiResponse(description="Token refreshed successfully"),
            401: OpenApiResponse(description="Invalid or blacklisted token"),
        },
        summary="Refresh Access Token",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token_str = serializer.validated_data["refresh"]
        new_access, new_refresh = AuthService.rotate_token(refresh_token_str)

        return api_success(
            data={
                "access": new_access,
                "refresh": new_refresh,
            },
            message="Token refreshed successfully.",
            status_code=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Revoke and blacklist active refresh token upon user logout."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(description="Successfully logged out"),
            400: OpenApiResponse(description="Invalid token"),
        },
        summary="User Logout",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token_str = serializer.validated_data["refresh"]
        ip_address = get_client_ip(request)
        AuthService.logout(
            refresh_token_str=refresh_token_str,
            user=request.user,
            ip_address=ip_address,
        )

        return api_success(
            data={},
            message="Successfully logged out.",
            status_code=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    """Initiate password reset flow for approved accounts with anti-enumeration protection."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Instructions dispatched if account exists"),
        },
        summary="Forgot Password Request",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        ip_address = get_client_ip(request)

        AuthService.request_password_reset(email=email, ip_address=ip_address)

        return api_success(
            data={"email": mask_email(email)},
            message="If an account with that email exists and is active, password reset instructions have been sent.",
            status_code=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """Set new password using a valid cryptographic reset token."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successfully"),
            400: OpenApiResponse(description="Invalid or expired reset token"),
        },
        summary="Complete Password Reset",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"].strip()
        new_password = serializer.validated_data["new_password"]
        ip_address = get_client_ip(request)

        AuthService.reset_password(token=token, new_password=new_password, ip_address=ip_address)

        return api_success(
            data={},
            message="Password has been successfully reset. Please log in with your new password.",
            status_code=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Retrieve authenticated user's profile and academic or administrative role data."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer},
        summary="Current User Profile",
        tags=["Authentication"],
    )
    def get(self, request):
        user_data = AuthService.get_user_profile_data(request.user)
        return api_success(
            data={"user": user_data},
            message="User profile retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )


class AdminStudentProvisionView(APIView):
    """Admin-only endpoint to onboard and provision a new student with approved credentials."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=StudentProvisionSerializer,
        responses={201: OpenApiResponse(description="Student provisioned successfully")},
        summary="Admin Provision Student",
        tags=["Admin Student Management"],
    )
    def post(self, request):
        serializer = StudentProvisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        ip_address = get_client_ip(request)

        user, profile = StudentProvisioningService.provision_student(
            admin_user=request.user,
            full_name=data["full_name"],
            student_id_number=data["student_id_number"],
            batch_code=data["batch_code"],
            email=data.get("email"),
            mobile_number=data.get("mobile_number"),
            password=data.get("password"),
            college_name=data.get("college_name", ""),
            graduation_year=data.get("graduation_year"),
            onboarding_status=data.get("onboarding_status", "ACTIVE"),
            ip_address=ip_address,
        )

        return api_success(
            data={
                "user_id": str(user.id),
                "profile": StudentProfileNestedSerializer(profile).data,
                "email": user.email,
                "mobile_number": user.mobile_number,
                "onboarding_status": user.onboarding_status,
                "is_active": user.is_active,
            },
            message="Student provisioned successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class AdminStudentStatusView(APIView):
    """Admin-only endpoint to activate/deactivate an account or grant/revoke portal access."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=StudentStatusUpdateSerializer,
        responses={200: OpenApiResponse(description="Student status updated successfully")},
        summary="Admin Update Student Status",
        tags=["Admin Student Management"],
    )
    def patch(self, request, pk):
        serializer = StudentStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        ip_address = get_client_ip(request)

        profile = StudentProvisioningService.update_student_status(
            admin_user=request.user,
            student_profile_id=str(pk),
            is_active=data.get("is_active"),
            onboarding_status=data.get("onboarding_status"),
            reason=data.get("reason", ""),
            ip_address=ip_address,
        )

        return api_success(
            data={
                "profile": StudentProfileNestedSerializer(profile).data,
                "is_active": profile.user.is_active,
                "onboarding_status": profile.user.onboarding_status,
            },
            message="Student status updated successfully.",
            status_code=status.HTTP_200_OK,
        )
