import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError, connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.common.responses import api_error, api_success
from apps.common.throttling import HealthCheckThrottle

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """GET /api/v1/health/

    Overall health probe verifying web service vitality and subsystem statuses.
    """

    permission_classes = [AllowAny]
    throttle_classes = [HealthCheckThrottle]

    def get(self, request, *args, **kwargs):
        # 1. Probe database
        db_healthy = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                db_healthy = row == (1,)
        except Exception as e:
            logger.warning(f"Health probe database check failed: {e}")
            db_healthy = False

        # 2. Probe Redis
        redis_healthy = False
        try:
            cache.set("__health_probe_ping__", "pong", timeout=5)
            redis_healthy = cache.get("__health_probe_ping__") == "pong"
        except Exception as e:
            logger.warning(f"Health probe Redis check failed: {e}")
            redis_healthy = False

        overall_status = "healthy" if db_healthy else "degraded"
        status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

        return api_success(
            data={
                "status": overall_status,
                "service": "gqt-student-portal-backend",
                "environment": getattr(settings, "ENVIRONMENT", "development"),
                "version": getattr(request, "version", "v1") or "v1",
                "subsystems": {
                    "database": "healthy" if db_healthy else "unhealthy",
                    "redis": "healthy" if redis_healthy else "unhealthy",
                },
            },
            status_code=status_code,
        )


class DatabaseHealthCheckView(APIView):
    """GET /api/v1/health/database/

    Targeted database probe measuring query round-trip latency and verifying schema connectivity.
    """

    permission_classes = [AllowAny]
    throttle_classes = [HealthCheckThrottle]

    def get(self, request, *args, **kwargs):
        start_time = time.perf_counter()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                if row != (1,):
                    raise DatabaseError("Database did not return expected verification tuple.")

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            db_engine = settings.DATABASES["default"]["ENGINE"]
            db_name = settings.DATABASES["default"].get("NAME", "unknown")

            return api_success(
                data={
                    "status": "healthy",
                    "engine": db_engine,
                    "database": str(db_name),
                    "latency_ms": latency_ms,
                }
            )
        except Exception as exc:
            logger.error(f"Database health check failed: {exc}", exc_info=exc)
            return api_error(
                code="DATABASE_UNAVAILABLE",
                message="Database connectivity check failed.",
                details={"error": str(exc)},
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class RedisHealthCheckView(APIView):
    """GET /api/v1/health/redis/

    Targeted Redis cache probe measuring read/write latency.
    """

    permission_classes = [AllowAny]
    throttle_classes = [HealthCheckThrottle]

    def get(self, request, *args, **kwargs):
        start_time = time.perf_counter()
        probe_key = f"__redis_health_probe_{int(time.time())}__"
        probe_val = "ok"

        try:
            cache.set(probe_key, probe_val, timeout=5)
            retrieved = cache.get(probe_key)
            if retrieved != probe_val:
                raise ConnectionError("Redis cache write succeeded but value verification failed.")

            cache.delete(probe_key)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

            return api_success(
                data={
                    "status": "healthy",
                    "backend": settings.CACHES["default"]["BACKEND"],
                    "latency_ms": latency_ms,
                }
            )
        except Exception as exc:
            logger.error(f"Redis health check failed: {exc}", exc_info=exc)
            return api_error(
                code="REDIS_UNAVAILABLE",
                message="Redis connectivity check failed.",
                details={"error": str(exc)},
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class LivenessCheckView(APIView):
    """GET /api/v1/health/live/
    
    Fast, lightweight liveness probe for container orchestrators (Kubernetes/Docker).
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return api_success(data={"status": "alive", "timestamp": int(time.time())})


class ReadinessCheckView(APIView):
    """GET /api/v1/health/ready/
    
    Readiness probe verifying DB and cache connectivity before routing live traffic.
    """

    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                if cursor.fetchone() != (1,):
                    raise DatabaseError("Database unavailable")
            cache.set("__readiness_ping__", "1", timeout=5)
            if cache.get("__readiness_ping__") != "1":
                raise ConnectionError("Cache unavailable")
            return api_success(data={"status": "ready", "ready": True})
        except Exception as exc:
            return api_error(
                code="SERVICE_NOT_READY",
                message="Service not ready to accept traffic.",
                details={"error": str(exc)},
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

