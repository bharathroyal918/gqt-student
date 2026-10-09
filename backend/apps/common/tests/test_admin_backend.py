"""Comprehensive test suite for the complete Admin Backend.

Tests every endpoint, business flow, and permission boundary across:
1. Student Management
2. Course Management
3. Module Management & Reordering
4. Assignment & Test Case Management
5. Task Management
6. Capstone Project Management & Grading
7. Announcement Broadcasts
8. Analytics & Executive Reports
"""

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.services import AuthService
from apps.assignments.models import TestCase as CodingTestCase
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module
from apps.notifications.models import Announcement
from apps.projects.models import Project, ProjectFeedback, ProjectSubmission
from apps.scoring.models import ScoreRecord
from apps.students.models import StudentProfile
from apps.tasks.models import Task

User = get_user_model()


class AdminBackendIntegrationTests(TestCase):
    """End-to-end integration tests for all administrative endpoints and permission boundaries."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()

        # Admin user
        self.admin_user = User.objects.create_user(
            email="admin.lead@gqt.edu",
            password="AdminPassword123!",
            role=User.RoleChoices.ADMIN,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        self.admin_token, _ = AuthService.issue_tokens_for_user(self.admin_user)

        # Student user
        self.student_user = User.objects.create_user(
            email="student.john@gqt.edu",
            mobile_number="+919876540001",
            password="StudentPass123!",
            role=User.RoleChoices.STUDENT,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
            is_active=True,
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id_number="GQT-STU-101",
            full_name="John Doe",
            batch_code="PY-2026-B1",
            total_points=Decimal("150.00"),
        )
        self.student_token, _ = AuthService.issue_tokens_for_user(self.student_user)

    def _auth_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.admin_token}")

    def _auth_student(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.student_token}")

    # =========================================================================
    # 1. STUDENT MANAGEMENT
    # =========================================================================

    def test_student_list_and_search(self):
        self._auth_admin()
        url = reverse("api_v1:admin_students:list_create")

        # Test listing
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertGreaterEqual(len(response.data["data"]), 1)

        # Test search
        search_resp = self.client.get(f"{url}?search=John")
        self.assertEqual(search_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(search_resp.data["data"]), 1)
        self.assertEqual(search_resp.data["data"][0]["full_name"], "John Doe")

    def test_student_detail_and_update(self):
        self._auth_admin()
        url = reverse(
            "api_v1:admin_students:detail_update",
            kwargs={"pk": self.student_profile.id},
        )

        # Detail
        get_resp = self.client.get(url)
        self.assertEqual(get_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(get_resp.data["data"]["full_name"], "John Doe")

        # Update
        patch_resp = self.client.patch(
            url,
            {
                "full_name": "Jonathan Doe",
                "batch_code": "PY-2026-ADV",
                "is_active": True,
                "onboarding_status": "ACTIVE",
            },
            format="json",
        )
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.full_name, "Jonathan Doe")
        self.assertEqual(self.student_profile.batch_code, "PY-2026-ADV")

    def test_student_assign_courses(self):
        course = Course.objects.create(title="Python Full Stack", slug="python-fs")
        self._auth_admin()

        url = reverse(
            "api_v1:admin_students:assign_courses",
            kwargs={"pk": self.student_profile.id},
        )
        response = self.client.post(
            url, {"course_ids": [str(course.id)]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            CourseEnrollment.objects.filter(
                student=self.student_profile,
                course=course,
                status=CourseEnrollment.EnrollmentStatus.ACTIVE,
            ).exists()
        )

    def test_student_progress_scores_and_rank(self):
        self._auth_admin()
        pk = self.student_profile.id

        # Progress
        prog_url = reverse("api_v1:admin_students:progress", kwargs={"pk": pk})
        prog_resp = self.client.get(prog_url)
        self.assertEqual(prog_resp.status_code, status.HTTP_200_OK)
        self.assertIn("overview", prog_resp.data["data"])

        # Scores
        scores_url = reverse("api_v1:admin_students:scores", kwargs={"pk": pk})
        scores_resp = self.client.get(scores_url)
        self.assertEqual(scores_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(scores_resp.data["data"]["total_points"], "150.00")

        # Rank
        rank_url = reverse("api_v1:admin_students:rank", kwargs={"pk": pk})
        rank_resp = self.client.get(rank_url)
        self.assertEqual(rank_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(rank_resp.data["data"]["global_rank"], 1)

    def test_student_cannot_access_student_admin_api(self):
        self._auth_student()
        url = reverse("api_v1:admin_students:list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 2. COURSE MANAGEMENT
    # =========================================================================

    def test_course_crud_and_publish(self):
        self._auth_admin()
        list_url = reverse("api_v1:admin_courses:list_create")

        # 1. Create Course
        create_resp = self.client.post(
            list_url,
            {
                "title": "Mastering Django REST",
                "slug": "mastering-django-rest",
                "description": "Comprehensive backend curriculum",
                "thumbnail_url": "https://example.com/thumbnail.png",
                "is_published": False,
                "order": 1,
            },
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        course_id = create_resp.data["data"]["id"]

        # 2. Retrieve & Update
        detail_url = reverse(
            "api_v1:admin_courses:detail_update_delete", kwargs={"pk": course_id}
        )
        update_resp = self.client.patch(
            detail_url, {"description": "Updated description"}, format="json"
        )
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(update_resp.data["data"]["description"], "Updated description")

        # 3. Publish Toggle
        pub_url = reverse("api_v1:admin_courses:publish", kwargs={"pk": course_id})
        pub_resp = self.client.post(pub_url, {"is_published": True}, format="json")
        self.assertEqual(pub_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(pub_resp.data["data"]["is_published"])

        # 4. Safe Archive / Soft Delete
        del_resp = self.client.delete(detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)
        course = Course.objects.get(id=course_id)
        self.assertTrue(course.is_deleted)
        self.assertFalse(course.is_published)

    def test_student_cannot_access_course_admin_api(self):
        self._auth_student()
        url = reverse("api_v1:admin_courses:list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 3. MODULE MANAGEMENT & REORDERING
    # =========================================================================

    def test_module_crud_and_reorder(self):
        course = Course.objects.create(title="Data Structures", slug="data-structures")
        self._auth_admin()
        list_url = reverse("api_v1:admin_modules:list_create")

        # 1. Create Module 1
        m1_resp = self.client.post(
            list_url,
            {
                "course_id": str(course.id),
                "title": "Arrays & Strings",
                "slug": "arrays-strings",
                "order_index": 1,
                "summary": "Core array manipulation",
                "passing_percentage": 75.00,
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(m1_resp.status_code, status.HTTP_201_CREATED)
        m1_id = m1_resp.data["data"]["id"]

        # 2. Create Module 2 with prerequisite M1
        m2_resp = self.client.post(
            list_url,
            {
                "course_id": str(course.id),
                "title": "Linked Lists",
                "slug": "linked-lists",
                "order_index": 2,
                "prerequisite_ids": [m1_id],
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(m2_resp.status_code, status.HTTP_201_CREATED)
        m2_id = m2_resp.data["data"]["id"]

        # 3. Reorder modules
        reorder_url = reverse("api_v1:admin_modules:reorder")
        reorder_resp = self.client.post(
            reorder_url,
            {
                "course_id": str(course.id),
                "orders": [
                    {"id": m1_id, "order_index": 2},
                    {"id": m2_id, "order_index": 1},
                ],
            },
            format="json",
        )
        self.assertEqual(reorder_resp.status_code, status.HTTP_200_OK)

        m1 = Module.objects.get(id=m1_id)
        m2 = Module.objects.get(id=m2_id)
        self.assertEqual(m1.order_index, 2)
        self.assertEqual(m2.order_index, 1)

    def test_student_cannot_access_module_admin_api(self):
        self._auth_student()
        url = reverse("api_v1:admin_modules:list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 4. ASSIGNMENT & TEST CASE MANAGEMENT
    # =========================================================================

    def test_coding_question_and_testcase_lifecycle(self):
        course = Course.objects.create(title="Algorithms", slug="algorithms")
        module = Module.objects.create(
            course=course, title="Recursion", slug="recursion", order_index=1
        )
        self._auth_admin()

        # 1. Create Question with embedded test cases
        q_url = reverse("api_v1:admin_assignments:question_list_create")
        q_resp = self.client.post(
            q_url,
            {
                "module_id": str(module.id),
                "title": "Fibonacci Number",
                "slug": "fibonacci-number",
                "difficulty": "EASY",
                "problem_statement": "Calculate the nth Fibonacci number.",
                "allowed_languages": ["python", "java"],
                "starter_code": {"python": "def fib(n): pass"},
                "points": 50.00,
                "test_cases": [
                    {
                        "input_data": "5",
                        "expected_output": "5",
                        "is_visible": True,
                        "weight": 1.00,
                    },
                    {
                        "input_data": "10",
                        "expected_output": "55",
                        "is_visible": False,
                        "weight": 2.00,
                    },
                ],
            },
            format="json",
        )
        self.assertEqual(q_resp.status_code, status.HTTP_201_CREATED)
        question_id = q_resp.data["data"]["id"]
        self.assertEqual(len(q_resp.data["data"]["test_cases"]), 2)

        # 2. Add extra hidden testcase
        tc_url = reverse(
            "api_v1:admin_assignments:testcase_create", kwargs={"pk": question_id}
        )
        tc_resp = self.client.post(
            tc_url,
            {
                "input_data": "20",
                "expected_output": "6765",
                "is_visible": False,
                "weight": 3.00,
            },
            format="json",
        )
        self.assertEqual(tc_resp.status_code, status.HTTP_201_CREATED)
        tc_id = tc_resp.data["data"]["id"]

        # 3. Update Testcase
        tc_detail_url = reverse(
            "api_v1:admin_assignments:testcase_detail_update_delete",
            kwargs={"pk": tc_id},
        )
        update_tc_resp = self.client.patch(
            tc_detail_url, {"weight": 5.00}, format="json"
        )
        self.assertEqual(update_tc_resp.status_code, status.HTTP_200_OK)

        # 4. Delete Testcase
        del_tc_resp = self.client.delete(tc_detail_url)
        self.assertEqual(del_tc_resp.status_code, status.HTTP_200_OK)
        self.assertFalse(CodingTestCase.objects.filter(id=tc_id).exists())

    def test_student_cannot_access_assignment_admin_api(self):
        self._auth_student()
        url = reverse("api_v1:admin_assignments:question_list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 5. TASK MANAGEMENT
    # =========================================================================

    def test_daily_task_crud(self):
        self._auth_admin()
        task_date = timezone.localdate() + timedelta(days=1)
        list_url = reverse("api_v1:admin_tasks:list_create")

        # 1. Create Daily Task
        create_resp = self.client.post(
            list_url,
            {
                "title": "Two Sum Daily Challenge",
                "description": "Solve two sum in linear time complexity.",
                "scheduled_date": str(task_date),
                "points": 25.00,
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        task_id = create_resp.data["data"]["id"]

        # 2. Update Task
        detail_url = reverse(
            "api_v1:admin_tasks:detail_update_delete", kwargs={"pk": task_id}
        )
        update_resp = self.client.patch(detail_url, {"points": 30.00}, format="json")
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(update_resp.data["data"]["points"], "30.00")

        # 3. Delete Task
        del_resp = self.client.delete(detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_student_cannot_access_task_admin_api(self):
        self._auth_student()
        url = reverse("api_v1:admin_tasks:list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 6. CAPSTONE PROJECT MANAGEMENT & SUBMISSION REVIEW
    # =========================================================================

    def test_project_crud_and_submission_review(self):
        self._auth_admin()
        proj_url = reverse("api_v1:admin_projects:project_list_create")

        # 1. Create Capstone Project
        create_resp = self.client.post(
            proj_url,
            {
                "title": "E-Commerce Microservice API",
                "slug": "ecommerce-microservice",
                "description": "Build high concurrency ordering service",
                "deliverables_instructions": "Submit GitHub repo URL and live URL",
                "max_score": 100.00,
            },
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        project_id = create_resp.data["data"]["id"]
        project = Project.objects.get(id=project_id)

        # 2. Simulate Student Submission
        submission = ProjectSubmission.objects.create(
            project=project,
            student=self.student_profile,
            github_repository_url="https://github.com/student/ecommerce",
            live_demo_url="https://demo.student.com",
            notes="Implemented with JWT and Redis caching",
            status=ProjectSubmission.SubmissionStatus.SUBMITTED,
        )

        # 3. Admin Review & Grade
        review_url = reverse(
            "api_v1:admin_projects:submission_detail_review",
            kwargs={"pk": submission.id},
        )
        review_resp = self.client.post(
            review_url,
            {
                "status": "APPROVED",
                "score": 95.00,
                "feedback_text": "Excellent architecture and test coverage.",
                "suggested_changes": "Add rate limiting for login endpoints.",
                "rating": 5,
            },
            format="json",
        )
        self.assertEqual(review_resp.status_code, status.HTTP_200_OK)

        submission.refresh_from_db()
        self.assertEqual(submission.status, ProjectSubmission.SubmissionStatus.APPROVED)
        self.assertEqual(submission.score, Decimal("95.00"))

        # Check feedback created
        feedback = ProjectFeedback.objects.filter(submission=submission).first()
        self.assertIsNotNone(feedback)
        self.assertEqual(feedback.rating, 5)

        # Check score record and student total points awarded
        score_rec = ScoreRecord.objects.filter(
            student=self.student_profile, source_type=ScoreRecord.SourceType.PROJECT
        ).first()
        self.assertIsNotNone(score_rec)
        self.assertEqual(score_rec.points, Decimal("95.00"))

        self.student_profile.refresh_from_db()
        # 150.00 initial + 95.00 awarded = 245.00
        self.assertEqual(self.student_profile.total_points, Decimal("245.00"))

    def test_student_cannot_access_project_admin_api(self):
        self._auth_student()
        url = reverse("api_v1:admin_projects:project_list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 7. ANNOUNCEMENT BROADCASTS
    # =========================================================================

    def test_announcement_crud(self):
        self._auth_admin()
        ann_url = reverse("api_v1:admin_announcements:list_create")

        # 1. Create Announcement
        create_resp = self.client.post(
            ann_url,
            {
                "title": "System Maintenance Downtime",
                "content": "Portal will undergo routine maintenance at midnight.",
                "target_batch": "PY-2026-B1",
                "priority": "HIGH",
            },
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        ann_id = create_resp.data["data"]["id"]

        # 2. Update Announcement
        detail_url = reverse(
            "api_v1:admin_announcements:detail_update_delete", kwargs={"pk": ann_id}
        )
        update_resp = self.client.patch(
            detail_url, {"priority": "URGENT"}, format="json"
        )
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(update_resp.data["data"]["priority"], "URGENT")

        # 3. Deactivate
        del_resp = self.client.delete(detail_url)
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)
        ann = Announcement.objects.get(id=ann_id)
        self.assertFalse(ann.is_active)

    def test_student_cannot_access_announcement_admin_api(self):
        self._auth_student()
        url = reverse("api_v1:admin_announcements:list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # =========================================================================
    # 8. ANALYTICS & EXECUTIVE REPORTS
    # =========================================================================

    def test_analytics_dashboard_and_reports(self):
        self._auth_admin()

        # 1. Dashboard Overview
        dash_url = reverse("api_v1:admin_analytics:dashboard")
        dash_resp = self.client.get(dash_url)
        self.assertEqual(dash_resp.status_code, status.HTTP_200_OK)
        self.assertIn("total_students", dash_resp.data["data"])
        self.assertIn("active_students", dash_resp.data["data"])
        self.assertIn("top_performers", dash_resp.data["data"])

        # 2. Performance Report
        perf_url = reverse("api_v1:admin_analytics:report_performance")
        perf_resp = self.client.get(f"{perf_url}?batch_code=PY-2026-B1")
        self.assertEqual(perf_resp.status_code, status.HTTP_200_OK)
        self.assertIn("average_points", perf_resp.data["data"])

        # 3. Completion Report
        comp_url = reverse("api_v1:admin_analytics:report_completion")
        comp_resp = self.client.get(comp_url)
        self.assertEqual(comp_resp.status_code, status.HTTP_200_OK)
        self.assertIn("courses", comp_resp.data["data"])

        # 4. Assignment Report
        assign_url = reverse("api_v1:admin_analytics:report_assignment")
        assign_resp = self.client.get(assign_url)
        self.assertEqual(assign_resp.status_code, status.HTTP_200_OK)
        self.assertIn("questions", assign_resp.data["data"])

        # 5. Project Report
        proj_url = reverse("api_v1:admin_analytics:report_project")
        proj_resp = self.client.get(proj_url)
        self.assertEqual(proj_resp.status_code, status.HTTP_200_OK)
        self.assertIn("projects", proj_resp.data["data"])

        # 6. Monthly Activity Report
        month_url = reverse("api_v1:admin_analytics:report_monthly_activity")
        month_resp = self.client.get(f"{month_url}?days=7")
        self.assertEqual(month_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(month_resp.data["data"]["days_analyzed"], 7)
        self.assertEqual(len(month_resp.data["data"]["timeline"]), 7)

    def test_student_cannot_access_analytics_and_reports_api(self):
        self._auth_student()
        endpoints = [
            reverse("api_v1:admin_analytics:dashboard"),
            reverse("api_v1:admin_analytics:report_performance"),
            reverse("api_v1:admin_analytics:report_completion"),
            reverse("api_v1:admin_analytics:report_assignment"),
            reverse("api_v1:admin_analytics:report_project"),
            reverse("api_v1:admin_analytics:report_monthly_activity"),
        ]
        for ep in endpoints:
            resp = self.client.get(ep)
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
