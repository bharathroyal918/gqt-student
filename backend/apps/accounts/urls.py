"""URL patterns for authentication and password recovery."""

from django.urls import path

from apps.accounts.views import (
    EmailLoginView,
    ForgotPasswordView,
    LogoutView,
    MeView,
    RefreshTokenView,
    RequestOTPView,
    ResetPasswordView,
    VerifyOTPView,
)

app_name = "auth"

urlpatterns = [
    path("login/email/", EmailLoginView.as_view(), name="login_email"),
    path("otp/request/", RequestOTPView.as_view(), name="otp_request"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp_verify"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password/forgot/", ForgotPasswordView.as_view(), name="password_forgot"),
    path("password/reset/", ResetPasswordView.as_view(), name="password_reset"),
    path("me/", MeView.as_view(), name="me"),
]
