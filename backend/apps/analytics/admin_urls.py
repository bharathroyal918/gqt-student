"""URL routing for Admin Analytics, Executive Reports, and Export Jobs."""

from django.urls import path

from apps.analytics.admin_views import (
    AnalyticsDashboardView,
    ReportAssignmentView,
    ReportCompletionView,
    ReportExportCreateView,
    ReportExportDetailView,
    ReportExportDownloadView,
    ReportExportListView,
    ReportMonthlyActivityView,
    ReportPerformanceView,
    ReportProjectView,
)

app_name = "admin_analytics"

urlpatterns = [
    # Dashboard KPI Metrics & Charts
    path("analytics/dashboard/", AnalyticsDashboardView.as_view(), name="dashboard"),

    # Domain Reports
    path("reports/performance/", ReportPerformanceView.as_view(), name="report_performance"),
    path("reports/completion/", ReportCompletionView.as_view(), name="report_completion"),
    path("reports/assignment/", ReportAssignmentView.as_view(), name="report_assignment"),
    path("reports/project/", ReportProjectView.as_view(), name="report_project"),
    path("reports/monthly-activity/", ReportMonthlyActivityView.as_view(), name="report_monthly_activity"),

    # Asynchronous Export Architecture
    path("reports/exports/", ReportExportListView.as_view(), name="export_list"),
    path("reports/export/", ReportExportCreateView.as_view(), name="export_create"),
    path("reports/exports/<uuid:job_id>/", ReportExportDetailView.as_view(), name="export_detail"),
    path("reports/exports/<uuid:job_id>/download/", ReportExportDownloadView.as_view(), name="export_download"),
]
