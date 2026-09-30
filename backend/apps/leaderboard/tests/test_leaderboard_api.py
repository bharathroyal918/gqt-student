"""Comprehensive Test Suite for Production-Grade Leaderboard.

Tests:
1. Top 10 Leaderboard & Top 3 highlighting.
2. Current student standing always visible (even if outside Top 10).
3. Nearby ranks (±2) relative to the authenticated student.
4. Deterministic tie-breaking across:
   - Primary: total_points DESC
   - Secondary: solved_questions_count DESC
   - Tertiary: current_streak_days DESC
   - Quaternary: created_at ASC
5. Strict privacy protection: Zero leakage of email, phone, or private data to peer students.
6. /api/v1/leaderboard/me/ dedicated rank endpoint.
7. Filtering by batch code and course.
8. Admin full leaderboard with search, pagination, and RBAC security.
9. Caching and real-time cache invalidation upon score changes.
"""

from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.assignments.models import CodingQuestion, StudentQuestionProgress
from apps.courses.models import Course, CourseEnrollment
from apps.leaderboard.services import LeaderboardService
from apps.modules.models import Module
from apps.scoring.services import ScoringService
from apps.students.models import StudentProfile

User = get_user_model()


class LeaderboardApiTests(TestCase):
    """Test suite for Leaderboard API and Service logic."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()

        # Create Admin
        self.admin_user = User.objects.create_user(
            email="admin.lb@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.ADMIN,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )

        # Create Course & Module
        self.course = Course.objects.create(
            title="Full-Stack Java & Python",
            slug="full-stack-java-python",
            is_published=True,
        )
        self.module = Module.objects.create(
            course=self.course,
            title="Module 01: Core Logic",
            slug="module-01-core-logic",
            order_index=1,
            is_published=True,
        )
        self.question1 = CodingQuestion.objects.create(
            module=self.module,
            title="Q1 Reverse Array",
            slug="q1-reverse-array",
            difficulty=CodingQuestion.DifficultyChoices.EASY,
            problem_statement="Reverse an array of integers.",
            points=Decimal("10.00"),
            is_active=True,
        )
        self.question2 = CodingQuestion.objects.create(
            module=self.module,
            title="Q2 Palindrome String",
            slug="q2-palindrome-string",
            difficulty=CodingQuestion.DifficultyChoices.MEDIUM,
            problem_statement="Check if a string is palindrome.",
            points=Decimal("20.00"),
            is_active=True,
        )
        from apps.projects.models import Project
        self.project = Project.objects.create(
            course=self.course,
            title="Capstone E-Commerce Platform",
            slug="capstone-ecommerce",
            max_score=Decimal("100.00"),
            description="Build an e-commerce platform.",
            deliverables_instructions="Submit GitHub repo and demo link.",
            is_active=True,
        )

    def _create_student(
        self,
        email_suffix: str,
        full_name: str,
        total_points: float,
        streak_days: int = 1,
        batch_code: str = "BATCH-2026-A",
        created_delta_minutes: int = 0,
    ) -> tuple[User, StudentProfile]:
        user = User.objects.create_user(
            email=f"stu.{email_suffix}@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        profile = StudentProfile.objects.create(
            user=user,
            student_id_number=f"GQT-{email_suffix.upper()}",
            full_name=full_name,
            batch_code=batch_code,
            total_points=Decimal(str(total_points)),
            current_streak_days=streak_days,
            highest_streak_days=streak_days,
        )
        if created_delta_minutes != 0:
            # Shift created_at deterministically
            StudentProfile.objects.filter(id=profile.id).update(
                created_at=timezone.now() + timedelta(minutes=created_delta_minutes)
            )
            profile.refresh_from_db()

        # Enroll in course
        CourseEnrollment.objects.create(
            student=profile,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )
        return user, profile

    def test_top_10_and_top_3_highlighting_with_student_outside_top_10(self):
        """Create 15 students and verify Top 10 with Top 3 highlighted, plus rank 15 visibility."""
        students = []
        for i in range(1, 16):
            # Points from 150 down to 10
            u, p = self._create_student(
                email_suffix=f"s{i:02d}",
                full_name=f"Student {i:02d}",
                total_points=160 - (i * 10),
            )
            students.append((u, p))

        # Authenticate as student #15 (rank 15, lowest score)
        user_15, profile_15 = students[14]
        self.client.force_authenticate(user=user_15)

        response = self.client.get("/api/v1/leaderboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]

        # Top 10 validation
        top_10 = data["top_10"]
        self.assertEqual(len(top_10), 10)
        self.assertEqual(top_10[0]["rank"], 1)
        self.assertTrue(top_10[0]["is_top_3"])
        self.assertTrue(top_10[1]["is_top_3"])
        self.assertTrue(top_10[2]["is_top_3"])
        self.assertFalse(top_10[3]["is_top_3"])
        self.assertFalse(top_10[9]["is_top_3"])

        # Current student standing (Rank 15 outside Top 10)
        curr = data["current_student"]
        self.assertEqual(curr["rank"], 15)
        self.assertEqual(curr["student_id"], str(profile_15.id))
        self.assertFalse(curr["is_in_top_10"])
        self.assertEqual(curr["total_participants"], 15)

        # Nearby students (±2 around rank 15 -> rank 13, 14, 15)
        nearby = data["nearby_students"]
        nearby_ranks = [s["rank"] for s in nearby]
        self.assertIn(13, nearby_ranks)
        self.assertIn(14, nearby_ranks)
        self.assertIn(15, nearby_ranks)

    def test_deterministic_tie_breaking_rules(self):
        """Verify strict 4-tier deterministic tie-breaking.

        Tier 1: total_points DESC
        Tier 2: solved_questions_count DESC
        Tier 3: current_streak_days DESC
        Tier 4: created_at ASC
        """
        # 4 students with identical total_points = 50.0
        u1, p1 = self._create_student("tie1", "Student Alpha", 50.0, streak_days=2, created_delta_minutes=0)
        u2, p2 = self._create_student("tie2", "Student Beta", 50.0, streak_days=5, created_delta_minutes=0)
        u3, p3 = self._create_student("tie3", "Student Gamma", 50.0, streak_days=2, created_delta_minutes=-30)  # Registered earlier
        u4, p4 = self._create_student("tie4", "Student Delta", 50.0, streak_days=2, created_delta_minutes=30)   # Registered later

        # Student Alpha solved 2 questions
        StudentQuestionProgress.objects.create(
            student=p1, question=self.question1, is_solved=True, best_score=Decimal("10.0")
        )
        StudentQuestionProgress.objects.create(
            student=p1, question=self.question2, is_solved=True, best_score=Decimal("20.0")
        )

        # Student Beta, Gamma, Delta solved 0 questions
        # Expected Rankings:
        # Rank 1: p1 (Alpha) -> solved 2 questions (Tier 2 winner)
        # Rank 2: p2 (Beta)  -> streak 5 vs 2 (Tier 3 winner)
        # Rank 3: p3 (Gamma) -> streak 2, created 30m earlier than Delta (Tier 4 winner)
        # Rank 4: p4 (Delta) -> streak 2, created later

        self.client.force_authenticate(user=u1)
        response = self.client.get("/api/v1/leaderboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        top_10 = response.json()["data"]["top_10"]

        ranked_ids = [entry["student_id"] for entry in top_10]
        self.assertEqual(
            ranked_ids,
            [str(p1.id), str(p2.id), str(p3.id), str(p4.id)],
            "Tie-breaking did not resolve in deterministic order [Alpha, Beta, Gamma, Delta].",
        )

    def test_student_privacy_isolation(self):
        """Ensure Student A cannot access private fields (email, phone, etc.) of Student B in leaderboard."""
        u1, p1 = self._create_student("alice", "Alice Wonder", 100.0)
        u2, p2 = self._create_student("bob", "Bob Builder", 90.0)

        self.client.force_authenticate(user=u1)
        response = self.client.get("/api/v1/leaderboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        top_10 = response.json()["data"]["top_10"]
        for entry in top_10:
            self.assertNotIn("email", entry)
            self.assertNotIn("phone_number", entry)
            self.assertNotIn("parent_phone", entry)
            self.assertNotIn("college_name", entry)
            self.assertIn("rank", entry)
            self.assertIn("full_name", entry)
            self.assertIn("total_points", entry)

    def test_leaderboard_me_endpoint(self):
        """Test GET /api/v1/leaderboard/me/ returns exact student standing."""
        u1, p1 = self._create_student("me1", "Solo Student", 75.0, streak_days=4)
        self.client.force_authenticate(user=u1)

        response = self.client.get("/api/v1/leaderboard/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]

        self.assertEqual(data["student_id"], str(p1.id))
        self.assertEqual(data["rank"], 1)
        self.assertEqual(data["total_points"], 75.0)
        self.assertEqual(data["current_streak_days"], 4)
        self.assertTrue(data["is_current_student"])

    def test_batch_and_course_filtering(self):
        """Test filtering by batch code and course."""
        u_a1, p_a1 = self._create_student("a1", "Batch A Top", 100.0, batch_code="BATCH-ALPHA")
        u_b1, p_b1 = self._create_student("b1", "Batch B Top", 200.0, batch_code="BATCH-BETA")

        # Request with batch_code filter BATCH-ALPHA
        self.client.force_authenticate(user=u_a1)
        response = self.client.get("/api/v1/leaderboard/?batch_code=BATCH-ALPHA")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        top_10 = response.json()["data"]["top_10"]

        self.assertEqual(len(top_10), 1)
        self.assertEqual(top_10[0]["student_id"], str(p_a1.id))
        self.assertEqual(top_10[0]["rank"], 1)

    def test_admin_leaderboard_access_and_filtering(self):
        """Admin can access full leaderboard with search and contact info, whereas students get 403."""
        u1, p1 = self._create_student("stud_adm", "Admin Target Student", 120.0)

        # Student cannot access admin leaderboard
        self.client.force_authenticate(user=u1)
        response_forbidden = self.client.get("/api/v1/admin/leaderboard/")
        self.assertEqual(response_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # Admin can access admin leaderboard
        self.client.force_authenticate(user=self.admin_user)
        response_admin = self.client.get("/api/v1/admin/leaderboard/?search=Target")
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)
        results = response_admin.json()
        
        # Paginated standardized response envelope
        items = results.get("data", results)
        self.assertTrue(len(items) >= 1)
        self.assertEqual(items[0]["email"], u1.email)
        self.assertEqual(items[0]["student_id_number"], p1.student_id_number)

    def test_cache_invalidation_after_score_change(self):
        """Ensure leaderboard updates immediately in real-time when a score change occurs."""
        u1, p1 = self._create_student("c1", "Rank 1 Initially", 100.0)
        u2, p2 = self._create_student("c2", "Rank 2 Initially", 50.0)

        self.client.force_authenticate(user=u2)
        # 1. First fetch populates cache
        r1 = self.client.get("/api/v1/leaderboard/")
        self.assertEqual(r1.json()["data"]["top_10"][0]["student_id"], str(p1.id))

        # 2. Award 20 marks to p2 via ScoringService
        ScoringService.evaluate_assignment_submission(
            student=p2,
            question_id=str(self.question2.id),
            question_title=self.question2.title,
            passed_test_cases=5,
            total_test_cases=5,
            max_points=Decimal("20.00"),
            awarded_by=self.admin_user,
        )
        p2.refresh_from_db()
        self.assertEqual(float(p2.total_points), 70.0)  # 50 + 20 from Q2

        # Award another assignment to increase score
        ScoringService.evaluate_assignment_submission(
            student=p2,
            question_id=str(self.question1.id),
            question_title=self.question1.title,
            passed_test_cases=5,
            total_test_cases=5,
            max_points=Decimal("10.00"),
            awarded_by=self.admin_user,
        )
        p2.refresh_from_db()
        self.assertEqual(float(p2.total_points), 80.0)

        # Add project marks to reach 160 (surpassing p1's 100)
        ScoringService.evaluate_project_submission(
            student=p2,
            project_id=str(self.project.id),
            project_title=self.project.title,
            score=Decimal("80.00"),
            max_score=Decimal("100.00"),
            awarded_by=self.admin_user,
            feedback_notes="Mastery level project",
        )
        p2.refresh_from_db()
        self.assertEqual(float(p2.total_points), 160.0)

        # 3. Next fetch without stale cache must show p2 at Rank 1
        r2 = self.client.get("/api/v1/leaderboard/")
        top_10_updated = r2.json()["data"]["top_10"]
        self.assertEqual(top_10_updated[0]["student_id"], str(p2.id))
        self.assertEqual(top_10_updated[0]["rank"], 1)
        self.assertEqual(top_10_updated[1]["student_id"], str(p1.id))
        self.assertEqual(top_10_updated[1]["rank"], 2)
