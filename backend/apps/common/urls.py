from django.urls import path

from apps.common.health import (
    DatabaseHealthCheckView,
    HealthCheckView,
    LivenessCheckView,
    ReadinessCheckView,
    RedisHealthCheckView,
)

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("health/live/", LivenessCheckView.as_view(), name="health-live"),
    path("health/ready/", ReadinessCheckView.as_view(), name="health-ready"),
    path("health/database/", DatabaseHealthCheckView.as_view(), name="health-database"),
    path("health/redis/", RedisHealthCheckView.as_view(), name="health-redis"),
]
