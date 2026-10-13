"""Tests for CORS preflight, allowed origins, and origin isolation on authentication endpoints."""

import pytest
from django.test import Client, TestCase, override_settings
from django.urls import reverse


class TestCorsPreflightAndAllowedOrigins(TestCase):
    """Verify CORS headers and OPTIONS preflight behavior on authentication endpoints."""

    def setUp(self):
        self.client = Client()
        self.login_url = reverse("api_v1:auth:login_student")

    def test_options_preflight_allowed_origin_127_0_0_1_4173(self):
        """Preflight OPTIONS request from local preview origin http://127.0.0.1:4173 receives CORS headers."""
        response = self.client.options(
            self.login_url,
            HTTP_ORIGIN="http://127.0.0.1:4173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,authorization,x-request-id",
        )

        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:4173"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"
        allow_methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert "POST" in allow_methods
        assert "OPTIONS" in allow_methods
        allow_headers = response.headers.get("Access-Control-Allow-Headers", "").lower()
        assert "content-type" in allow_headers

    def test_options_preflight_allowed_origin_localhost_4173(self):
        """Preflight OPTIONS request from localhost:4173 receives CORS headers."""
        response = self.client.options(
            self.login_url,
            HTTP_ORIGIN="http://localhost:4173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,authorization",
        )

        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:4173"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_options_preflight_disallowed_origin_rejected(self):
        """Preflight OPTIONS request from an unapproved origin receives no Access-Control-Allow-Origin header."""
        response = self.client.options(
            self.login_url,
            HTTP_ORIGIN="http://attacker.example.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,authorization",
        )

        assert "Access-Control-Allow-Origin" not in response.headers

    def test_options_preflight_disallowed_tenant_subdomain_rejected(self):
        """Untrusted tenant or subdomain origin is rejected without CORS header."""
        response = self.client.options(
            self.login_url,
            HTTP_ORIGIN="https://malicious-tenant.onrender.com",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,authorization",
        )

        assert "Access-Control-Allow-Origin" not in response.headers

    def test_post_request_allowed_origin_receives_cors_header(self):
        """Actual POST login request from an allowed origin contains Access-Control-Allow-Origin."""
        response = self.client.post(
            self.login_url,
            data={"email": "nonexistent@gqt.local", "password": "WrongPassword123!"},
            content_type="application/json",
            HTTP_ORIGIN="http://127.0.0.1:4173",
        )

        # Whether authentication succeeds or fails, CORS header must be present for allowed origin
        assert response.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:4173"
        assert response.headers.get("Access-Control-Allow-Credentials") == "true"

    def test_post_request_disallowed_origin_lacks_cors_header(self):
        """POST login request from an unapproved origin lacks Access-Control-Allow-Origin."""
        response = self.client.post(
            self.login_url,
            data={"email": "nonexistent@gqt.local", "password": "WrongPassword123!"},
            content_type="application/json",
            HTTP_ORIGIN="http://evil-site.example.com",
        )

        assert "Access-Control-Allow-Origin" not in response.headers

    @override_settings(CORS_ALLOW_ALL_ORIGINS=False, CORS_ALLOWED_ORIGIN_REGEXES=[])
    def test_wildcard_origins_strictly_disallowed(self):
        """Wildcard origins are not permitted."""
        response = self.client.options(
            self.login_url,
            HTTP_ORIGIN="https://anything.vercel.app",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type",
        )

        assert "Access-Control-Allow-Origin" not in response.headers
