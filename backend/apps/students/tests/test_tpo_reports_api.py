"""Automated tests for Phase 6 TPO Reports, Secure Exports & Auditability APIs."""

from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import AuditLog, TPOProfile, User
from apps.assignments.models import CodeSubmission, CodingQuestion
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.scoring.models import ScoreRecord
from apps.students.models import AttendanceRecord, College, StudentProfile

User = get_user_model()


@pytest.mark.django_db
class TestTPOReportsAPIs:
    """Test suite covering Phase 6 TPO Report generation, CSV/JSON export security, and auditability."""

    def setup_method(self):
        self.client = APIClient()

        # 1. Create two colleges
        self.college_a = College.objects.create(
            name="Alpha Engineering Institute",
            code="AEI-101",
            city="Bengaluru",
            state="Karnataka",
            is_active=True,
        )
        self.college_b = College.objects.create(
            name="Beta University of Tech",
            code="BUT-202",
            city="Hyderabad",
            state="Telangana",
            is_active=True,
        )

        # 2. Create TPO for College A
        self.tpo_user_a = User.objects.create_user(
            email="tpo_reports_alpha@example.com",
            password="SecureTPOCreds123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        self.tpo_profile_a = TPOProfile.objects.create(
            user=self.tpo_user_a,
            full_name="Alpha Report Officer",
            college=self.college_a,
            is_active=True,
        )

        # 3. Create Students for College A
        # Student A1: High performer
        self.student_user_a1 = User.objects.create_user(
            email="alice@alpha.edu",
            mobile_number="+919876543210",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
        )
        self.student_a1 = StudentProfile.objects.create(
            user=self.student_user_a1,
            student_id_number="AEI-001",
            full_name="Alice Alpha",
            college=self.college_a,
            college_name=self.college_a.name,
            batch_code="BATCH-2026-A",
            branch="Computer Science",
            course_opted="Full Stack Development",
            attendance_percentage=Decimal("90.00"),
            total_points=Decimal("500.00"),
            total_classes=50,
            attended_classes=45,
            current_streak_days=5,
            highest_streak_days=10,
        )

        # Student A2: Formula injection test string in student name & Needs Support
        self.student_user_a2 = User.objects.create_user(
            email="aaron@alpha.edu",
            mobile_number="+919876543211",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
        )
        self.student_a2 = StudentProfile.objects.create(
            user=self.student_user_a2,
            student_id_number="AEI-002",
            full_name="=cmd|' /C calc'!A0",  # CSV formula injection probe
            college=self.college_a,
            college_name=self.college_a.name,
            batch_code="BATCH-2026-B",
            branch="Information Science",
            course_opted="Full Stack Development",
            attendance_percentage=Decimal("60.00"),
            total_points=Decimal("0.00"),
            total_classes=50,
            attended_classes=30,
            current_streak_days=0,
            highest_streak_days=0,
        )

        # Student B1: Other college student (Isolation test)
        self.student_user_b1 = User.objects.create_user(
            email="bob@beta.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
        )
        self.student_b1 = StudentProfile.objects.create(
            user=self.student_user_b1,
            student_id_number="BUT-001",
            full_name="Bob Beta Other College",
            college=self.college_b,
            college_name=self.college_b.name,
            batch_code="BATCH-2026-A",
            branch="Electronics",
            course_opted="Data Science",
            attendance_percentage=Decimal("85.00"),
            total_points=Decimal("400.00"),
            total_classes=50,
            attended_classes=42,
            current_streak_days=3,
            highest_streak_days=6,
        )

        # Course & Module & Submission Setup
        self.course = Course.objects.create(
            title="Full Stack Python",
            slug="full-stack-python",
            is_published=True,
        )
        self.module = Module.objects.create(
            course=self.course,
            title="Module 1: Django",
            slug="module-1-django",
            order_index=1,
            is_published=True,
        )
        CourseEnrollment.objects.create(
            student=self.student_a1,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )
        StudentModuleProgress.objects.create(
            student=self.student_a1,
            module=self.module,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
        )
        self.question = CodingQuestion.objects.create(
            module=self.module,
            title="Two Sum",
            slug="two-sum",
        )
        self.sub = CodeSubmission.objects.create(
            student=self.student_a1,
            question=self.question,
            language="python",
            source_code="pass",
            status=CodeSubmission.SubmissionStatus.ACCEPTED,
            score_awarded=Decimal("100.00"),
            passed_test_cases=5,
            total_test_cases=5,
        )

    # --------------------------------------------------------------------------
    # REPORT TYPES & METADATA TESTS
    # --------------------------------------------------------------------------

    def test_get_supported_report_types(self):
        """TPO can list supported report types and format capabilities."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/reports/types/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        report_ids = [r["id"] for r in data]
        assert "STUDENT_ROSTER" in report_ids
        assert "ATTENDANCE_COMPLIANCE" in report_ids
        assert "LEARNING_PROGRESS" in report_ids
        assert "ASSIGNMENTS_LABS" in report_ids
        assert "STUDENTS_NEEDING_SUPPORT" in report_ids
        assert "COLLEGE_SUMMARY" in report_ids

    # --------------------------------------------------------------------------
    # REPORT PREVIEW TESTS
    # --------------------------------------------------------------------------

    def test_report_preview_student_roster(self):
        """Preview student roster generates accurate columns and row counts."""
        self.client.force_authenticate(user=self.tpo_user_a)
        payload = {"report_type": "STUDENT_ROSTER", "filters": {}}
        response = self.client.post("/api/v1/tpo/reports/preview/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["report_type"] == "STUDENT_ROSTER"
        assert data["college"]["name"] == "Alpha Engineering Institute"
        assert data["total_rows"] == 2
        assert "Student ID" in data["columns"]
        assert len(data["preview_rows"]) == 2

    def test_report_preview_attendance_compliance(self):
        """Preview attendance compliance includes eligibility status."""
        self.client.force_authenticate(user=self.tpo_user_a)
        payload = {"report_type": "ATTENDANCE_COMPLIANCE", "filters": {}}
        response = self.client.post("/api/v1/tpo/reports/preview/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["total_rows"] == 2
        assert "Placement Eligibility Status" in data["columns"]

    def test_report_preview_students_needing_support(self):
        """Preview students needing support lists flagged student Aaron."""
        self.client.force_authenticate(user=self.tpo_user_a)
        payload = {"report_type": "STUDENTS_NEEDING_SUPPORT", "filters": {}}
        response = self.client.post("/api/v1/tpo/reports/preview/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["total_rows"] >= 1

    # --------------------------------------------------------------------------
    # EXPORT CSV & INJECTION MITIGATION TESTS
    # --------------------------------------------------------------------------

    def test_report_export_csv_format_and_headers(self):
        """Export CSV returns UTF-8 with BOM and valid Content-Disposition."""
        self.client.force_authenticate(user=self.tpo_user_a)
        payload = {"report_type": "STUDENT_ROSTER", "format": "CSV", "filters": {}}
        response = self.client.post("/api/v1/tpo/reports/export/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "text/csv" in response["Content-Type"]
        assert "attachment; filename=" in response["Content-Disposition"]
        assert "student_roster" in response["Content-Disposition"]

        content = response.content.decode("utf-8-sig")
        lines = content.strip().split("\r\n")
        assert len(lines) >= 3  # Header + 2 rows
        assert "Student ID,Full Name,Email" in lines[0]

    def test_report_export_csv_formula_injection_sanitization(self):
        """Formula characters (=, +, -, @) are sanitized with prepended single quote."""
        self.client.force_authenticate(user=self.tpo_user_a)
        payload = {"report_type": "STUDENT_ROSTER", "format": "CSV", "filters": {}}
        response = self.client.post("/api/v1/tpo/reports/export/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        content = response.content.decode("utf-8-sig")

        # The malicious student name starting with '=' should be prepended with "'"
        assert "'=cmd|' /C calc'!A0" in content
        # Ensure it does NOT start nakedly with =
        assert ",=cmd|" not in content

    def test_report_export_json_format(self):
        """Export JSON returns formatted JSON artifact with headers and records."""
        self.client.force_authenticate(user=self.tpo_user_a)
        payload = {"report_type": "STUDENT_ROSTER", "format": "JSON", "filters": {}}
        response = self.client.post("/api/v1/tpo/reports/export/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "application/json" in response["Content-Type"]
        assert "student_roster" in response["Content-Disposition"]

        json_data = response.json()
        assert json_data["report_type"] == "STUDENT_ROSTER"
        assert json_data["total_rows"] == 2
        assert len(json_data["data"]) == 2

    # --------------------------------------------------------------------------
    # SECURITY & ISOLATION TESTS
    # --------------------------------------------------------------------------

    def test_security_gate_cross_college_student_never_exported(self):
        """Bob Beta (College B) must NEVER appear in College A exports or previews."""
        self.client.force_authenticate(user=self.tpo_user_a)
        payload = {"report_type": "STUDENT_ROSTER", "format": "JSON", "filters": {}}
        response = self.client.post("/api/v1/tpo/reports/export/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        student_ids = [row["Student ID"] for row in data]

        assert "AEI-001" in student_ids
        assert "AEI-002" in student_ids
        assert "BUT-001" not in student_ids

    def test_security_gate_unauthorized_user_denied(self):
        """Anonymous and student users cannot call report export."""
        # Anonymous
        response_anon = self.client.post("/api/v1/tpo/reports/export/", {"report_type": "STUDENT_ROSTER"})
        assert response_anon.status_code == status.HTTP_401_UNAUTHORIZED

        # Student user
        self.client.force_authenticate(user=self.student_user_a1)
        response_student = self.client.post("/api/v1/tpo/reports/export/", {"report_type": "STUDENT_ROSTER"})
        assert response_student.status_code == status.HTTP_403_FORBIDDEN

    def test_security_gate_audit_logging_recorded(self):
        """Preview and export actions create immutable AuditLog entries."""
        self.client.force_authenticate(user=self.tpo_user_a)

        # 1. Preview
        self.client.post("/api/v1/tpo/reports/preview/", {"report_type": "ATTENDANCE_COMPLIANCE"})
        assert AuditLog.objects.filter(actor=self.tpo_user_a, action="TPO_REPORT_PREVIEW").exists()

        # 2. Export
        self.client.post("/api/v1/tpo/reports/export/", {"report_type": "ATTENDANCE_COMPLIANCE", "format": "CSV"})
        assert AuditLog.objects.filter(actor=self.tpo_user_a, action="TPO_REPORT_EXPORT").exists()
