"""URL patterns for authentication and password recovery."""

from django.urls import path

from apps.accounts.views import (
    AdminLoginView,
    AdminProfileView,
    AvatarUploadView,
    ChangePasswordView,
    EmailLoginView,
    ForgotPasswordOTPRequestView,
    ForgotPasswordOTPVerifyView,
    ForgotPasswordView,
    LogoutView,
    MeView,
    RefreshTokenView,
    RequestOTPView,
    ResetPasswordView,
    StudentLoginView,
    StudentRegisterView,
    VerifyOTPView,
)

from apps.students.tpo_views import TPOLoginView, TPORegisterView

app_name = "auth"

urlpatterns = [
    # Registration
    path("register/", StudentRegisterView.as_view(), name="register"),
    path("student/register/", StudentRegisterView.as_view(), name="student_register"),
    path("register/tpo/", TPORegisterView.as_view(), name="register_tpo"),
    path("tpo/register/", TPORegisterView.as_view(), name="tpo_register"),
    # Dedicated Logins
    path("login/student/", StudentLoginView.as_view(), name="login_student"),
    path("login/admin/", AdminLoginView.as_view(), name="login_admin"),
    path("login/tpo/", TPOLoginView.as_view(), name="login_tpo"),
    path("tpo/login/", TPOLoginView.as_view(), name="tpo_login"),
    path("login/email/", EmailLoginView.as_view(), name="login_email"),
    # OTP-based Login
    path("otp/request/", RequestOTPView.as_view(), name="otp_request"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp_verify"),
    # Session lifecycle
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # OTP & Token Password Reset
    path(
        "password/forgot-otp/",
        ForgotPasswordOTPRequestView.as_view(),
        name="password_forgot_otp",
    ),
    path(
        "password/verify-reset-otp/",
        ForgotPasswordOTPVerifyView.as_view(),
        name="password_verify_reset_otp",
    ),
    path("password/forgot/", ForgotPasswordView.as_view(), name="password_forgot"),
    path("password/reset/", ResetPasswordView.as_view(), name="password_reset"),
    path("password/change/", ChangePasswordView.as_view(), name="password_change"),
    # User Profile & Admin Settings
    path("me/", MeView.as_view(), name="me"),
    path("avatar/upload/", AvatarUploadView.as_view(), name="avatar_upload"),
    path("admin/profile/", AdminProfileView.as_view(), name="admin_profile"),
]
