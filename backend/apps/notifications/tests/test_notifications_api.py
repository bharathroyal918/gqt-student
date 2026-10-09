"""Comprehensive test suite for Notifications, Announcements, Idempotency, and Async Email delivery."""

import smtplib
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Course, CourseEnrollment
from apps.notifications.models import Announcement, Notification
from apps.notifications.services import NotificationService
from apps.notifications.tasks import _deliver_email_worker
from apps.students.models import StudentProfile

User = get_user_model()


class NotificationsAndAnnouncementsApiTests(APITestCase):
    """Test suite covering notifications, unread counts, idempotency, audience resolution, and admin management."""

    def setUp(self):
        cache.clear()

        # Admin user
        self.admin_user = User.objects.create_superuser(
            email="admin.notif@gqt.local", password="AdminPassword123!"
        )

        # Student A (Batch Alpha, enrolled in Course 1)
        self.user_a = User.objects.create_user(
            email="bharath.student@gqt.local",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
        )
        self.student_a = StudentProfile.objects.create(
            user=self.user_a,
            student_id_number="GQT-STU-ALPHA-1",
            full_name="Bharath Royal",
            batch_code="BATCH-ALPHA",
        )

        # Student B (Batch Beta, not enrolled in Course 1)
        self.user_b = User.objects.create_user(
            email="bob.student@gqt.local",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
        )
        self.student_b = StudentProfile.objects.create(
            user=self.user_b,
            student_id_number="GQT-STU-BETA-2",
            full_name="Bob Beta",
            batch_code="BATCH-BETA",
        )

        # Course setup
        self.course = Course.objects.create(
            title="Advanced Python Architecture",
            slug="advanced-python-arch",
            description="Complete mastery of Python",
            is_published=True,
        )
        CourseEnrollment.objects.create(
            student=self.student_a,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )

    def test_student_notifications_list_and_unread_count(self):
        """Student retrieves their notification feed and live unread count."""
        # Create 2 unread notifications and 1 read notification for Student A
        _n1 = Notification.objects.create(
            recipient=self.user_a,
            title="Task Deadline Approaching",
            body="Daily Challenge #4 is due in 2 hours.",
            notification_type=Notification.NotificationType.TASK_DEADLINE,
            is_read=False,
        )
        _n2 = Notification.objects.create(
            recipient=self.user_a,
            title="Project Graded",
            body="Your capstone submission received 10.00 marks.",
            notification_type=Notification.NotificationType.PROJECT_MARKED,
            is_read=False,
        )
        _n3 = Notification.objects.create(
            recipient=self.user_a,
            title="Achievement Unlocked",
            body="Earned 'Fast Learner' badge!",
            notification_type=Notification.NotificationType.ACHIEVEMENT,
            is_read=True,
            read_at=timezone.now(),
        )
        # Notification for Student B (should not appear for Student A)
        Notification.objects.create(
            recipient=self.user_b,
            title="Bob's Private Alert",
            body="Private alert for Bob.",
            notification_type=Notification.NotificationType.SYSTEM_NOTICE,
        )

        self.client.force_authenticate(user=self.user_a)

        # 1. Unread count
        count_res = self.client.get("/api/v1/students/notifications/unread-count/")
        self.assertEqual(count_res.status_code, status.HTTP_200_OK)
        self.assertEqual(count_res.json()["data"]["unread_count"], 2)

        # 2. List notifications
        list_res = self.client.get("/api/v1/students/notifications/")
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        data = list_res.json()["data"]
        self.assertEqual(data["count"], 3)
        self.assertEqual(data["unread_count"], 2)

        # 3. Filter unread only
        unread_res = self.client.get("/api/v1/students/notifications/?is_read=false")
        self.assertEqual(unread_res.status_code, status.HTTP_200_OK)
        self.assertEqual(unread_res.json()["data"]["count"], 2)

    def test_mark_single_notification_read_and_authorization(self):
        """Student marks their notification read; access is isolated from other students."""
        notif_a = Notification.objects.create(
            recipient=self.user_a,
            title="Module Unlocked",
            body="Module 3 Loops is now available.",
            notification_type=Notification.NotificationType.MODULE_UNLOCKED,
            is_read=False,
        )

        # Student B attempts to mark Student A's notification read
        self.client.force_authenticate(user=self.user_b)
        res_b = self.client.post(f"/api/v1/students/notifications/{notif_a.id}/read/")
        self.assertIn(
            res_b.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )

        # Student A marks their own notification read
        self.client.force_authenticate(user=self.user_a)
        res_a = self.client.post(f"/api/v1/students/notifications/{notif_a.id}/read/")
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        self.assertTrue(res_a.json()["data"]["notification"]["is_read"])
        self.assertEqual(res_a.json()["data"]["unread_count"], 0)

        notif_a.refresh_from_db()
        self.assertTrue(notif_a.is_read)
        self.assertIsNotNone(notif_a.read_at)

    def test_mark_all_notifications_read(self):
        """Student marks all unread notifications read in bulk."""
        for i in range(5):
            Notification.objects.create(
                recipient=self.user_a,
                title=f"Notification #{i}",
                body="Test body",
                is_read=False,
            )

        self.client.force_authenticate(user=self.user_a)
        res = self.client.post("/api/v1/students/notifications/mark-all-read/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.json()["data"]["updated_count"], 5)
        self.assertEqual(res.json()["data"]["unread_count"], 0)

        unread_remaining = Notification.objects.filter(
            recipient=self.user_a, is_read=False
        ).count()
        self.assertEqual(unread_remaining, 0)

    def test_notification_idempotency_duplicate_prevention(self):
        """Repeated events with the same idempotency key do not produce duplicate notifications."""
        key = "task_deadline_2026_09_30_student_a"

        # 1. First event
        notif1 = NotificationService.send_notification(
            recipient=self.user_a,
            title="Approaching Deadline",
            body="Your task is due soon.",
            notification_type=Notification.NotificationType.TASK_DEADLINE,
            idempotency_key=key,
        )

        # 2. Repeated trigger (e.g. background cron re-run)
        notif2 = NotificationService.send_notification(
            recipient=self.user_a,
            title="Approaching Deadline",
            body="Your task is due soon.",
            notification_type=Notification.NotificationType.TASK_DEADLINE,
            idempotency_key=key,
        )

        self.assertEqual(notif1.id, notif2.id)
        self.assertEqual(Notification.objects.filter(recipient=self.user_a).count(), 1)

    @patch("apps.notifications.tasks.send_mail")
    def test_async_email_worker_and_retry(self, mock_send_mail):
        """Async email delivery worker marks notification email_sent on success and handles retries."""
        notif = Notification.objects.create(
            recipient=self.user_a,
            title="Rank Change Alert",
            body="Congratulations! You climbed to Rank #1 on the leaderboard.",
            notification_type=Notification.NotificationType.RANK_CHANGE,
        )

        # 1. Successful email delivery simulation
        mock_send_mail.return_value = 1
        success = _deliver_email_worker(str(notif.id), max_retries=2)
        self.assertTrue(success)

        notif.refresh_from_db()
        self.assertTrue(notif.email_sent)
        self.assertIsNotNone(notif.email_sent_at)
        mock_send_mail.assert_called_once()

        # 2. Failure & retry simulation
        mock_send_mail.reset_mock()
        mock_send_mail.side_effect = smtplib.SMTPException("SMTP Connection Timeout")
        notif_fail = Notification.objects.create(
            recipient=self.user_a,
            title="System Alert",
            body="System maintenance tonight.",
        )
        fail_res = _deliver_email_worker(
            str(notif_fail.id), max_retries=2, base_delay=0.01
        )
        self.assertFalse(fail_res)
        self.assertEqual(mock_send_mail.call_count, 2)

    def test_admin_announcement_target_audience_resolution(self):
        """Admin creates announcements with different audiences; proper student fan-out is verified."""
        self.client.force_authenticate(user=self.admin_user)

        # 1. Global Announcement (All Students)
        res_global = self.client.post(
            "/api/v1/admin/announcements/",
            {
                "title": "Hackathon 2026 Registration Open",
                "content": "Sign up for the annual GQT Hackathon!",
                "target_audience": "ALL",
                "priority": "HIGH",
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(res_global.status_code, status.HTTP_201_CREATED)
        # Both Student A and Student B should receive notification
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user_a, title__contains="Hackathon 2026"
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user_b, title__contains="Hackathon 2026"
            ).exists()
        )

        # 2. Batch-Specific Announcement (BATCH-ALPHA only)
        res_batch = self.client.post(
            "/api/v1/admin/announcements/",
            {
                "title": "Alpha Batch Exclusive Workshop",
                "content": "Special Q&A session for Batch Alpha.",
                "target_audience": "BATCH",
                "target_batch": "BATCH-ALPHA",
                "priority": "NORMAL",
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(res_batch.status_code, status.HTTP_201_CREATED)
        # Student A receives it; Student B does not
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user_a, title__contains="Alpha Batch Exclusive"
            ).exists()
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.user_b, title__contains="Alpha Batch Exclusive"
            ).exists()
        )

        # 3. Course-Specific Announcement (Advanced Python Architecture only)
        res_course = self.client.post(
            "/api/v1/admin/announcements/",
            {
                "title": "Course Update: Python 3.13 Features Added",
                "content": "New modules added to your curriculum.",
                "target_audience": "COURSE",
                "target_course_id": str(self.course.id),
                "priority": "NORMAL",
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(res_course.status_code, status.HTTP_201_CREATED)
        # Student A is enrolled and receives it; Student B is not enrolled and does not
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user_a, title__contains="Python 3.13"
            ).exists()
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.user_b, title__contains="Python 3.13"
            ).exists()
        )

    def test_student_announcements_feed(self):
        """Student retrieves relevant active announcements."""
        ann_global = Announcement.objects.create(
            title="Global Campus News",
            content="Campus library open 24/7.",
            target_audience="ALL",
            published_by=self.admin_user,
            is_published=True,
            is_active=True,
        )
        ann_beta = Announcement.objects.create(
            title="Beta Batch Notice",
            content="Beta batch schedule.",
            target_audience="BATCH",
            target_batch="BATCH-BETA",
            published_by=self.admin_user,
            is_published=True,
            is_active=True,
        )

        # Student A (Alpha batch) gets global but not Beta
        self.client.force_authenticate(user=self.user_a)
        res_a = self.client.get("/api/v1/students/notifications/announcements/")
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        ann_ids_a = [a["id"] for a in res_a.json()["data"]["announcements"]]
        self.assertIn(str(ann_global.id), ann_ids_a)
        self.assertNotIn(str(ann_beta.id), ann_ids_a)

    def test_admin_announcement_audit_history(self):
        """Admin can inspect audit logs for an announcement."""
        self.client.force_authenticate(user=self.admin_user)
        create_res = self.client.post(
            "/api/v1/admin/announcements/",
            {
                "title": "Audit Test Announcement",
                "content": "Content for audit test",
                "target_audience": "ALL",
                "priority": "URGENT",
                "is_published": True,
            },
            format="json",
        )
        ann_id = create_res.json()["data"]["id"]

        audit_res = self.client.get(f"/api/v1/admin/announcements/{ann_id}/audit/")
        self.assertEqual(audit_res.status_code, status.HTTP_200_OK)
        logs = audit_res.json()["data"]["audit_logs"]
        self.assertTrue(len(logs) >= 1)
        actions = [l["action"] for l in logs]
        self.assertIn("ANNOUNCEMENT_CREATED", actions)
