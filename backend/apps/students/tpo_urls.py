"""URL patterns for TPO Portal API endpoints."""

from django.urls import path

from apps.students.tpo_views import (
    TPOAssignmentsLabsView,
    TPOAttendanceAnalyticsView,
    TPOCollegeDetailView,
    TPOCollegeSummaryView,
    TPOLeaderboardView,
    TPOLearningProgressView,
    TPOLoginView,
    TPOPerformanceTrendsView,
    TPOProfileMeView,
    TPOReportExportView,
    TPOReportPreviewView,
    TPOReportTypesListView,
    TPOStudentDetailView,
    TPOStudentsNeedingSupportView,
    TPOStudentRosterView,
)

app_name = "tpo"

urlpatterns = [
    path("auth/login/", TPOLoginView.as_view(), name="login"),
    path("me/", TPOProfileMeView.as_view(), name="profile_me"),
    path("college/", TPOCollegeDetailView.as_view(), name="college_detail"),
    path("college/summary/", TPOCollegeSummaryView.as_view(), name="college_summary"),
    path("college/students/", TPOStudentRosterView.as_view(), name="college_students"),
    path("college/students/<uuid:pk>/", TPOStudentDetailView.as_view(), name="college_student_detail"),
    # Phase 5 Analytics Endpoints
    path("analytics/learning-progress/", TPOLearningProgressView.as_view(), name="analytics_learning_progress"),
    path("analytics/assignments-labs/", TPOAssignmentsLabsView.as_view(), name="analytics_assignments_labs"),
    path("analytics/attendance/", TPOAttendanceAnalyticsView.as_view(), name="analytics_attendance"),
    path("analytics/trends/", TPOPerformanceTrendsView.as_view(), name="analytics_trends"),
    path("analytics/students-needing-support/", TPOStudentsNeedingSupportView.as_view(), name="analytics_students_needing_support"),
    path("analytics/leaderboard/", TPOLeaderboardView.as_view(), name="analytics_leaderboard"),
    # Phase 6 Reports & Secure Exports Endpoints
    path("reports/types/", TPOReportTypesListView.as_view(), name="reports_types"),
    path("reports/preview/", TPOReportPreviewView.as_view(), name="reports_preview"),
    path("reports/export/", TPOReportExportView.as_view(), name="reports_export"),
]


