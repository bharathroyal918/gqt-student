"""URL routes for Student-facing Notifications and Announcements."""

from django.urls import path

from apps.notifications.views import (
    StudentAnnouncementListView,
    StudentNotificationDeleteView,
    StudentNotificationListView,
    StudentNotificationMarkAllReadView,
    StudentNotificationMarkReadView,
    StudentNotificationUnreadCountView,
)

app_name = "notifications"

urlpatterns = [
    path("", StudentNotificationListView.as_view(), name="notification_list"),
    path("unread-count/", StudentNotificationUnreadCountView.as_view(), name="unread_count"),
    path("<uuid:notification_id>/read/", StudentNotificationMarkReadView.as_view(), name="mark_read"),
    path("mark-all-read/", StudentNotificationMarkAllReadView.as_view(), name="mark_all_read"),
    path("<uuid:notification_id>/", StudentNotificationDeleteView.as_view(), name="delete_notification"),
    path("announcements/", StudentAnnouncementListView.as_view(), name="student_announcements"),
]
