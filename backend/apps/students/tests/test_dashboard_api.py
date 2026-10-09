"""Comprehensive API test suite for Student Dashboard and Leaderboard.

Tests:
- Student A cannot see Student B's dashboard
- Logout / Login as another student
- Refresh live score and rank calculation
- Browser reopen session hydration
- Token refresh flow
- Concurrent requests execution
- Unauthenticated rejection
- Admin without student profile rejection
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.notifications.models import Notification
from apps.students.models import StudentProfile

User = get_user_model()


class StudentDashboardApiTests(TestCase):
    """Test suite for Student Dashboard data isolation, ownership, and live recalculations."""

    def setUp(self):
        cache.clear()
        self.client_a = APIClient()
        self.client_b = APIClient()

        # Create Course & Module
        self.course = Course.objects.create(
            title="Full Stack Cloud & DevOps",
            slug="full-stack-cloud-devops",
            is_published=True,
        )
        self.module = Module.objects.create(
            course=self.course,
            title="Module 1: Core Fundamentals",
            slug="module-1-core-fundamentals",
            order_index=1,
            is_published=True,
        )

        # Create Student A
        self.user_a = User.objects.create_user(
            email="student.a@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.profile_a = StudentProfile.objects.create(
            user=self.user_a,
            student_id_number="GQT-STU-001",
            full_name="Alice Student",
            batch_code="BATCH-2026-A",
            total_points=Decimal("350.00"),
            current_streak_days=5,
            highest_streak_days=7,
        )
        CourseEnrollment.objects.create(
            student=self.profile_a,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )
        StudentModuleProgress.objects.create(
            student=self.profile_a,
            module=self.module,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
        )
        Notification.objects.create(
            recipient=self.user_a,
            title="Welcome to Full Stack",
            body="Your cohort starts today.",
        )

        # Create Student B
        self.user_b = User.objects.create_user(
            email="student.b@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.profile_b = StudentProfile.objects.create(
            user=self.user_b,
            student_id_number="GQT-STU-002",
            full_name="Bob Learner",
            batch_code="BATCH-2026-B",
            total_points=Decimal("600.00"),
            current_streak_days=12,
            highest_streak_days=15,
        )
        Notification.objects.create(
            recipient=self.user_b,
            title="Assignment Feedback",
            body="Bob, your submission scored 100/100.",
        )

        # Authenticate clients
        self.client_a.force_authenticate(user=self.user_a)
        self.client_b.force_authenticate(user=self.user_b)
        self.dashboard_url = reverse("api_v1:students:student_dashboard")

    def test_student_a_cannot_see_student_b(self):
        """Student A calling dashboard receives ONLY Student A's data, never Student B's."""
        response_a = self.client_a.get(self.dashboard_url)
        self.assertEqual(response_a.status_code, status.HTTP_200_OK)
        data_a = response_a.data["data"]

        # Profile verification
        self.assertEqual(data_a["profile"]["id"], str(self.profile_a.id))
        self.assertEqual(data_a["profile"]["full_name"], "Alice Student")
        self.assertEqual(data_a["profile"]["email"], "student.a@gqt.edu")
        self.assertEqual(data_a["profile"]["total_score"], 350.0)
        self.assertEqual(data_a["profile"]["course"], "Full Stack Cloud & DevOps")
        self.assertEqual(data_a["profile"]["completed_modules"], 1)

        # Notifications verification
        notifs = data_a["activity"]["notifications"]
        self.assertEqual(len(notifs), 1)
        self.assertEqual(notifs[0]["title"], "Welcome to Full Stack")

        # Attempt to spoof/tamper by passing Student B's ID in query params
        tampered_url = f"{self.dashboard_url}?student_id={self.profile_b.id}&user_id={self.user_b.id}"
        tampered_res = self.client_a.get(tampered_url)
        self.assertEqual(tampered_res.status_code, status.HTTP_200_OK)
        tampered_data = tampered_res.data["data"]

        # Backend MUST ignore foreign parameters and still serve Student A
        self.assertEqual(tampered_data["profile"]["id"], str(self.profile_a.id))
        self.assertEqual(tampered_data["profile"]["full_name"], "Alice Student")
        self.assertNotEqual(tampered_data["profile"]["id"], str(self.profile_b.id))

    def test_logout_and_login_as_another_student(self):
        """Logging out Student A and logging in as Student B completely switches rendered dashboard data."""
        client = APIClient()

        # Step 1: Login as Student A
        login_res_a = client.post(
            reverse("api_v1:auth:login_email"),
            {"email": "student.a@gqt.edu", "password": "SecurePassword123!"},
            format="json",
        )
        self.assertEqual(login_res_a.status_code, status.HTTP_200_OK)
        token_a = login_res_a.data["data"]["access"]
        refresh_a = login_res_a.data["data"]["refresh"]

        # Fetch dashboard as Student A
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_a}")
        dash_a = client.get(self.dashboard_url)
        self.assertEqual(dash_a.status_code, status.HTTP_200_OK)
        self.assertEqual(dash_a.data["data"]["profile"]["full_name"], "Alice Student")

        # Step 2: Logout Student A
        logout_res = client.post(
            reverse("api_v1:auth:logout"),
            {"refresh": refresh_a},
            format="json",
        )
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        # Clear credentials
        client.credentials()

        # Step 3: Login as Student B
        login_res_b = client.post(
            reverse("api_v1:auth:login_email"),
            {"email": "student.b@gqt.edu", "password": "SecurePassword123!"},
            format="json",
        )
        self.assertEqual(login_res_b.status_code, status.HTTP_200_OK)
        token_b = login_res_b.data["data"]["access"]

        # Fetch dashboard with Student B's token
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_b}")
        dash_b = client.get(self.dashboard_url)
        self.assertEqual(dash_b.status_code, status.HTTP_200_OK)
        self.assertEqual(dash_b.data["data"]["profile"]["full_name"], "Bob Learner")
        self.assertEqual(dash_b.data["data"]["profile"]["total_score"], 600.0)
        self.assertEqual(
            dash_b.data["data"]["leaderboard"]["current_student"]["rank"], 1
        )

    def test_refresh_dashboard_live_score(self):
        """When student score updates, refetched dashboard immediately reflects new score and rank."""
        # Initial rank: Bob is 1st (600 pts), Alice is 2nd (350 pts)
        initial_dash = self.client_a.get(self.dashboard_url)
        self.assertEqual(initial_dash.data["data"]["profile"]["current_rank"], 2)

        # Award 500 points to Alice -> 850 total points (overtaking Bob)
        self.profile_a.total_points = Decimal("850.00")
        self.profile_a.save(update_fields=["total_points"])

        # Refetch dashboard
        refreshed_dash = self.client_a.get(self.dashboard_url)
        self.assertEqual(refreshed_dash.status_code, status.HTTP_200_OK)
        self.assertEqual(refreshed_dash.data["data"]["profile"]["total_score"], 850.0)
        self.assertEqual(refreshed_dash.data["data"]["profile"]["current_rank"], 1)
        self.assertEqual(
            refreshed_dash.data["data"]["leaderboard"]["top_10"][0]["student_id"],
            str(self.profile_a.id),
        )

    def test_browser_reopen_and_session_continuity(self):
        """Simulates browser reopen: client reuses valid token and hydrates /me and dashboard."""
        client = APIClient()
        login_res = client.post(
            reverse("api_v1:auth:login_email"),
            {"email": "student.a@gqt.edu", "password": "SecurePassword123!"},
            format="json",
        )
        token = login_res.data["data"]["access"]

        # Simulate fresh browser session with stored access token
        new_session_client = APIClient()
        new_session_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        # Hydrate user
        me_res = new_session_client.get(reverse("api_v1:auth:me"))
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        self.assertEqual(me_res.data["data"]["user"]["email"], "student.a@gqt.edu")

        # Hydrate dashboard
        dash_res = new_session_client.get(self.dashboard_url)
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        self.assertEqual(dash_res.data["data"]["profile"]["full_name"], "Alice Student")

    def test_token_refresh_flow(self):
        """Access token refreshed via /token/refresh/ maintains seamless dashboard access."""
        client = APIClient()
        login_res = client.post(
            reverse("api_v1:auth:login_email"),
            {"email": "student.b@gqt.edu", "password": "SecurePassword123!"},
            format="json",
        )
        refresh_token = login_res.data["data"]["refresh"]

        # Refresh access token
        refresh_res = client.post(
            reverse("api_v1:auth:token_refresh"),
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        new_access = refresh_res.data["data"]["access"]

        # Access dashboard using new access token
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access}")
        dash_res = client.get(self.dashboard_url)
        self.assertEqual(dash_res.status_code, status.HTTP_200_OK)
        self.assertEqual(dash_res.data["data"]["profile"]["full_name"], "Bob Learner")

    def test_concurrent_dashboard_requests(self):
        """Simulates parallel concurrent dashboard queries without data race or crosstalk."""
        # Execute rapid sequential & parallel-simulated queries across both students
        responses_a = [self.client_a.get(self.dashboard_url) for _ in range(5)]
        responses_b = [self.client_b.get(self.dashboard_url) for _ in range(5)]

        for res in responses_a:
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data["data"]["profile"]["full_name"], "Alice Student")

        for res in responses_b:
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data["data"]["profile"]["full_name"], "Bob Learner")

    def test_unauthenticated_request_rejected(self):
        """Unauthenticated requests to student dashboard are rejected with 401."""
        anon_client = APIClient()
        res = anon_client.get(self.dashboard_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_without_student_profile_rejected(self):
        """Admin users without an active student profile receive 403 Forbidden."""
        admin = User.objects.create_user(
            email="admin@gqt.edu",
            password="AdminPassword123!",
            role=User.RoleChoices.ADMIN,
            is_staff=True,
        )
        admin_client = APIClient()
        admin_client.force_authenticate(user=admin)
        res = admin_client.get(self.dashboard_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
