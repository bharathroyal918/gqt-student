from django.urls import path
from apps.placements.views import (
    AdminPlacementDriveListCreateView,
    AdminPlacementDriveDetailView,
    AdminPlacementApplicationListView,
    AdminPlacementApplicationStatusUpdateView,
    AdminPlacementStatsView,
    PlacementResumeDownloadView,
)

urlpatterns = [
    path("stats/", AdminPlacementStatsView.as_view(), name="admin_placement_stats"),
    path("drives/", AdminPlacementDriveListCreateView.as_view(), name="admin_placement_drives_list_create"),
    path("drives/<uuid:drive_id>/", AdminPlacementDriveDetailView.as_view(), name="admin_placement_drive_detail"),
    path("drives/<uuid:drive_id>/applications/", AdminPlacementApplicationListView.as_view(), name="admin_placement_drive_applications"),
    path("applications/", AdminPlacementApplicationListView.as_view(), name="admin_placement_all_applications"),
    path("applications/<uuid:application_id>/status/", AdminPlacementApplicationStatusUpdateView.as_view(), name="admin_placement_application_status"),
    path("applications/<uuid:application_id>/resume/", PlacementResumeDownloadView.as_view(), name="admin_placement_application_resume"),
]
