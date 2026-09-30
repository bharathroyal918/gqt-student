"""URL routing for Admin Leaderboard endpoints."""

from django.urls import path
from apps.leaderboard.admin_views import AdminLeaderboardListView

app_name = "admin_leaderboard"

urlpatterns = [
    path("", AdminLeaderboardListView.as_view(), name="admin_leaderboard_list"),
]
