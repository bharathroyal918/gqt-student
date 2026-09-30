"""Admin URL routes for assignment and test case management."""

from django.urls import path

from apps.assignments.admin_views import (
    CodingQuestionAdminDetailUpdateDeleteView,
    CodingQuestionAdminListCreateView,
    TestCaseAdminCreateView,
    TestCaseAdminDetailUpdateDeleteView,
)

app_name = "admin_assignments"

urlpatterns = [
    path("questions/", CodingQuestionAdminListCreateView.as_view(), name="question_list_create"),
    path(
        "questions/<uuid:pk>/",
        CodingQuestionAdminDetailUpdateDeleteView.as_view(),
        name="question_detail_update_delete",
    ),
    path(
        "questions/<uuid:pk>/testcases/",
        TestCaseAdminCreateView.as_view(),
        name="testcase_create",
    ),
    path(
        "testcases/<uuid:pk>/",
        TestCaseAdminDetailUpdateDeleteView.as_view(),
        name="testcase_detail_update_delete",
    ),
]
