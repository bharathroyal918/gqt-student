"""URL patterns for administrative student provisioning and status management."""

from django.urls import path

from apps.accounts.views import AdminStudentProvisionView, AdminStudentStatusView

app_name = "admin_students"

urlpatterns = [
    path("provision/", AdminStudentProvisionView.as_view(), name="provision"),
    path("<uuid:pk>/status/", AdminStudentStatusView.as_view(), name="status"),
]
