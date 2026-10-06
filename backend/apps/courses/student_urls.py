"""Student URL patterns for Recorded Classes."""

from django.urls import path

from apps.courses.student_views import (
    StudentRecordedClassProgressUpdateView,
    StudentRecordedClassStreamView,
    StudentRecordedCoursePlaylistView,
    StudentRecordedCoursesCatalogView,
)

app_name = "student_recorded_classes"

urlpatterns = [
    path("", StudentRecordedCoursesCatalogView.as_view(), name="catalog"),
    path("<uuid:course_id>/", StudentRecordedCoursePlaylistView.as_view(), name="course_playlist"),
    path("<uuid:course_id>/videos/<uuid:video_id>/", StudentRecordedClassStreamView.as_view(), name="video_stream"),
    path("<uuid:course_id>/videos/<uuid:video_id>/progress/", StudentRecordedClassProgressUpdateView.as_view(), name="video_progress"),
]
