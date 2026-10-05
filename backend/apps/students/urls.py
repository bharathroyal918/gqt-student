"""URL patterns for students app."""

from django.urls import path

from apps.accounts.views import AvatarUploadView
from apps.students.views import (
    StudentAttendanceSelfView,
    StudentCourseDetailView,
    StudentCourseListView,
    StudentDashboardView,
    StudentLeaderboardView,
    StudentModuleCompleteView,
    StudentModuleDetailView,
    StudentProfileDetailView,
    StudentProfileSelfUpdateView,
)

app_name = "students"

urlpatterns = [
    path("dashboard/", StudentDashboardView.as_view(), name="student_dashboard"),
    path("leaderboard/", StudentLeaderboardView.as_view(), name="student_leaderboard"),
    path("avatar/upload/", AvatarUploadView.as_view(), name="student_avatar_upload"),
    path("me/profile/", StudentProfileSelfUpdateView.as_view(), name="student_profile_me"),
    path("me/attendance/", StudentAttendanceSelfView.as_view(), name="student_attendance_me"),
    path("courses/", StudentCourseListView.as_view(), name="student_courses"),
    path("courses/<uuid:course_id>/", StudentCourseDetailView.as_view(), name="student_course_detail"),
    path("modules/<uuid:module_id>/", StudentModuleDetailView.as_view(), name="student_module_detail"),
    path("modules/<uuid:module_id>/complete/", StudentModuleCompleteView.as_view(), name="student_module_complete"),
    path("<uuid:pk>/profile/", StudentProfileDetailView.as_view(), name="student_profile_detail"),
]
