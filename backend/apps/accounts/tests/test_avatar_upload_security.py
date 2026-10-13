"""Tests for SEC-05: Avatar upload raster validation, Pillow decoded content verification, and re-encoding."""

import io
from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.students.models import StudentProfile

User = get_user_model()


class AvatarUploadSecurityTests(TestCase):
    """Test suite verifying strict raster format and image decoding security controls."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="avatar.tester@gqt.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-AV1",
            full_name="Avatar Tester",
        )
        self.client.force_authenticate(user=self.user)
        self.upload_url = reverse("api_v1:auth:avatar_upload")

    def _create_raster_image_bytes(self, fmt="PNG", size=(100, 100), color=(255, 0, 0)):
        buf = io.BytesIO()
        img = Image.new("RGB", size, color)
        img.save(buf, format=fmt)
        buf.seek(0)
        return buf.read()

    def test_valid_png_upload_succeeds_and_reencodes(self):
        """Valid PNG raster image is accepted, re-encoded, and profile updated."""
        png_bytes = self._create_raster_image_bytes("PNG")
        uploaded = SimpleUploadedFile("profile.png", png_bytes, content_type="image/png")

        response = self.client.post(self.upload_url, {"avatar": uploaded}, format="multipart")
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get("data", {})
        assert "avatar_url" in data
        assert data["avatar_url"].endswith((".jpg", ".png"))

    def test_valid_jpeg_upload_succeeds(self):
        """Valid JPEG raster image is accepted and re-encoded."""
        jpeg_bytes = self._create_raster_image_bytes("JPEG")
        uploaded = SimpleUploadedFile("profile.jpg", jpeg_bytes, content_type="image/jpeg")

        response = self.client.post(self.upload_url, {"avatar": uploaded}, format="multipart")
        assert response.status_code == status.HTTP_200_OK
        assert "avatar_url" in response.json().get("data", {})

    def test_svg_upload_is_strictly_rejected(self):
        """SVG vector images must be rejected to prevent Stored XSS."""
        svg_content = b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert('XSS')</script></svg>"
        uploaded = SimpleUploadedFile("avatar.svg", svg_content, content_type="image/svg+xml")

        response = self.client.post(self.upload_url, {"avatar": uploaded}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json().get("error", {}).get("code") == "INVALID_FILE_TYPE"

    def test_renamed_html_payload_is_rejected(self):
        """HTML file renamed with .png extension must be rejected by Pillow verification."""
        html_payload = b"<!DOCTYPE html><html><body><script>alert(1)</script></body></html>"
        uploaded = SimpleUploadedFile("exploit.png", html_payload, content_type="image/png")

        response = self.client.post(self.upload_url, {"avatar": uploaded}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json().get("error", {}).get("code") in ("CORRUPT_IMAGE", "INVALID_IMAGE_FORMAT")

    def test_corrupt_image_bytes_are_rejected(self):
        """Malformed image data must be safely rejected without unhandled exception."""
        corrupt_bytes = b"\x89PNG\r\n\x1a\nCorruptRandomNoiseBytes1234567890"
        uploaded = SimpleUploadedFile("broken.png", corrupt_bytes, content_type="image/png")

        response = self.client.post(self.upload_url, {"avatar": uploaded}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json().get("error", {}).get("code") in ("CORRUPT_IMAGE", "INVALID_IMAGE_FORMAT")

    def test_oversized_file_exceeding_5mb_is_rejected(self):
        """Files exceeding 5 MB must be rejected with FILE_TOO_LARGE."""
        oversized = SimpleUploadedFile("huge.png", b"X" * (5 * 1024 * 1024 + 1), content_type="image/png")

        response = self.client.post(self.upload_url, {"avatar": oversized}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json().get("error", {}).get("code") == "FILE_TOO_LARGE"

    def test_oversized_dimensions_rejected(self):
        """Images with dimensions exceeding 4096px must be rejected."""
        huge_dim_bytes = self._create_raster_image_bytes("JPEG", size=(5000, 100))
        uploaded = SimpleUploadedFile("wide.jpg", huge_dim_bytes, content_type="image/jpeg")

        response = self.client.post(self.upload_url, {"avatar": uploaded}, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json().get("error", {}).get("code") == "IMAGE_TOO_LARGE"
