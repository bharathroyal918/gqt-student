"""Views for authentication, password lifecycle, user identity, and student provisioning."""

import logging
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.serializers import (
    AdminLoginSerializer,
    EmailLoginSerializer,
    ForgotPasswordOTPRequestSerializer,
    ForgotPasswordOTPVerifySerializer,
    ForgotPasswordSerializer,
    LogoutSerializer,
    RefreshTokenSerializer,
    RequestOTPSerializer,
    ResetPasswordSerializer,
    StudentLoginSerializer,
    StudentProfileNestedSerializer,
    StudentProvisionSerializer,
    StudentRegisterSerializer,
    StudentStatusUpdateSerializer,
    UserProfileSerializer,
    VerifyOTPSerializer,
)
from apps.accounts.services import AuthService, StudentProvisioningService
from apps.common.permissions import IsAdmin
from apps.common.responses import api_success
from apps.common.utils import get_client_ip, mask_email, mask_phone

logger = logging.getLogger(__name__)


class StudentRegisterView(APIView):
    """Register a new student account and provision student profile in the database."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=StudentRegisterSerializer,
        responses={
            201: OpenApiResponse(description="Registration successful"),
            400: OpenApiResponse(description="Validation error or duplicate account"),
        },
        summary="Student Self-Registration",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = StudentRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        user, access_token, refresh_token, user_data = AuthService.register_student(
            full_name=serializer.validated_data["full_name"],
            email=serializer.validated_data["email"],
            mobile_number=serializer.validated_data["mobile_number"],
            password=serializer.validated_data["password"],
            student_id_number=serializer.validated_data.get("student_id_number", ""),
            college_name=serializer.validated_data.get("college_name", ""),
            batch_code=serializer.validated_data.get("batch_code", "BATCH-2026-A"),
            graduation_year=serializer.validated_data.get("graduation_year", 2026),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return api_success(
            data={
                "access": access_token,
                "refresh": refresh_token,
                "user": user_data,
            },
            message="Student registration successful. Welcome to GQT!",
            status_code=status.HTTP_201_CREATED,
        )


class StudentLoginView(APIView):
    """Authenticate a student user specifically using email and password."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=StudentLoginSerializer,
        responses={
            200: OpenApiResponse(description="Student login successful"),
            401: OpenApiResponse(description="Invalid credentials"),
            403: OpenApiResponse(description="Forbidden role or inactive account"),
        },
        summary="Student Portal Login",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = StudentLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        user, access_token, refresh_token, user_data = AuthService.login_as_student(
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
            message="Student authentication successful.",
            status_code=status.HTTP_200_OK,
        )


class AdminLoginView(APIView):
    """Authenticate an administrator or faculty member specifically using email and password."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=AdminLoginSerializer,
        responses={
            200: OpenApiResponse(description="Admin login successful"),
            401: OpenApiResponse(description="Invalid credentials"),
            403: OpenApiResponse(description="Forbidden role or unauthorized access"),
        },
        summary="Admin Portal Login",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]
        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        user, access_token, refresh_token, user_data = AuthService.login_as_admin(
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
            message="Admin authentication successful.",
            status_code=status.HTTP_200_OK,
        )


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


class ForgotPasswordOTPRequestView(APIView):
    """Initiate OTP-based password reset for students and admins via email or mobile."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=ForgotPasswordOTPRequestSerializer,
        responses={
            200: OpenApiResponse(description="OTP dispatched if account exists"),
            429: OpenApiResponse(description="Cooldown active or rate limit exceeded"),
        },
        summary="Request Password Reset OTP",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = ForgotPasswordOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"].strip()
        ip_address = get_client_ip(request)

        result = AuthService.request_password_reset_otp(identifier=identifier, ip_address=ip_address)

        return api_success(
            data=result,
            message="If an active account exists with these credentials, a 6-digit OTP has been sent.",
            status_code=status.HTTP_200_OK,
        )


class ForgotPasswordOTPVerifyView(APIView):
    """Verify numeric OTP code and exchange for a one-time password reset token."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=ForgotPasswordOTPVerifySerializer,
        responses={
            200: OpenApiResponse(description="OTP verified successfully, returns reset token"),
            400: OpenApiResponse(description="Invalid, expired, or maximum attempts exceeded"),
        },
        summary="Verify Password Reset OTP",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = ForgotPasswordOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"].strip()
        otp = serializer.validated_data["otp"].strip()
        ip_address = get_client_ip(request)

        result = AuthService.verify_password_reset_otp(
            identifier=identifier, otp=otp, ip_address=ip_address
        )

        return api_success(
            data=result,
            message="OTP verified successfully. You may now set your new password.",
            status_code=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    """Initiate password reset flow (supports both legacy token and modern OTP methods)."""

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

        # Triggers both email token and OTP records for seamless client compatibility
        AuthService.request_password_reset(email=email, ip_address=ip_address)
        otp_info = AuthService.request_password_reset_otp(identifier=email, ip_address=ip_address)

        return api_success(
            data={
                "email": mask_email(email),
                "channel": "email",
                "otp_dispatched": True,
            },
            message="If an account with that email exists and is active, a 6-digit OTP and password reset instructions have been sent.",
            status_code=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """Set new password using a valid cryptographic reset token or direct OTP verification."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successfully"),
            400: OpenApiResponse(description="Invalid or expired reset token/OTP"),
        },
        summary="Complete Password Reset",
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data.get("token", "").strip()
        identifier = serializer.validated_data.get("identifier", "").strip()
        otp = serializer.validated_data.get("otp", "").strip()
        new_password = serializer.validated_data["new_password"]
        ip_address = get_client_ip(request)

        AuthService.reset_password_flexible(
            new_password=new_password,
            token=token,
            identifier=identifier,
            otp=otp,
            ip_address=ip_address,
        )

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
