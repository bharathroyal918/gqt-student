"""Admin URL routes for course management, recorded classes, and student allocations."""

from django.urls import path

from apps.courses.admin_views import (
    CourseAdminDetailUpdateDeleteView,
    CourseAdminListCreateView,
    CourseAdminPublishView,
    CourseEnrollmentAdminAllocateView,
    CourseEnrollmentAdminListView,
    CourseEnrollmentAdminRevokeView,
    CourseRecordedClassAdminDetailView,
    CourseRecordedClassAdminListCreateView,
    CourseRecordedClassReorderView,
)

app_name = "admin_courses"

urlpatterns = [
    # Course Lifecycle
    path("", CourseAdminListCreateView.as_view(), name="list_create"),
    path(
        "<uuid:pk>/",
        CourseAdminDetailUpdateDeleteView.as_view(),
        name="detail_update_delete",
    ),
    path("<uuid:pk>/publish/", CourseAdminPublishView.as_view(), name="publish"),
    # Course Recorded Classes
    path(
        "<uuid:course_id>/recorded-classes/",
        CourseRecordedClassAdminListCreateView.as_view(),
        name="recorded_classes_list_create",
    ),
    path(
        "<uuid:course_id>/recorded-classes/reorder/",
        CourseRecordedClassReorderView.as_view(),
        name="recorded_classes_reorder",
    ),
    path(
        "<uuid:course_id>/recorded-classes/<uuid:video_id>/",
        CourseRecordedClassAdminDetailView.as_view(),
        name="recorded_classes_detail",
    ),
    # Course Student Enrollments / Allocations
    path(
        "<uuid:course_id>/enrollments/",
        CourseEnrollmentAdminListView.as_view(),
        name="enrollments_list",
    ),
    path(
        "<uuid:course_id>/enrollments/allocate/",
        CourseEnrollmentAdminAllocateView.as_view(),
        name="enrollments_allocate",
    ),
    path(
        "<uuid:course_id>/enrollments/<uuid:student_id>/revoke/",
        CourseEnrollmentAdminRevokeView.as_view(),
        name="enrollments_revoke",
    ),
]
