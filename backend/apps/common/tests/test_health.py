from unittest.mock import patch

from django.db import DatabaseError
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckTests(APITestCase):
    """Test suite for health check endpoints."""

    def test_overall_health_check_success(self):
        url = "/api/v1/health/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "healthy")
        self.assertEqual(data["data"]["service"], "gqt-student-portal-backend")
        self.assertIn("subsystems", data["data"])
        self.assertEqual(data["data"]["subsystems"]["database"], "healthy")
        self.assertIn("timestamp", data["meta"])

    def test_database_health_check_success(self):
        url = "/api/v1/health/database/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "healthy")
        self.assertIn("latency_ms", data["data"])
        self.assertIn("engine", data["data"])
        self.assertIn("database", data["data"])

    def test_database_health_check_failure(self):
        url = "/api/v1/health/database/"
        with patch("django.db.connection.cursor", side_effect=DatabaseError("DB connection lost")):
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "DATABASE_UNAVAILABLE")
        self.assertIn("DB connection lost", data["error"]["details"]["error"])

    def test_redis_health_check_success(self):
        url = "/api/v1/health/redis/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "healthy")
        self.assertIn("latency_ms", data["data"])
        self.assertIn("backend", data["data"])

    def test_redis_health_check_failure(self):
        url = "/api/v1/health/redis/"
        with patch(
            "django.core.cache.cache.set", side_effect=ConnectionError("Cannot connect to Redis")
        ):
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "REDIS_UNAVAILABLE")
        self.assertIn("Cannot connect to Redis", data["error"]["details"]["error"])
