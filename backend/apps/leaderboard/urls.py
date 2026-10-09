"""URL routing for Student & Public Leaderboard endpoints."""

from django.urls import path

from apps.leaderboard.views import LeaderboardListView, LeaderboardMeView

app_name = "leaderboard"

urlpatterns = [
    path("", LeaderboardListView.as_view(), name="leaderboard_list"),
    path("me/", LeaderboardMeView.as_view(), name="leaderboard_me"),
]
