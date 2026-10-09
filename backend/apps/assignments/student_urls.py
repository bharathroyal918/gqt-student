"""URL configuration for student coding practice platform."""

from django.urls import path

from apps.assignments.student_views import (
    StudentCodeRunView,
    StudentCodeSubmitView,
    StudentQuestionDetailView,
    StudentQuestionListView,
    StudentSubmissionDetailView,
    StudentSubmissionHistoryView,
)

app_name = "student_assignments"

urlpatterns = [
    path("questions/", StudentQuestionListView.as_view(), name="question_list"),
    path(
        "questions/<uuid:question_id>/",
        StudentQuestionDetailView.as_view(),
        name="question_detail",
    ),
    path(
        "questions/<uuid:question_id>/run/",
        StudentCodeRunView.as_view(),
        name="code_run",
    ),
    path(
        "questions/<uuid:question_id>/submit/",
        StudentCodeSubmitView.as_view(),
        name="code_submit",
    ),
    path(
        "questions/<uuid:question_id>/submissions/",
        StudentSubmissionHistoryView.as_view(),
        name="submission_history",
    ),
    path(
        "submissions/<uuid:submission_id>/",
        StudentSubmissionDetailView.as_view(),
        name="submission_detail",
    ),
]
