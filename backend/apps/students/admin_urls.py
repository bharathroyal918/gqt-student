"""Admin URL routes for student management."""

from django.urls import path

from apps.accounts.views import AdminStudentProvisionView, AdminStudentStatusView
from apps.students.admin_views import (
    StudentAdminAttendanceView,
    StudentAdminCoursesView,
    StudentAdminDetailUpdateView,
    StudentAdminGrantAccessByEmailView,
    StudentAdminGrantAccessView,
    StudentAdminListCreateView,
    StudentAdminProgressView,
    StudentAdminRankView,
    StudentAdminRevokeAccessView,
    StudentAdminScoresView,
)

app_name = "admin_students"

urlpatterns = [
    path("", StudentAdminListCreateView.as_view(), name="list_create"),
    path("provision/", AdminStudentProvisionView.as_view(), name="provision"),
    path("grant-access-by-email/", StudentAdminGrantAccessByEmailView.as_view(), name="grant_access_by_email"),
    path("<uuid:pk>/", StudentAdminDetailUpdateView.as_view(), name="detail_update"),
    path("<uuid:pk>/status/", AdminStudentStatusView.as_view(), name="status"),
    path("<uuid:pk>/grant-access/", StudentAdminGrantAccessView.as_view(), name="grant_access"),
    path("<uuid:pk>/revoke-access/", StudentAdminRevokeAccessView.as_view(), name="revoke_access"),
    path("<uuid:pk>/attendance/", StudentAdminAttendanceView.as_view(), name="attendance"),
    path("<uuid:pk>/courses/", StudentAdminCoursesView.as_view(), name="assign_courses"),
    path("<uuid:pk>/progress/", StudentAdminProgressView.as_view(), name="progress"),
    path("<uuid:pk>/scores/", StudentAdminScoresView.as_view(), name="scores"),
    path("<uuid:pk>/rank/", StudentAdminRankView.as_view(), name="rank"),
]
