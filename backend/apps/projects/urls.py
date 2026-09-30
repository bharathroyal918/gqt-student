"""URL routing for Student-Facing Project views."""

from django.urls import path
from apps.projects.views import (
    ProjectFileDownloadView,
    StudentProjectDetailView,
    StudentProjectListView,
    StudentProjectSubmitView,
)

app_name = "student_projects"

urlpatterns = [
    path("", StudentProjectListView.as_view(), name="project_list"),
    path("<uuid:project_id>/", StudentProjectDetailView.as_view(), name="project_detail"),
    path("<uuid:project_id>/submit/", StudentProjectSubmitView.as_view(), name="project_submit"),
    path("files/<uuid:file_id>/download/", ProjectFileDownloadView.as_view(), name="file_download"),
]
