"""Comprehensive test suite for Contact Module, Company Info, Rate Limiting, Anti-Spam, and Admin Workflows."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.contact.models import ContactInquiry

User = get_user_model()


class ContactModuleApiTests(APITestCase):
    """Test suite covering contact info, inquiry validation, rate limiting, anti-spam, and admin ticket resolution."""

    def setUp(self):
        cache.clear()

        # 1. Admin User
        self.admin_user = User.objects.create_superuser(
            email="admin.contact@gqt.local", password="AdminPassword123!"
        )

        # 2. Student User
        self.student_user = User.objects.create_user(
            email="student.contact@gqt.local", password="Password123!", role=User.RoleChoices.STUDENT
        )

    def test_get_company_info_public(self):
        """Public endpoint returns institutional contact info, addresses, and social links."""
        res = self.client.get("/api/v1/contact/info/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.json()["data"]
        self.assertIn("company_name", data)
        self.assertIn("support_email", data)
        self.assertIn("phone_primary", data)
        self.assertIn("office_address", data)
        self.assertIn("social_links", data)
        self.assertEqual(data["office_address"]["city"], "Bengaluru")
        self.assertIn("linkedin", data["social_links"])

    def test_submit_contact_inquiry_valid(self):
        """Student/user submits valid contact inquiry and receives sanitized confirmation."""
        payload = {
            "name": "Bharath Kumar",
            "email": "bharath@example.com",
            "subject": "Sequential Module Access Query",
            "category": ContactInquiry.CategoryChoices.COURSE_DOUBT,
            "message": "I would like to clarify prerequisite unlock criteria for Module 12.",
        }

        res = self.client.post("/api/v1/contact/inquiries/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        data = res.json()["data"]
        self.assertEqual(data["name"], "Bharath Kumar")
        self.assertEqual(data["email"], "bharath@example.com")
        self.assertEqual(data["category"], "COURSE_DOUBT")
        self.assertNotIn("admin_notes", data)  # Never expose private admin notes

        inquiry = ContactInquiry.objects.get(id=data["id"])
        self.assertEqual(inquiry.status, ContactInquiry.InquiryStatus.PENDING)

    def test_submit_contact_inquiry_validation_errors(self):
        """Validation errors returned for malformed email, short message, or short name."""
        payload = {
            "name": "A",  # Too short (< 2 chars)
            "email": "invalid-email-string",
            "subject": "Hi",  # Too short (< 3 chars)
            "message": "short",  # Too short (< 10 chars)
        }

        res = self.client.post("/api/v1/contact/inquiries/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        err_details = res.json()["error"]["details"]
        self.assertIn("name", err_details)
        self.assertIn("email", err_details)
        self.assertIn("subject", err_details)
        self.assertIn("message", err_details)

    def test_anti_spam_honeypot_blocking(self):
        """Bot automated submissions that fill out the hidden honeypot field are blocked."""
        payload = {
            "name": "Automated Spammer",
            "email": "spammer@botnet.test",
            "subject": "Cheap SEO Services",
            "message": "Visit our website for high ranking SEO packages now.",
            "website": "http://spam-link.test",  # Honeypot filled
        }

        res = self.client.post("/api/v1/contact/inquiries/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(ContactInquiry.objects.filter(email="spammer@botnet.test").exists())

    def test_submission_rate_limiting(self):
        """Rate limiting restricts more than 5 submissions within the 10-minute window."""
        payload = {
            "name": "Repeat Submitter",
            "email": "repeat@example.com",
            "subject": "Support Ticket",
            "message": "Detailed support inquiry text for checking rate limiting.",
        }

        # First 5 submissions succeed
        for i in range(5):
            res = self.client.post(
                "/api/v1/contact/inquiries/", payload, format="json", REMOTE_ADDR="198.51.100.1"
            )
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # 6th submission is throttled
        res_blocked = self.client.post(
            "/api/v1/contact/inquiries/", payload, format="json", REMOTE_ADDR="198.51.100.1"
        )
        self.assertEqual(res_blocked.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_blocked.json()["error"]["code"], "SUBMISSION_BLOCKED")
        self.assertIn("limit", res_blocked.json()["error"]["message"])

    def test_admin_inquiry_listing_and_ticket_resolution(self):
        """Admin views submitted tickets and updates status with notes."""
        inquiry = ContactInquiry.objects.create(
            name="Alice Student",
            email="alice.test@gqt.local",
            subject="IDE Theme Customization",
            category=ContactInquiry.CategoryChoices.TECHNICAL_SUPPORT,
            message="How do I switch the IDE color theme in the portal?",
        )

        self.client.force_authenticate(user=self.admin_user)

        # 1. List inquiries
        list_res = self.client.get("/api/v1/admin/contact/inquiries/")
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.json()["data"]["inquiries"]), 1)

        # 2. Update status to RESOLVED with notes
        update_payload = {
            "status": ContactInquiry.InquiryStatus.RESOLVED,
            "admin_notes": "Replied via email explaining Monaco editor settings.",
        }
        patch_res = self.client.patch(
            f"/api/v1/admin/contact/inquiries/{inquiry.id}/",
            update_payload,
            format="json",
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)

        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, ContactInquiry.InquiryStatus.RESOLVED)
        self.assertEqual(inquiry.resolved_by, self.admin_user)
        self.assertIsNotNone(inquiry.resolved_at)
        self.assertEqual(inquiry.admin_notes, "Replied via email explaining Monaco editor settings.")

    def test_student_cannot_access_admin_contact_inquiries(self):
        """Students are strictly forbidden from accessing admin contact tickets."""
        self.client.force_authenticate(user=self.student_user)

        res = self.client.get("/api/v1/admin/contact/inquiries/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
