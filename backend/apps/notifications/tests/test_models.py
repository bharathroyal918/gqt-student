from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications.models import Announcement, Notification

User = get_user_model()


class NotificationModelTests(TestCase):
    """Test suite for Notification and Announcement models."""

    def setUp(self):
        self.user = User.objects.create_user(email="notif.user@gqt.local", password="Password123!")
        self.admin = User.objects.create_superuser(
            email="admin.notif@gqt.local", password="Password123!"
        )

    def test_notification_creation_and_ordering(self):
        notif = Notification.objects.create(
            recipient=self.user,
            title="Module Unlocked",
            body="You have unlocked Module 2: If-Else",
            notification_type=Notification.NotificationType.MODULE_UNLOCKED,
        )
        self.assertFalse(notif.is_read)
        self.assertEqual(notif.recipient, self.user)

    def test_announcement_broadcast(self):
        announcement = Announcement.objects.create(
            title="Scheduled Maintenance Notice",
            content="Platform maintenance at 2 AM IST.",
            priority=Announcement.PriorityChoices.HIGH,
            published_by=self.admin,
        )
        self.assertTrue(announcement.is_active)
        self.assertEqual(str(announcement), "Scheduled Maintenance Notice (Global) [HIGH]")
