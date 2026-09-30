"""Admin URL routes for course management."""

from django.urls import path

from apps.courses.admin_views import (
    CourseAdminDetailUpdateDeleteView,
    CourseAdminListCreateView,
    CourseAdminPublishView,
)

app_name = "admin_courses"

urlpatterns = [
    path("", CourseAdminListCreateView.as_view(), name="list_create"),
    path("<uuid:pk>/", CourseAdminDetailUpdateDeleteView.as_view(), name="detail_update_delete"),
    path("<uuid:pk>/publish/", CourseAdminPublishView.as_view(), name="publish"),
]
