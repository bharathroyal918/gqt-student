from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.contact.models import ContactInquiry

User = get_user_model()


class ContactModelTests(TestCase):
    """Test suite for ContactInquiry helpdesk ticketing model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="inquiry.user@gqt.local", password="Password123!"
        )

    def test_contact_inquiry_creation(self):
        inquiry = ContactInquiry.objects.create(
            user=self.user,
            name="Inquiry User",
            email="inquiry.user@gqt.local",
            subject="Question regarding Loops module",
            category=ContactInquiry.CategoryChoices.COURSE_DOUBT,
            message="Could you provide additional testcases for nested loops?",
            status=ContactInquiry.InquiryStatus.PENDING,
        )
        self.assertEqual(inquiry.status, ContactInquiry.InquiryStatus.PENDING)
        self.assertEqual(
            str(inquiry), "[PENDING] Question regarding Loops module from inquiry.user@gqt.local"
        )
