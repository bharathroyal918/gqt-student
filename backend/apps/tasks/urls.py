"""URL routing for Student-Facing Daily Tasks."""

from django.urls import path
from apps.tasks.views import (
    StudentTaskCompleteView,
    StudentTaskDetailView,
    StudentTaskListView,
)

app_name = "student_tasks"

urlpatterns = [
    path("", StudentTaskListView.as_view(), name="task_list"),
    path("<uuid:task_id>/", StudentTaskDetailView.as_view(), name="task_detail"),
    path("<uuid:task_id>/complete/", StudentTaskCompleteView.as_view(), name="task_complete"),
]
