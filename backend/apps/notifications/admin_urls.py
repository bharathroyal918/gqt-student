"""Admin URL routes for announcements."""

from django.urls import path

from apps.notifications.admin_views import (
    AnnouncementAdminAuditHistoryView,
    AnnouncementAdminDetailUpdateDeleteView,
    AnnouncementAdminListCreateView,
    AnnouncementAdminPublishView,
)

app_name = "admin_announcements"

urlpatterns = [
    path("", AnnouncementAdminListCreateView.as_view(), name="list_create"),
    path(
        "<uuid:pk>/",
        AnnouncementAdminDetailUpdateDeleteView.as_view(),
        name="detail_update_delete",
    ),
    path(
        "<uuid:pk>/publish/",
        AnnouncementAdminPublishView.as_view(),
        name="publish",
    ),
    path(
        "<uuid:pk>/audit/",
        AnnouncementAdminAuditHistoryView.as_view(),
        name="audit_history",
    ),
]
