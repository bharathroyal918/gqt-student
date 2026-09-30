"""Comprehensive test suite for Admin Analytics, KPI Dashboards, Reports, and Async Export Architecture."""

from decimal import Decimal
import json
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.analytics.models import ExportJob
from apps.analytics.services import AnalyticsAdminService
from apps.analytics.tasks import _process_export_job_worker
from apps.assignments.models import CodeSubmission, CodingQuestion
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.projects.models import Project, ProjectSubmission
from apps.students.models import StudentProfile

User = get_user_model()


class AnalyticsAndReportsApiTests(APITestCase):
    """Test suite covering KPI aggregation, reports, caching, and background export jobs."""

    def setUp(self):
        cache.clear()

        # 1. Admin User
        self.admin_user = User.objects.create_superuser(
            email="admin.analytics@gqt.local", password="AdminPassword123!"
        )

        # 2. Regular Student User
        self.student_user = User.objects.create_user(
            email="student.analytics@gqt.local", password="Password123!", role=User.RoleChoices.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            student_id_number="GQT-STU-ANA-1",
            full_name="Alice Analytics",
            batch_code="BATCH-2026-A",
            total_points=Decimal("250.00"),
            current_streak_days=4,
            highest_streak_days=7,
        )

        # 3. Student 2
        self.student_user_2 = User.objects.create_user(
            email="bob.analytics@gqt.local", password="Password123!", role=User.RoleChoices.STUDENT
        )
        self.student_profile_2 = StudentProfile.objects.create(
            user=self.student_user_2,
            student_id_number="GQT-STU-ANA-2",
            full_name="Bob Beginner",
            batch_code="BATCH-2026-B",
            total_points=Decimal("50.00"),
            current_streak_days=1,
            highest_streak_days=1,
        )

        # 4. Course, Module, and Questions
        self.course = Course.objects.create(
            title="Enterprise System Design",
            slug="enterprise-system-design",
            is_published=True,
        )
        self.module = Module.objects.create(
            course=self.course,
            title="Distributed Systems",
            slug="distributed-systems",
            order_index=1,
            is_published=True,
        )
        self.question = CodingQuestion.objects.create(
            module=self.module,
            title="Rate Limiter Implementation",
            slug="rate-limiter-impl",
            difficulty=CodingQuestion.DifficultyChoices.MEDIUM,
            points=Decimal("50.00"),
            is_active=True,
        )

        # Enrollments
        CourseEnrollment.objects.create(
            student=self.student_profile,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )

        # Module Progress
        StudentModuleProgress.objects.create(
            student=self.student_profile,
            module=self.module,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
        )

        # Submissions
        CodeSubmission.objects.create(
            student=self.student_profile,
            question=self.question,
            source_code="print('ok')",
            language="python",
            status=CodeSubmission.SubmissionStatus.ACCEPTED,
            score_awarded=Decimal("50.00"),
            passed_test_cases=3,
            total_test_cases=3,
        )

        # Project
        self.project = Project.objects.create(
            title="Cloud Infrastructure Automation",
            slug="cloud-infra-auto",
            course=self.course,
            max_score=Decimal("100.00"),
            is_active=True,
        )
        ProjectSubmission.objects.create(
            project=self.project,
            student=self.student_profile,
            github_repository_url="https://github.com/alice/cloud-infra",
            status=ProjectSubmission.SubmissionStatus.APPROVED,
            score=Decimal("95.00"),
        )

    def test_dashboard_metrics_aggregation(self):
        """Admin fetches comprehensive KPI metrics, score distribution, and timeline."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/v1/admin/analytics/dashboard/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.json()["data"]
        self.assertEqual(data["total_students"], 2)
        self.assertEqual(data["active_students"], 2)
        self.assertIn("score_distribution", data)
        self.assertIn("assignment_statistics", data)
        self.assertEqual(data["assignment_statistics"]["total_submissions"], 1)
        self.assertEqual(data["assignment_statistics"]["accepted_submissions"], 1)
        self.assertEqual(data["project_statistics"]["approved_submissions"], 1)
        self.assertTrue(len(data["top_performers"]) >= 1)
        self.assertTrue(len(data["activity_timeline"]) >= 1)

    def test_dashboard_metrics_filtering(self):
        """Dashboard filters by course UUID and batch code correctly."""
        self.client.force_authenticate(user=self.admin_user)

        # Filter by specific batch
        res_batch = self.client.get("/api/v1/admin/analytics/dashboard/?batch_code=BATCH-2026-A")
        self.assertEqual(res_batch.status_code, status.HTTP_200_OK)
        data_batch = res_batch.json()["data"]
        self.assertEqual(data_batch["total_students"], 1)

        # Filter by course ID
        res_course = self.client.get(f"/api/v1/admin/analytics/dashboard/?course_id={self.course.id}")
        self.assertEqual(res_course.status_code, status.HTTP_200_OK)
        data_course = res_course.json()["data"]
        self.assertEqual(data_course["total_modules"], 1)

    def test_performance_report(self):
        """Admin fetches student performance summary report."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/v1/admin/reports/performance/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.json()["data"]
        self.assertEqual(data["total_students"], 2)
        self.assertTrue(float(data["average_points"]) > 0)
        self.assertTrue(len(data["batch_breakdown"]) >= 1)
        self.assertTrue(len(data["students"]) >= 1)

    def test_curriculum_completion_report(self):
        """Admin fetches curriculum module completion percentages."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/v1/admin/reports/completion/?course_id={self.course.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.json()["data"]
        self.assertEqual(len(data["courses"]), 1)
        course_stat = data["courses"][0]
        self.assertEqual(course_stat["active_enrollments"], 1)
        self.assertEqual(len(course_stat["modules"]), 1)
        self.assertEqual(course_stat["modules"][0]["completion_rate"], 100.0)

    def test_assignment_statistics_report(self):
        """Admin fetches question pass rate and attempt statistics."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/v1/admin/reports/assignment/?module_id={self.module.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.json()["data"]
        self.assertEqual(len(data["questions"]), 1)
        q = data["questions"][0]
        self.assertEqual(q["total_submissions"], 1)
        self.assertEqual(q["pass_rate"], 100.0)

    def test_project_evaluation_report(self):
        """Admin fetches project evaluation scores and review numbers."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/v1/admin/reports/project/?course_id={self.course.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.json()["data"]
        self.assertEqual(len(data["projects"]), 1)
        p = data["projects"][0]
        self.assertEqual(p["approved_submissions"], 1)
        self.assertEqual(p["average_score"], "95.00")

    def test_monthly_activity_report(self):
        """Admin fetches time-series activity analysis."""
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/v1/admin/reports/monthly-activity/?days=14")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.json()["data"]
        self.assertEqual(data["days_analyzed"], 14)
        self.assertEqual(len(data["timeline"]), 14)

    def test_async_export_job_flow(self):
        """Initiating an export job returns 202, executes in background, and streams generated file."""
        self.client.force_authenticate(user=self.admin_user)

        # 1. Create Export Job
        payload = {
            "report_type": ExportJob.ReportType.STUDENT_PERFORMANCE,
            "format": "CSV",
            "filters": {"batch_code": "BATCH-2026-A"},
        }
        res = self.client.post("/api/v1/admin/reports/export/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_202_ACCEPTED)
        job_id = res.json()["data"]["id"]

        # 2. Worker compiles file
        success = _process_export_job_worker(job_id)
        self.assertTrue(success)

        # 3. Retrieve status
        status_res = self.client.get(f"/api/v1/admin/reports/exports/{job_id}/")
        self.assertEqual(status_res.status_code, status.HTTP_200_OK)
        job_data = status_res.json()["data"]
        self.assertEqual(job_data["status"], "COMPLETED")
        self.assertTrue(job_data["file_size_bytes"] > 0)
        self.assertEqual(job_data["row_count"], 1)

        # 4. Download file
        download_res = self.client.get(f"/api/v1/admin/reports/exports/{job_id}/download/")
        self.assertEqual(download_res.status_code, status.HTTP_200_OK)
        self.assertEqual(download_res["Content-Type"], "text/csv")
        self.assertIn("attachment; filename=", download_res["Content-Disposition"])

    def test_student_cannot_access_admin_analytics_and_reports(self):
        """Students are strictly forbidden from accessing admin analytics and reports."""
        self.client.force_authenticate(user=self.student_user)

        res_dash = self.client.get("/api/v1/admin/analytics/dashboard/")
        self.assertEqual(res_dash.status_code, status.HTTP_403_FORBIDDEN)

        res_perf = self.client.get("/api/v1/admin/reports/performance/")
        self.assertEqual(res_perf.status_code, status.HTTP_403_FORBIDDEN)

        res_export = self.client.post(
            "/api/v1/admin/reports/export/",
            {"report_type": "STUDENT_PERFORMANCE", "format": "CSV"},
            format="json",
        )
        self.assertEqual(res_export.status_code, status.HTTP_403_FORBIDDEN)
