"""Admin URL routes for daily practice task management."""

from django.urls import path

from apps.tasks.admin_views import (
    TaskAdminCompletionsView,
    TaskAdminDetailUpdateDeleteView,
    TaskAdminListCreateView,
)

app_name = "admin_tasks"

urlpatterns = [
    path("", TaskAdminListCreateView.as_view(), name="list_create"),
    path("<uuid:pk>/", TaskAdminDetailUpdateDeleteView.as_view(), name="detail_update_delete"),
    path("<uuid:pk>/completions/", TaskAdminCompletionsView.as_view(), name="completions"),
]
