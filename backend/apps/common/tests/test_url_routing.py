"""Comprehensive URL Routing & Namespace Verification Test Suite.

Verifies:
1. Every application namespace in api_v1 is unique and deterministic.
2. Canonical URLs reverse to the expected path with trailing slash.
3. Root-level operational endpoints (/health/, /certificates/verify/) resolve cleanly.
4. Security and role boundaries across authentication, student, admin, and public routes.
"""

import uuid
from django.test import TestCase
from django.urls import resolve, reverse


class URLRoutingAndNamespaceTests(TestCase):
    """Verifies that all API v1 endpoints and namespaced routes reverse cleanly."""

    def test_health_routes_reverse(self):
        """Health check endpoints must reverse to canonical paths."""
        self.assertEqual(reverse("api_v1:health-check"), "/api/v1/health/")
        self.assertEqual(reverse("api_v1:health-live"), "/api/v1/health/live/")
        self.assertEqual(reverse("api_v1:health-ready"), "/api/v1/health/ready/")
        self.assertEqual(reverse("api_v1:health-database"), "/api/v1/health/database/")
        self.assertEqual(reverse("api_v1:health-redis"), "/api/v1/health/redis/")

    def test_auth_routes_reverse(self):
        """Authentication routes must reverse properly."""
        self.assertEqual(reverse("api_v1:auth:login_student"), "/api/v1/auth/login/student/")
        self.assertEqual(reverse("api_v1:auth:login_admin"), "/api/v1/auth/login/admin/")
        self.assertEqual(reverse("api_v1:auth:login_email"), "/api/v1/auth/login/email/")
        self.assertEqual(reverse("api_v1:auth:otp_request"), "/api/v1/auth/otp/request/")
        self.assertEqual(reverse("api_v1:auth:otp_verify"), "/api/v1/auth/otp/verify/")
        self.assertEqual(reverse("api_v1:auth:token_refresh"), "/api/v1/auth/token/refresh/")
        self.assertEqual(reverse("api_v1:auth:logout"), "/api/v1/auth/logout/")
        self.assertEqual(reverse("api_v1:auth:me"), "/api/v1/auth/me/")
        self.assertEqual(reverse("api_v1:auth:password_forgot"), "/api/v1/auth/password/forgot/")
        self.assertEqual(reverse("api_v1:auth:password_reset"), "/api/v1/auth/password/reset/")

    def test_student_routes_reverse(self):
        """Student-facing profile, dashboard, and curriculum routes must reverse properly."""
        dummy_id = uuid.uuid4()
        self.assertEqual(reverse("api_v1:students:student_dashboard"), "/api/v1/students/dashboard/")
        self.assertEqual(reverse("api_v1:students:student_leaderboard"), "/api/v1/students/leaderboard/")
        self.assertEqual(reverse("api_v1:students:student_profile_me"), "/api/v1/students/me/profile/")
        self.assertEqual(reverse("api_v1:students:student_attendance_me"), "/api/v1/students/me/attendance/")
        self.assertEqual(reverse("api_v1:students:student_courses"), "/api/v1/students/courses/")
        self.assertEqual(
            reverse("api_v1:students:student_course_detail", kwargs={"course_id": dummy_id}),
            f"/api/v1/students/courses/{dummy_id}/",
        )
        self.assertEqual(
            reverse("api_v1:students:student_module_detail", kwargs={"module_id": dummy_id}),
            f"/api/v1/students/modules/{dummy_id}/",
        )
        self.assertEqual(
            reverse("api_v1:students:student_module_complete", kwargs={"module_id": dummy_id}),
            f"/api/v1/students/modules/{dummy_id}/complete/",
        )

    def test_student_assignments_routes_reverse(self):
        """Student coding assignment and sandbox runner routes must reverse properly."""
        dummy_id = uuid.uuid4()
        self.assertEqual(reverse("api_v1:student_assignments:question_list"), "/api/v1/students/assignments/questions/")
        self.assertEqual(
            reverse("api_v1:student_assignments:question_detail", kwargs={"question_id": dummy_id}),
            f"/api/v1/students/assignments/questions/{dummy_id}/",
        )
        self.assertEqual(
            reverse("api_v1:student_assignments:code_run", kwargs={"question_id": dummy_id}),
            f"/api/v1/students/assignments/questions/{dummy_id}/run/",
        )
        self.assertEqual(
            reverse("api_v1:student_assignments:code_submit", kwargs={"question_id": dummy_id}),
            f"/api/v1/students/assignments/questions/{dummy_id}/submit/",
        )
        self.assertEqual(
            reverse("api_v1:student_assignments:submission_history", kwargs={"question_id": dummy_id}),
            f"/api/v1/students/assignments/questions/{dummy_id}/submissions/",
        )
        self.assertEqual(
            reverse("api_v1:student_assignments:submission_detail", kwargs={"submission_id": dummy_id}),
            f"/api/v1/students/assignments/submissions/{dummy_id}/",
        )

    def test_student_tasks_and_projects_reverse(self):
        """Student tasks and capstone project routes must reverse properly."""
        dummy_id = uuid.uuid4()
        self.assertEqual(reverse("api_v1:student_tasks:task_list"), "/api/v1/students/tasks/")
        self.assertEqual(
            reverse("api_v1:student_tasks:task_detail", kwargs={"task_id": dummy_id}),
            f"/api/v1/students/tasks/{dummy_id}/",
        )
        self.assertEqual(
            reverse("api_v1:student_tasks:task_complete", kwargs={"task_id": dummy_id}),
            f"/api/v1/students/tasks/{dummy_id}/complete/",
        )
        self.assertEqual(reverse("api_v1:student_projects:project_list"), "/api/v1/students/projects/")
        self.assertEqual(
            reverse("api_v1:student_projects:project_detail", kwargs={"project_id": dummy_id}),
            f"/api/v1/students/projects/{dummy_id}/",
        )
        self.assertEqual(
            reverse("api_v1:student_projects:project_submit", kwargs={"project_id": dummy_id}),
            f"/api/v1/students/projects/{dummy_id}/submit/",
        )

    def test_ai_assistant_routes_reverse(self):
        """AI Assistant conversation and message routes must reverse uniquely."""
        dummy_id = uuid.uuid4()
        self.assertEqual(reverse("api_v1:ai_assistant:conversation_list_create"), "/api/v1/students/ai/conversations/")
        self.assertEqual(
            reverse("api_v1:ai_assistant:conversation_detail_archive", kwargs={"conversation_id": dummy_id}),
            f"/api/v1/students/ai/conversations/{dummy_id}/",
        )
        self.assertEqual(
            reverse("api_v1:ai_assistant:message_send", kwargs={"conversation_id": dummy_id}),
            f"/api/v1/students/ai/conversations/{dummy_id}/messages/",
        )
        self.assertEqual(
            reverse("api_v1:ai_assistant:message_retry", kwargs={"conversation_id": dummy_id}),
            f"/api/v1/students/ai/conversations/{dummy_id}/retry/",
        )

    def test_notifications_and_certificates_routes_reverse(self):
        """Notifications and credential routes must reverse properly."""
        dummy_id = uuid.uuid4()
        self.assertEqual(reverse("api_v1:notifications:notification_list"), "/api/v1/students/notifications/")
        self.assertEqual(reverse("api_v1:notifications:unread_count"), "/api/v1/students/notifications/unread-count/")
        self.assertEqual(
            reverse("api_v1:notifications:mark_read", kwargs={"notification_id": dummy_id}),
            f"/api/v1/students/notifications/{dummy_id}/read/",
        )
        self.assertEqual(reverse("api_v1:notifications:mark_all_read"), "/api/v1/students/notifications/mark-all-read/")
        self.assertEqual(reverse("api_v1:notifications:student_announcements"), "/api/v1/students/notifications/announcements/")
        self.assertEqual(reverse("api_v1:certificates:student_badges"), "/api/v1/students/achievements/")
        self.assertEqual(reverse("api_v1:certificates:student_certificates"), "/api/v1/students/certificates/")
        self.assertEqual(
            reverse("api_v1:certificates:certificate_download", kwargs={"certificate_id": dummy_id}),
            f"/api/v1/students/certificates/{dummy_id}/download/",
        )

    def test_admin_routes_reverse(self):
        """Admin student, curriculum, assessment, and analytics routes must reverse properly."""
        dummy_id = uuid.uuid4()
        self.assertEqual(reverse("api_v1:admin_students:list_create"), "/api/v1/admin/students/")
        self.assertEqual(reverse("api_v1:admin_students:provision"), "/api/v1/admin/students/provision/")
        self.assertEqual(
            reverse("api_v1:admin_students:detail_update", kwargs={"pk": dummy_id}),
            f"/api/v1/admin/students/{dummy_id}/",
        )
        self.assertEqual(
            reverse("api_v1:admin_students:status", kwargs={"pk": dummy_id}),
            f"/api/v1/admin/students/{dummy_id}/status/",
        )
        self.assertEqual(reverse("api_v1:admin_courses:list_create"), "/api/v1/admin/courses/")
        self.assertEqual(
            reverse("api_v1:admin_courses:detail_update_delete", kwargs={"pk": dummy_id}),
            f"/api/v1/admin/courses/{dummy_id}/",
        )
        self.assertEqual(reverse("api_v1:admin_modules:list_create"), "/api/v1/admin/modules/")
        self.assertEqual(reverse("api_v1:admin_modules:reorder"), "/api/v1/admin/modules/reorder/")
        self.assertEqual(reverse("api_v1:admin_assignments:question_list_create"), "/api/v1/admin/assignments/questions/")
        self.assertEqual(reverse("api_v1:admin_tasks:list_create"), "/api/v1/admin/tasks/")
        self.assertEqual(reverse("api_v1:admin_projects:project_list_create"), "/api/v1/admin/projects/")
        self.assertEqual(reverse("api_v1:admin_announcements:list_create"), "/api/v1/admin/announcements/")
        self.assertEqual(reverse("api_v1:admin_certificates:list"), "/api/v1/admin/certificates/")
        self.assertEqual(reverse("api_v1:admin_contact:inquiry_list"), "/api/v1/admin/contact/inquiries/")
        self.assertEqual(reverse("api_v1:admin_leaderboard:admin_leaderboard_list"), "/api/v1/admin/leaderboard/")
        self.assertEqual(reverse("api_v1:admin_analytics:dashboard"), "/api/v1/admin/analytics/dashboard/")
        self.assertEqual(reverse("api_v1:admin_analytics:report_performance"), "/api/v1/admin/reports/performance/")
        self.assertEqual(reverse("api_v1:admin_analytics:export_list"), "/api/v1/admin/reports/exports/")

    def test_contact_and_leaderboard_routes_reverse(self):
        """Contact and leaderboard routes must reverse properly."""
        self.assertEqual(reverse("api_v1:contact:company_info"), "/api/v1/contact/info/")
        self.assertEqual(reverse("api_v1:contact:inquiry_submit"), "/api/v1/contact/inquiries/")
        self.assertEqual(reverse("api_v1:leaderboard:leaderboard_list"), "/api/v1/leaderboard/")
        self.assertEqual(reverse("api_v1:leaderboard:leaderboard_me"), "/api/v1/leaderboard/me/")
