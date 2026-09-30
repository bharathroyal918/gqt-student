"""Admin URL routes for student management."""

from django.urls import path

from apps.accounts.views import AdminStudentProvisionView, AdminStudentStatusView
from apps.students.admin_views import (
    StudentAdminCoursesView,
    StudentAdminDetailUpdateView,
    StudentAdminListCreateView,
    StudentAdminProgressView,
    StudentAdminRankView,
    StudentAdminScoresView,
)

app_name = "admin_students"

urlpatterns = [
    path("", StudentAdminListCreateView.as_view(), name="list_create"),
    path("provision/", AdminStudentProvisionView.as_view(), name="provision"),
    path("<uuid:pk>/", StudentAdminDetailUpdateView.as_view(), name="detail_update"),
    path("<uuid:pk>/status/", AdminStudentStatusView.as_view(), name="status"),
    path("<uuid:pk>/courses/", StudentAdminCoursesView.as_view(), name="assign_courses"),
    path("<uuid:pk>/progress/", StudentAdminProgressView.as_view(), name="progress"),
    path("<uuid:pk>/scores/", StudentAdminScoresView.as_view(), name="scores"),
    path("<uuid:pk>/rank/", StudentAdminRankView.as_view(), name="rank"),
]
