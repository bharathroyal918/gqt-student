"""Comprehensive Test Suite for Concurrent Login Support, Session Isolation & Health Check Rate-Limit Immunity.

Verifies:
1. Multiple students, TPOs, and admins can authenticate concurrently without blocking or interfering.
2. Token refreshing for User A does not invalidate or overwrite User B's session.
3. Logging out User A does not invalidate User B's active session.
4. Multi-device / multi-session support for the same user account.
5. Cross-user data isolation and TPO multi-college IDOR boundaries.
6. Health check endpoints (/health/live/, /health/ready/, etc.) are immune to DRF rate limiting (no 429s).
"""

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import TPOProfile, User
from apps.students.models import College, StudentProfile


class ConcurrentSessionAndIsolationTests(APITestCase):
    """Verifies concurrency, session isolation, and rate-limit immunity across roles."""

    def setUp(self):
        # Create Colleges
        self.college_a = College.objects.create(
            name="Alpha Engineering Institute",
            code="AEI",
            city="Bengaluru",
            state="Karnataka",
            is_active=True,
        )
        self.college_b = College.objects.create(
            name="Beta Institute of Technology",
            code="BIT",
            city="Hyderabad",
            state="Telangana",
            is_active=True,
        )

        # Create Students
        self.student_a_user = User.objects.create_user(
            email="student_a@example.com",
            password="Password@123",
            mobile_number="9876543210",
            role=User.RoleChoices.STUDENT,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
        )
        self.student_a_profile = StudentProfile.objects.create(
            user=self.student_a_user,
            student_id_number="GQT-STU-001",
            full_name="Student Alpha",
            college=self.college_a,
            college_name=self.college_a.name,
            batch_code="Batch-2026-3",
            graduation_year=2026,
            attendance_percentage=85.0,
            total_points=250.0,
        )

        self.student_b_user = User.objects.create_user(
            email="student_b@example.com",
            password="Password@123",
            mobile_number="9876543211",
            role=User.RoleChoices.STUDENT,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
        )
        self.student_b_profile = StudentProfile.objects.create(
            user=self.student_b_user,
            student_id_number="GQT-STU-002",
            full_name="Student Beta",
            college=self.college_b,
            college_name=self.college_b.name,
            batch_code="Batch-2026-3",
            graduation_year=2026,
            attendance_percentage=72.0,
            total_points=180.0,
        )

        # Create Admin
        self.admin_user = User.objects.create_user(
            email="admin_user@gqt.edu",
            password="Password@123",
            mobile_number="9876543212",
            role=User.RoleChoices.ADMIN,
            is_staff=True,
            is_superuser=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
        )

        # Create TPO Users
        self.tpo_a_user = User.objects.create_user(
            email="tpo_a@alpha.edu",
            password="Password@123",
            mobile_number="9876543213",
            role=User.RoleChoices.TPO,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
        )
        self.tpo_a_profile = TPOProfile.objects.create(
            user=self.tpo_a_user,
            full_name="TPO Officer Alpha",
            designation="Training & Placement Officer",
            department="Placement Cell",
            college=self.college_a,
            is_active=True,
            assigned_by=self.admin_user,
        )

        self.tpo_b_user = User.objects.create_user(
            email="tpo_b@beta.edu",
            password="Password@123",
            mobile_number="9876543214",
            role=User.RoleChoices.TPO,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
        )
        self.tpo_b_profile = TPOProfile.objects.create(
            user=self.tpo_b_user,
            full_name="TPO Officer Beta",
            designation="Training & Placement Officer",
            department="Placement Cell",
            college=self.college_b,
            is_active=True,
            assigned_by=self.admin_user,
        )

    def test_concurrent_logins_for_multiple_students(self):
        """Student A and Student B authenticate simultaneously and receive independent, isolated sessions."""
        resp_a = self.client.post(
            "/api/v1/auth/login/student/",
            {"email": "student_a@example.com", "password": "Password@123"},
        )
        self.assertEqual(resp_a.status_code, status.HTTP_200_OK)
        token_a = resp_a.json()["data"]["access"]

        resp_b = self.client.post(
            "/api/v1/auth/login/student/",
            {"email": "student_b@example.com", "password": "Password@123"},
        )
        self.assertEqual(resp_b.status_code, status.HTTP_200_OK)
        token_b = resp_b.json()["data"]["access"]

        # Both tokens are distinct and independently valid
        self.assertNotEqual(token_a, token_b)

        # Authenticate with Token A -> Returns Student A data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_a}")
        me_a = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me_a.status_code, status.HTTP_200_OK)
        self.assertEqual(me_a.json()["data"]["user"]["email"], "student_a@example.com")
        self.assertEqual(me_a.json()["data"]["user"]["student_profile"]["full_name"], "Student Alpha")

        # Authenticate with Token B -> Returns Student B data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}")
        me_b = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me_b.status_code, status.HTTP_200_OK)
        self.assertEqual(me_b.json()["data"]["user"]["email"], "student_b@example.com")
        self.assertEqual(me_b.json()["data"]["user"]["student_profile"]["full_name"], "Student Beta")

    def test_concurrent_student_admin_and_tpo_sessions(self):
        """Admin, Student, and TPO users operate concurrently without permission or token cross-talk."""
        # 1. Login Admin
        resp_admin = self.client.post(
            "/api/v1/auth/login/admin/",
            {"email": "admin_user@gqt.edu", "password": "Password@123"},
        )
        admin_token = resp_admin.json()["data"]["access"]

        # 2. Login Student
        resp_student = self.client.post(
            "/api/v1/auth/login/student/",
            {"email": "student_a@example.com", "password": "Password@123"},
        )
        student_token = resp_student.json()["data"]["access"]

        # 3. Login TPO
        resp_tpo = self.client.post(
            "/api/v1/auth/login/email/",
            {"email": "tpo_a@alpha.edu", "password": "Password@123"},
        )
        tpo_token = resp_tpo.json()["data"]["access"]

        # Verify Admin has access to admin endpoints
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
        admin_check = self.client.get("/api/v1/admin/students/")
        self.assertEqual(admin_check.status_code, status.HTTP_200_OK)

        # Verify Student has access to student dashboard but is denied admin endpoints
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {student_token}")
        student_dash = self.client.get("/api/v1/students/dashboard/")
        self.assertEqual(student_dash.status_code, status.HTTP_200_OK)
        admin_denied = self.client.get("/api/v1/admin/students/")
        self.assertEqual(admin_denied.status_code, status.HTTP_403_FORBIDDEN)

        # Verify TPO has access to TPO summary
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tpo_token}")
        tpo_summary = self.client.get("/api/v1/tpo/college/summary/")
        self.assertEqual(tpo_summary.status_code, status.HTTP_200_OK)
        self.assertEqual(tpo_summary.json()["data"]["college"]["name"], "Alpha Engineering Institute")

    def test_token_refresh_isolation(self):
        """Rotating User A's token does NOT invalidate or affect User B's active refresh or access tokens."""
        # Log in User A
        resp_a = self.client.post(
            "/api/v1/auth/login/student/",
            {"email": "student_a@example.com", "password": "Password@123"},
        )
        refresh_a = resp_a.json()["data"]["refresh"]

        # Log in User B
        resp_b = self.client.post(
            "/api/v1/auth/login/student/",
            {"email": "student_b@example.com", "password": "Password@123"},
        )
        access_b = resp_b.json()["data"]["access"]
        refresh_b = resp_b.json()["data"]["refresh"]

        # Rotate User A's token
        rotate_resp_a = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": refresh_a},
        )
        self.assertEqual(rotate_resp_a.status_code, status.HTTP_200_OK)
        new_access_a = rotate_resp_a.json()["data"]["access"]

        # User B's access token remains valid and operational
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_b}")
        me_b = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me_b.status_code, status.HTTP_200_OK)
        self.assertEqual(me_b.json()["data"]["user"]["email"], "student_b@example.com")

        # User B's refresh token can also be refreshed independently
        rotate_resp_b = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": refresh_b},
        )
        self.assertEqual(rotate_resp_b.status_code, status.HTTP_200_OK)

    def test_logout_isolation(self):
        """Logging out User A (blacklisting User A's refresh token) does NOT terminate User B's session."""
        # Log in User A and User B
        resp_a = self.client.post(
            "/api/v1/auth/login/student/",
            {"email": "student_a@example.com", "password": "Password@123"},
        )
        refresh_a = resp_a.json()["data"]["refresh"]

        resp_b = self.client.post(
            "/api/v1/auth/login/student/",
            {"email": "student_b@example.com", "password": "Password@123"},
        )
        access_b = resp_b.json()["data"]["access"]
        refresh_b = resp_b.json()["data"]["refresh"]

        # Logout User A
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp_a.json()['data']['access']}")
        logout_a = self.client.post("/api/v1/auth/logout/", {"refresh": refresh_a})
        self.assertEqual(logout_a.status_code, status.HTTP_200_OK)

        # User A's refresh token is blacklisted
        refresh_a_fail = self.client.post("/api/v1/auth/token/refresh/", {"refresh": refresh_a})
        self.assertEqual(refresh_a_fail.status_code, status.HTTP_401_UNAUTHORIZED)

        # User B remains fully logged in and functional
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_b}")
        me_b = self.client.get("/api/v1/auth/me/")
        self.assertEqual(me_b.status_code, status.HTTP_200_OK)
        self.assertEqual(me_b.json()["data"]["user"]["email"], "student_b@example.com")

        # User B can still refresh their token
        refresh_b_ok = self.client.post("/api/v1/auth/token/refresh/", {"refresh": refresh_b})
        self.assertEqual(refresh_b_ok.status_code, status.HTTP_200_OK)

    def test_multi_device_login_for_same_user(self):
        """A user logging in from a second device receives an independent token without terminating device 1."""
        # Device 1 Login
        resp_dev1 = self.client.post(
            "/api/v1/auth/login/student/",
            {"email": "student_a@example.com", "password": "Password@123"},
        )
        access_1 = resp_dev1.json()["data"]["access"]
        refresh_1 = resp_dev1.json()["data"]["refresh"]

        # Device 2 Login
        resp_dev2 = self.client.post(
            "/api/v1/auth/login/student/",
            {"email": "student_a@example.com", "password": "Password@123"},
        )
        access_2 = resp_dev2.json()["data"]["access"]
        refresh_2 = resp_dev2.json()["data"]["refresh"]

        self.assertNotEqual(access_1, access_2)

        # Both devices can fetch profile concurrently
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_1}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, status.HTTP_200_OK)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_2}")
        self.assertEqual(self.client.get("/api/v1/auth/me/").status_code, status.HTTP_200_OK)

        # Logging out Device 1 only terminates Device 1's refresh token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_1}")
        self.client.post("/api/v1/auth/logout/", {"refresh": refresh_1})

        # Device 2 can still refresh its token
        ref2_ok = self.client.post("/api/v1/auth/token/refresh/", {"refresh": refresh_2})
        self.assertEqual(ref2_ok.status_code, status.HTTP_200_OK)

    def test_tpo_multi_college_data_isolation(self):
        """TPO A (College A) and TPO B (College B) operate concurrently with strict college data isolation."""
        # TPO A Login
        resp_tpo_a = self.client.post(
            "/api/v1/auth/login/email/",
            {"email": "tpo_a@alpha.edu", "password": "Password@123"},
        )
        token_tpo_a = resp_tpo_a.json()["data"]["access"]

        # TPO B Login
        resp_tpo_b = self.client.post(
            "/api/v1/auth/login/email/",
            {"email": "tpo_b@beta.edu", "password": "Password@123"},
        )
        token_tpo_b = resp_tpo_b.json()["data"]["access"]

        # TPO A Roster contains only Student A
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_tpo_a}")
        roster_a = self.client.get("/api/v1/tpo/college/students/")
        self.assertEqual(roster_a.status_code, status.HTTP_200_OK)
        student_ids_a = [s["id"] for s in roster_a.json()["data"]]
        self.assertIn(str(self.student_a_profile.id), student_ids_a)
        self.assertNotIn(str(self.student_b_profile.id), student_ids_a)

        # TPO B Roster contains only Student B
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_tpo_b}")
        roster_b = self.client.get("/api/v1/tpo/college/students/")
        self.assertEqual(roster_b.status_code, status.HTTP_200_OK)
        student_ids_b = [s["id"] for s in roster_b.json()["data"]]
        self.assertIn(str(self.student_b_profile.id), student_ids_b)
        self.assertNotIn(str(self.student_a_profile.id), student_ids_b)

        # TPO A cannot access Student B detail (IDOR Protection)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_tpo_a}")
        idor_check = self.client.get(f"/api/v1/tpo/college/students/{self.student_b_profile.id}/")
        self.assertEqual(idor_check.status_code, status.HTTP_404_NOT_FOUND)

    def test_health_check_endpoints_throttle_immunity_high_load(self):
        """Liveness, readiness, and root health check probes tolerate high-frequency polling with zero 429 errors."""
        endpoints = [
            "/health/live/",
            "/health/ready/",
            "/health/",
            "/health/health/live/",
            "/api/v1/health/live/",
        ]
        for url in endpoints:
            for _ in range(50):
                resp = self.client.get(url)
                self.assertEqual(
                    resp.status_code,
                    status.HTTP_200_OK,
                    f"Probe {url} unexpectedly returned status {resp.status_code}",
                )
