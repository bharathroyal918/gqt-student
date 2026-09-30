from rest_framework import status
from rest_framework.test import APITestCase


class MiddlewareTests(APITestCase):
    """Test suite for RequestIDMiddleware and tracing headers."""

    def test_request_id_generated_when_absent(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response header
        self.assertIn("X-Request-ID", response.headers)
        request_id = response.headers["X-Request-ID"]
        self.assertTrue(len(request_id) > 10)

        # Check response JSON meta
        data = response.json()
        self.assertEqual(data["meta"]["request_id"], request_id)

    def test_request_id_preserved_when_present(self):
        custom_id = "test-custom-trace-uuid-12345"
        response = self.client.get("/api/v1/health/", HTTP_X_REQUEST_ID=custom_id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.headers["X-Request-ID"], custom_id)
        data = response.json()
        self.assertEqual(data["meta"]["request_id"], custom_id)
