"""Tests for SEC-13: Certificate verification rate limiting and throttle scope isolation."""

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import ScopedRateThrottle

from apps.certificates.views import PublicCertificateVerifyView


class CertificateVerifyThrottlingTests(TestCase):
    """SEC-13: Verify rate-limiting on public certificate verification."""

    def setUp(self):
        self.client = APIClient()
        self.verify_url = reverse("api_v1:public_cert_verify", kwargs={"identifier": "NON-EXISTENT-ID"})

    def test_cert_verify_throttle_configuration(self):
        """Verify endpoint uses throttle_scope = 'cert_verify' and rate is configured in settings."""
        assert PublicCertificateVerifyView.throttle_scope == "cert_verify"
        assert ScopedRateThrottle in PublicCertificateVerifyView.throttle_classes
        assert "cert_verify" in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]

    def test_cert_verify_rate_limiting_enforcement_returns_429(self):
        """Exceeding cert_verify throttle limit returns HTTP 429 Too Many Requests."""
        orig_rate = ScopedRateThrottle.THROTTLE_RATES.get("cert_verify")
        cache.clear()
        ScopedRateThrottle.THROTTLE_RATES["cert_verify"] = "2/minute"
        try:
            # First 2 requests pass through to view (returns 404 for non-existent cert)
            res1 = self.client.get(self.verify_url)
            assert res1.status_code == status.HTTP_404_NOT_FOUND

            res2 = self.client.get(self.verify_url)
            assert res2.status_code == status.HTTP_404_NOT_FOUND

            # 3rd request exceeds limit
            res3 = self.client.get(self.verify_url)
            assert res3.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        finally:
            cache.clear()
            if orig_rate is not None:
                ScopedRateThrottle.THROTTLE_RATES["cert_verify"] = orig_rate
            else:
                ScopedRateThrottle.THROTTLE_RATES.pop("cert_verify", None)

    def test_cert_verify_throttle_does_not_affect_unrelated_endpoints(self):
        """Exhausting cert_verify throttle limit does NOT block unrelated endpoints."""
        orig_rate = ScopedRateThrottle.THROTTLE_RATES.get("cert_verify")
        cache.clear()
        ScopedRateThrottle.THROTTLE_RATES["cert_verify"] = "1/minute"
        try:
            res1 = self.client.get(self.verify_url)
            assert res1.status_code == status.HTTP_404_NOT_FOUND

            # Second cert verify is blocked
            res2 = self.client.get(self.verify_url)
            assert res2.status_code == status.HTTP_429_TOO_MANY_REQUESTS

            # Unrelated endpoint (e.g. public colleges) is NOT blocked
            colleges_url = reverse("api_v1:students:public_colleges_list")
            unrelated_res = self.client.get(colleges_url)
            assert unrelated_res.status_code == status.HTTP_200_OK
        finally:
            cache.clear()
            if orig_rate is not None:
                ScopedRateThrottle.THROTTLE_RATES["cert_verify"] = orig_rate
            else:
                ScopedRateThrottle.THROTTLE_RATES.pop("cert_verify", None)
