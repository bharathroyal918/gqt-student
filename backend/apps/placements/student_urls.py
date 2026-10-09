from django.urls import path

from apps.placements.views import (
    PlacementResumeDownloadView,
    StudentMyApplicationsView,
    StudentPlacementApplyView,
    StudentPlacementDriveDetailView,
    StudentPlacementDriveListView,
)

urlpatterns = [
    path(
        "drives/",
        StudentPlacementDriveListView.as_view(),
        name="student_placement_drives_list",
    ),
    path(
        "drives/<uuid:drive_id>/",
        StudentPlacementDriveDetailView.as_view(),
        name="student_placement_drive_detail",
    ),
    path(
        "drives/<uuid:drive_id>/apply/",
        StudentPlacementApplyView.as_view(),
        name="student_placement_apply",
    ),
    path(
        "my-applications/",
        StudentMyApplicationsView.as_view(),
        name="student_my_placement_applications",
    ),
    path(
        "applications/<uuid:application_id>/resume/",
        PlacementResumeDownloadView.as_view(),
        name="placement_resume_download",
    ),
]
