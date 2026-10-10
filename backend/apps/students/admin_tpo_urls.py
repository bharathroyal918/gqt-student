"""Admin URL patterns for TPO management and college assignments."""

from django.urls import path

from apps.students.admin_tpo_views import (
    AdminTPOApproveView,
    AdminTPOAuditHistoryView,
    AdminTPODeactivateView,
    AdminTPODetailUpdateView,
    AdminTPOListCreateView,
    AdminTPOReactivateView,
    AdminTPOReassignCollegeView,
)

app_name = "admin_tpos"

urlpatterns = [
    path("", AdminTPOListCreateView.as_view(), name="list_create"),
    path("<uuid:pk>/", AdminTPODetailUpdateView.as_view(), name="detail_update"),
    path("<uuid:pk>/approve/", AdminTPOApproveView.as_view(), name="approve"),
    path("<uuid:pk>/reassign-college/", AdminTPOReassignCollegeView.as_view(), name="reassign_college"),
    path("<uuid:pk>/deactivate/", AdminTPODeactivateView.as_view(), name="deactivate"),
    path("<uuid:pk>/reactivate/", AdminTPOReactivateView.as_view(), name="reactivate"),
    path("<uuid:pk>/audit-history/", AdminTPOAuditHistoryView.as_view(), name="audit_history"),
]
