"""Admin URL routes for certificate management."""

from django.urls import path

from apps.certificates.admin_views import (
    AdminCertificateListView,
    AdminCertificateRevokeView,
)

app_name = "admin_certificates"

urlpatterns = [
    path("", AdminCertificateListView.as_view(), name="list"),
    path("<uuid:certificate_id>/revoke/", AdminCertificateRevokeView.as_view(), name="revoke"),
]
