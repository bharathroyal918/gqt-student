"""Admin URL routes for capstone project management and submission grading."""

from django.urls import path

from apps.projects.admin_views import (
    ProjectAdminDetailUpdateView,
    ProjectAdminListCreateView,
    ProjectSubmissionAdminDetailReviewView,
    ProjectSubmissionAdminListView,
    ProjectSubmissionFilesView,
)

app_name = "admin_projects"

urlpatterns = [
    path("", ProjectAdminListCreateView.as_view(), name="project_list_create"),
    path(
        "<uuid:pk>/",
        ProjectAdminDetailUpdateView.as_view(),
        name="project_detail_update",
    ),
    path(
        "submissions/", ProjectSubmissionAdminListView.as_view(), name="submission_list"
    ),
    path(
        "submissions/<uuid:pk>/",
        ProjectSubmissionAdminDetailReviewView.as_view(),
        name="submission_detail_review",
    ),
    path(
        "submissions/<uuid:pk>/files/",
        ProjectSubmissionFilesView.as_view(),
        name="submission_files",
    ),
]
