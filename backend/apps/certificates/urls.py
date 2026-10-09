"""URL routes for Student Achievements, Badges, and Certificate verification."""

from django.urls import path

from apps.certificates.views import (
    PublicCertificateVerifyView,
    StudentBadgeListView,
    StudentCertificateDownloadView,
    StudentCertificateListView,
)

app_name = "certificates"

urlpatterns = [
    path("achievements/", StudentBadgeListView.as_view(), name="student_badges"),
    path(
        "certificates/",
        StudentCertificateListView.as_view(),
        name="student_certificates",
    ),
    path(
        "certificates/<uuid:certificate_id>/download/",
        StudentCertificateDownloadView.as_view(),
        name="certificate_download",
    ),
    path(
        "verify/<str:identifier>/",
        PublicCertificateVerifyView.as_view(),
        name="public_verify",
    ),
]
