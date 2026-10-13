"""Tests for SEC-06 (Resume URL & Open Redirect) and SEC-09 (Resume Upload Restrictions)."""

import io
import zipfile
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.placements.models import PlacementApplication, PlacementDrive
from apps.students.models import StudentProfile

User = get_user_model()


class ResumeUploadAndRedirectSecurityTests(TestCase):
    """Test suite verifying file upload constraints and open redirect mitigations."""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="applicant.security@gqt.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.profile = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-SEC-APP",
            full_name="Security Applicant",
        )
        self.client.force_authenticate(user=self.user)

        self.drive = PlacementDrive.objects.create(
            company_name="SafeCorp",
            role="Backend Engineer",
            skills="Python, Django",
            location="Bengaluru",
            stipend_or_ctc="12 LPA",
            job_description="Secure coding role",
            status=PlacementDrive.DriveStatus.ONGOING,
            application_deadline=timezone.now() + timezone.timedelta(days=30),
        )
        self.apply_url = reverse(
            "api_v1:student_placement_apply", kwargs={"drive_id": self.drive.id}
        )

    def _make_valid_docx_bytes(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("[Content_Types].xml", b"<Types></Types>")
            zf.writestr("word/document.xml", b"<w:document></w:document>")
        buf.seek(0)
        return buf.read()

    # =========================================================================
    # SEC-09: RESUME UPLOAD RESTRICTIONS
    # =========================================================================

    def test_oversized_resume_file_is_rejected(self):
        """Resume file exceeding 10 MB must be rejected."""
        oversized = SimpleUploadedFile(
            "large_resume.pdf",
            b"%PDF-" + b"A" * (10 * 1024 * 1024 + 5),
            content_type="application/pdf",
        )
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_file": oversized,
        }
        res = self.client.post(self.apply_url, payload, format="multipart")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "resume_file" in res.json().get("error", {}).get("details", {})

    def test_unsupported_resume_extension_is_rejected(self):
        """Executable or script extensions must be strictly rejected."""
        executable = SimpleUploadedFile(
            "resume.exe",
            b"MZ\x90\x00BinaryContent",
            content_type="application/octet-stream",
        )
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_file": executable,
        }
        res = self.client.post(self.apply_url, payload, format="multipart")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_spoofed_pdf_signature_mismatch_is_rejected(self):
        """File with .pdf extension lacking %PDF- signature must be rejected."""
        fake_pdf = SimpleUploadedFile(
            "resume.pdf",
            b"#!/bin/bash\necho Malicious\n",
            content_type="application/pdf",
        )
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_file": fake_pdf,
        }
        res = self.client.post(self.apply_url, payload, format="multipart")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_corrupt_docx_archive_is_rejected(self):
        """Corrupt DOCX archive lacking Word components must be rejected."""
        broken_docx = SimpleUploadedFile(
            "resume.docx",
            b"PK\x03\x04BrokenZipContent",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_file": broken_docx,
        }
        res = self.client.post(self.apply_url, payload, format="multipart")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_valid_pdf_upload_succeeds(self):
        """Valid PDF resume file upload is accepted."""
        valid_pdf = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF",
            content_type="application/pdf",
        )
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_file": valid_pdf,
        }
        res = self.client.post(self.apply_url, payload, format="multipart")
        assert res.status_code == status.HTTP_201_CREATED

    def test_valid_docx_upload_succeeds(self):
        """Valid DOCX resume file upload is accepted."""
        valid_docx = SimpleUploadedFile(
            "resume.docx",
            self._make_valid_docx_bytes(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_file": valid_docx,
        }
        res = self.client.post(self.apply_url, payload, format="multipart")
        assert res.status_code == status.HTTP_201_CREATED

    # =========================================================================
    # SEC-06: RESUME URL AND OPEN REDIRECT CONTROLS
    # =========================================================================

    def test_javascript_resume_url_is_rejected(self):
        """javascript: URI schemes must be rejected."""
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_url": "javascript:alert(document.cookie)",
        }
        res = self.client.post(self.apply_url, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_data_resume_url_is_rejected(self):
        """data: URI schemes must be rejected."""
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_url": "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
        }
        res = self.client.post(self.apply_url, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_https_resume_url_is_rejected(self):
        """Non-HTTPS URLs must be rejected."""
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_url": "http://drive.google.com/file/d/123/view",
        }
        res = self.client.post(self.apply_url, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_deceptive_hostname_is_rejected(self):
        """Deceptive domains masquerading as trusted providers must be rejected."""
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_url": "https://drive.google.com.phishing.attacker.com/doc",
        }
        res = self.client.post(self.apply_url, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_unapproved_external_domain_is_rejected(self):
        """Unapproved external domains must be rejected."""
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_url": "https://evil-unapproved.com/resume",
        }
        res = self.client.post(self.apply_url, payload)
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_approved_google_drive_resume_url_is_accepted(self):
        """Approved Google Drive resume URLs are accepted."""
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_url": "https://drive.google.com/file/d/1B2C3D4E5F/view?usp=sharing",
        }
        res = self.client.post(self.apply_url, payload)
        assert res.status_code == status.HTTP_201_CREATED

    def test_approved_onedrive_resume_url_is_accepted(self):
        """Approved OneDrive resume URLs are accepted."""
        drive2 = PlacementDrive.objects.create(
            company_name="CloudCorp",
            role="Cloud Architect",
            skills="AWS, Azure",
            location="Bengaluru",
            stipend_or_ctc="15 LPA",
            job_description="Cloud role",
            status=PlacementDrive.DriveStatus.ONGOING,
            application_deadline=timezone.now() + timezone.timedelta(days=30),
        )
        url2 = reverse("api_v1:student_placement_apply", kwargs={"drive_id": drive2.id})
        payload = {
            "phone_number": "9876543210",
            "cgpa_or_percentage": "8.5",
            "resume_url": "https://onedrive.live.com/view.aspx?cid=123&resid=456",
        }
        res = self.client.post(url2, payload)
        assert res.status_code == status.HTTP_201_CREATED

    def test_download_endpoint_redirects_for_safe_external_url(self):
        """PlacementResumeDownloadView redirects to approved safe external URLs."""
        app = PlacementApplication.objects.create(
            drive=self.drive,
            student=self.profile,
            student_name="Security Applicant",
            student_id_number="GQT-STU-SEC-APP",
            email=self.user.email,
            resume_url="https://drive.google.com/file/d/safe-resume-id/view",
        )
        dl_url = reverse("api_v1:placement_resume_download", kwargs={"application_id": app.id})
        res = self.client.get(dl_url)
        assert res.status_code == status.HTTP_302_FOUND
        assert res.url == "https://drive.google.com/file/d/safe-resume-id/view"

    def test_download_endpoint_blocks_unsafe_legacy_external_url(self):
        """PlacementResumeDownloadView refuses open redirect to unapproved legacy URL."""
        app = PlacementApplication.objects.create(
            drive=self.drive,
            student=self.profile,
            student_name="Security Applicant",
            student_id_number="GQT-STU-SEC-APP",
            email=self.user.email,
            resume_url="https://phishing.malicious-site.com/exploit",
        )
        dl_url = reverse("api_v1:placement_resume_download", kwargs={"application_id": app.id})
        res = self.client.get(dl_url)
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert res.json().get("error", {}).get("code") == "UNSAFE_RESUME_URL"
