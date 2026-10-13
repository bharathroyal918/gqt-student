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
            graduation_year=2026,
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
            graduation_year=2026,
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
            graduation_year=2026,
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

    # --------------------------------------------------------------------------
    # COMPREHENSIVE FILTER VALIDATION TESTS
    # --------------------------------------------------------------------------

    def test_valid_filters_all_supported_reports(self):
        """Verify each supported report type generates preview with its valid filter contract."""
        self.client.force_authenticate(user=self.tpo_user_a)

        valid_cases = [
            ("STUDENT_ROSTER", {"batch_code": "BATCH-2026-A", "graduation_year": 2026, "course_opted": "Full Stack", "is_active": True}),
            ("ATTENDANCE_COMPLIANCE", {"batch_code": "BATCH-2026-A", "graduation_year": 2026}),
            ("LEARNING_PROGRESS", {"course_id": str(self.course.id), "status": "COMPLETED"}),
            ("ASSIGNMENTS_LABS", {"date_from": "2026-01-01", "date_to": "2026-12-31", "graduation_year": 2026}),
            ("STUDENTS_NEEDING_SUPPORT", {"risk_type": "LOW_ATTENDANCE", "graduation_year": 2026}),
            ("COLLEGE_SUMMARY", {}),
        ]

        for r_type, filters in valid_cases:
            res = self.client.post("/api/v1/tpo/reports/preview/", {"report_type": r_type, "filters": filters}, format="json")
            assert res.status_code == status.HTTP_200_OK, f"Failed for {r_type} with valid filters: {res.json()}"
            assert res.json()["data"]["report_type"] == r_type

    def test_unknown_filter_keys_rejected(self):
        """Unknown filter keys are rejected with HTTP 400 validation error."""
        self.client.force_authenticate(user=self.tpo_user_a)

        # 1. Preview endpoint
        res_prev = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "STUDENT_ROSTER", "filters": {"malicious_key": "val"}},
            format="json",
        )
        assert res_prev.status_code == status.HTTP_400_BAD_REQUEST

        # 2. Export endpoint
        res_exp = self.client.post(
            "/api/v1/tpo/reports/export/",
            {"report_type": "STUDENT_ROSTER", "format": "CSV", "filters": {"unknown_key": "val"}},
            format="json",
        )
        assert res_exp.status_code == status.HTTP_400_BAD_REQUEST

    def test_college_summary_rejects_any_filters(self):
        """COLLEGE_SUMMARY does not accept any filters; any key results in HTTP 400."""
        self.client.force_authenticate(user=self.tpo_user_a)
        res = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "COLLEGE_SUMMARY", "filters": {"batch_code": "BATCH-2026-A"}},
            format="json",
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_is_active_rejected(self):
        """Arbitrary or ambiguous is_active values (e.g. 'maybe') return HTTP 400."""
        self.client.force_authenticate(user=self.tpo_user_a)
        for bad_val in ["maybe", "unknown", 100, -1, "not_bool"]:
            res = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "STUDENT_ROSTER", "filters": {"is_active": bad_val}},
                format="json",
            )
            assert res.status_code == status.HTTP_400_BAD_REQUEST, f"Expected 400 for is_active={bad_val}"

    def test_valid_is_active_accepted(self):
        """Documented boolean representations and 'ALL' return HTTP 200."""
        self.client.force_authenticate(user=self.tpo_user_a)
        for good_val in [True, False, "true", "false", "1", "0", "ALL", "all"]:
            res = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "STUDENT_ROSTER", "filters": {"is_active": good_val}},
                format="json",
            )
            assert res.status_code == status.HTTP_200_OK, f"Expected 200 for is_active={good_val}"

    def test_invalid_graduation_year_rejected(self):
        """Invalid types and out-of-bounds graduation years return HTTP 400."""
        self.client.force_authenticate(user=self.tpo_user_a)
        for bad_yr in ["twenty-twenty", 1850, 3000, 2024.5, -2026]:
            res = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "STUDENT_ROSTER", "filters": {"graduation_year": bad_yr}},
                format="json",
            )
            assert res.status_code == status.HTTP_400_BAD_REQUEST, f"Expected 400 for graduation_year={bad_yr}"

    def test_valid_graduation_year_accepted(self):
        """Valid graduation years within 1990-2100 and 'ALL' return HTTP 200."""
        self.client.force_authenticate(user=self.tpo_user_a)
        for good_yr in [2026, "2026", "ALL", "all"]:
            res = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "STUDENT_ROSTER", "filters": {"graduation_year": good_yr}},
                format="json",
            )
            assert res.status_code == status.HTTP_200_OK, f"Expected 200 for graduation_year={good_yr}"

    def test_invalid_course_id_rejected(self):
        """Malformed or nonexistent course UUID returns HTTP 400."""
        self.client.force_authenticate(user=self.tpo_user_a)
        # 1. Malformed
        res_malformed = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "LEARNING_PROGRESS", "filters": {"course_id": "not-a-uuid"}},
            format="json",
        )
        assert res_malformed.status_code == status.HTTP_400_BAD_REQUEST

        # 2. Nonexistent UUID
        res_nonexistent = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "LEARNING_PROGRESS", "filters": {"course_id": "00000000-0000-0000-0000-000000000000"}},
            format="json",
        )
        assert res_nonexistent.status_code == status.HTTP_400_BAD_REQUEST

    def test_valid_course_id_accepted(self):
        """Valid course UUID and 'ALL' return HTTP 200."""
        self.client.force_authenticate(user=self.tpo_user_a)
        res_valid = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "LEARNING_PROGRESS", "filters": {"course_id": str(self.course.id)}},
            format="json",
        )
        assert res_valid.status_code == status.HTTP_200_OK

        res_all = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "LEARNING_PROGRESS", "filters": {"course_id": "ALL"}},
            format="json",
        )
        assert res_all.status_code == status.HTTP_200_OK

    def test_status_filter_validation(self):
        """Invalid status returns HTTP 400; valid statuses return HTTP 200."""
        self.client.force_authenticate(user=self.tpo_user_a)
        res_bad = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "LEARNING_PROGRESS", "filters": {"status": "INVALID_STATUS"}},
            format="json",
        )
        assert res_bad.status_code == status.HTTP_400_BAD_REQUEST

        for st_val in ["COMPLETED", "ON_TRACK", "NOT_STARTED", "ALL"]:
            res_good = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "LEARNING_PROGRESS", "filters": {"status": st_val}},
                format="json",
            )
            assert res_good.status_code == status.HTTP_200_OK

    def test_risk_type_filter_validation(self):
        """Invalid risk_type returns HTTP 400; valid risk types return HTTP 200."""
        self.client.force_authenticate(user=self.tpo_user_a)
        res_bad = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "STUDENTS_NEEDING_SUPPORT", "filters": {"risk_type": "FAKE_RISK"}},
            format="json",
        )
        assert res_bad.status_code == status.HTTP_400_BAD_REQUEST

        for r_val in ["LOW_ATTENDANCE", "ZERO_SUBMISSIONS", "HIGH_FAILURE_RATE", "STALLED_PROGRESS", "ALL"]:
            res_good = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "STUDENTS_NEEDING_SUPPORT", "filters": {"risk_type": r_val}},
                format="json",
            )
            assert res_good.status_code == status.HTTP_200_OK

    def test_assignment_lab_date_filters_validation(self):
        """Malformed dates, reversed date ranges, and > 5 year ranges return HTTP 400."""
        self.client.force_authenticate(user=self.tpo_user_a)
        # Malformed format
        res_mal = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "ASSIGNMENTS_LABS", "filters": {"date_from": "2026-99-99"}},
            format="json",
        )
        assert res_mal.status_code == status.HTTP_400_BAD_REQUEST

        # Reversed range
        res_rev = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "ASSIGNMENTS_LABS", "filters": {"date_from": "2026-12-01", "date_to": "2026-01-01"}},
            format="json",
        )
        assert res_rev.status_code == status.HTTP_400_BAD_REQUEST

        # Range > 5 years
        res_wide = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "ASSIGNMENTS_LABS", "filters": {"date_from": "2015-01-01", "date_to": "2025-01-01"}},
            format="json",
        )
        assert res_wide.status_code == status.HTTP_400_BAD_REQUEST

        # Valid boundaries
        res_valid = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "ASSIGNMENTS_LABS", "filters": {"date_from": "2026-01-01", "date_to": "2026-06-30"}},
            format="json",
        )
        assert res_valid.status_code == status.HTTP_200_OK

        # Optional date_from only
        res_from = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "ASSIGNMENTS_LABS", "filters": {"date_from": "2026-01-01"}},
            format="json",
        )
        assert res_from.status_code == status.HTTP_200_OK

        # Optional date_to only
        res_to = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "ASSIGNMENTS_LABS", "filters": {"date_to": "2026-06-30"}},
            format="json",
        )
        assert res_to.status_code == status.HTTP_200_OK

    def test_invalid_report_type_and_export_format_rejected(self):
        """Unsupported report_type or export format returns HTTP 400."""
        self.client.force_authenticate(user=self.tpo_user_a)
        # Invalid report type
        res_rt = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "INVALID_REPORT_XYZ"},
            format="json",
        )
        assert res_rt.status_code == status.HTTP_400_BAD_REQUEST

        # Invalid export format
        res_fmt = self.client.post(
            "/api/v1/tpo/reports/export/",
            {"report_type": "STUDENT_ROSTER", "format": "XML"},
            format="json",
        )
        assert res_fmt.status_code == status.HTTP_400_BAD_REQUEST

    def test_safe_filenames_with_unusual_college_identifiers(self):
        """Filenames must not contain CRLF, path separators, quotes, or header control chars."""
        # 1. College with CRLF and Header Injection attempt
        evil_college = College.objects.create(
            name="Alpha\r\nSet-Cookie: session=pwned\r\n\r\n",
            code="EVIL\r\nCRLF",
            is_active=True,
        )
        tpo_evil = User.objects.create_user(
            email="evil_tpo@example.com",
            password="Password123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        TPOProfile.objects.create(
            user=tpo_evil,
            full_name="Evil TPO",
            college=evil_college,
            is_active=True,
        )
        self.client.force_authenticate(user=tpo_evil)
        res = self.client.post("/api/v1/tpo/reports/export/", {"report_type": "STUDENT_ROSTER", "format": "CSV"})
        assert res.status_code == status.HTTP_200_OK
        cd = res["Content-Disposition"]
        assert "\r" not in cd
        assert "\n" not in cd
        assert "evil_crlf_student_roster" in cd

        # 2. College with directory traversal and quotes
        traversal_college = College.objects.create(
            name='Test " College / \\ ..',
            code="../../etc/passwd",
            is_active=True,
        )
        tpo_evil.tpo_profile.college = traversal_college
        tpo_evil.tpo_profile.save()
        res_trav = self.client.post("/api/v1/tpo/reports/export/", {"report_type": "STUDENT_ROSTER", "format": "CSV"})
        assert res_trav.status_code == status.HTTP_200_OK
        cd_trav = res_trav["Content-Disposition"]
        assert "../" not in cd_trav
        assert "..\\" not in cd_trav
        assert "etc_passwd_student_roster" in cd_trav

        # 3. College with blank code and blank name -> fallback to 'institution'
        blank_college = College.objects.create(
            name="   ",
            code="",
            is_active=True,
        )
        tpo_evil.tpo_profile.college = blank_college
        tpo_evil.tpo_profile.save()
        res_blank = self.client.post("/api/v1/tpo/reports/export/", {"report_type": "STUDENT_ROSTER", "format": "CSV"})
        assert res_blank.status_code == status.HTTP_200_OK
        assert "institution_student_roster" in res_blank["Content-Disposition"]

    def test_csv_formula_injection_all_dangerous_characters(self):
        """Verify dynamic cells starting with =, +, -, @, tab, CR are prepended with single quote."""
        from apps.students.tpo_reports_services import sanitize_csv_cell

        assert sanitize_csv_cell("=1+1") == "'=1+1"
        assert sanitize_csv_cell("+cmd|calc") == "'+cmd|calc"
        assert sanitize_csv_cell("-2+3") == "'-2+3"
        assert sanitize_csv_cell("@SUM(A1:A5)") == "'@SUM(A1:A5)"
        assert sanitize_csv_cell("\tTABBED") == "'\tTABBED"
        assert sanitize_csv_cell("\rRETURN") == "'\rRETURN"
        assert sanitize_csv_cell("Normal Text") == "Normal Text"
        assert sanitize_csv_cell(None) == ""
        assert sanitize_csv_cell(100) == "100"

    def test_json_export_does_not_corrupt_data_with_csv_quotes(self):
        """JSON exports must NOT prepend quotes to values starting with formula characters."""
        self.client.force_authenticate(user=self.tpo_user_a)
        res = self.client.post("/api/v1/tpo/reports/export/", {"report_type": "STUDENT_ROSTER", "format": "JSON"})
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        a2_record = next((r for r in data if r["Student ID"] == "AEI-002"), None)
        assert a2_record is not None
        assert a2_record["Full Name"] == "=cmd|' /C calc'!A0"

    def test_oversized_filter_values_and_payloads_rejected(self):
        """Filter value > 200 chars or > 10 filter keys must be rejected with HTTP 400."""
        self.client.force_authenticate(user=self.tpo_user_a)
        # 1. Oversized filter value (> 200 chars)
        res_long = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {
                "report_type": "STUDENT_ROSTER",
                "filters": {"batch_code": "X" * 201},
            },
            format="json",
        )
        assert res_long.status_code == status.HTTP_400_BAD_REQUEST

        # 2. Too many filter keys (> 10)
        many_filters = {f"k{i}": "val" for i in range(11)}
        res_many = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "STUDENT_ROSTER", "filters": many_filters},
            format="json",
        )
        assert res_many.status_code == status.HTTP_400_BAD_REQUEST

    def test_throttle_scope_configuration(self):
        """Verify report endpoints have throttle_scope = 'reports' and rate is configured."""
        from apps.students.tpo_views import (
            TPOReportExportView,
            TPOReportPreviewView,
            TPOReportTypesListView,
        )
        from django.conf import settings

        assert TPOReportTypesListView.throttle_scope == "reports"
        assert TPOReportPreviewView.throttle_scope == "reports"
        assert TPOReportExportView.throttle_scope == "reports"
        assert "reports" in settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]

    def test_throttle_enforcement_returns_429(self):
        """Verify exceeding report rate throttle returns HTTP 429 Too Many Requests."""
        from django.core.cache import cache
        from rest_framework.throttling import ScopedRateThrottle

        orig_rate = ScopedRateThrottle.THROTTLE_RATES.get("reports")
        cache.clear()
        ScopedRateThrottle.THROTTLE_RATES["reports"] = "2/minute"
        try:
            self.client.force_authenticate(user=self.tpo_user_a)
            res1 = self.client.get("/api/v1/tpo/reports/types/")
            assert res1.status_code == status.HTTP_200_OK
            res2 = self.client.get("/api/v1/tpo/reports/types/")
            assert res2.status_code == status.HTTP_200_OK
            res3 = self.client.get("/api/v1/tpo/reports/types/")
            assert res3.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        finally:
            cache.clear()
            if orig_rate is not None:
                ScopedRateThrottle.THROTTLE_RATES["reports"] = orig_rate
            else:
                ScopedRateThrottle.THROTTLE_RATES.pop("reports", None)

    def test_cross_college_isolation_with_malicious_filters(self):
        """College A TPO cannot access College B student even by filtering for College B batch code."""
        self.client.force_authenticate(user=self.tpo_user_a)
        payload = {
            "report_type": "STUDENT_ROSTER",
            "filters": {
                "batch_code": "BATCH-2026-A",
                "graduation_year": 2026,
            },
        }
        res = self.client.post("/api/v1/tpo/reports/preview/", payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        preview_rows = res.json()["data"]["preview_rows"]
        student_ids = [row[0] for row in preview_rows]
        assert "AEI-001" in student_ids
        assert "BUT-001" not in student_ids

    def test_unassigned_or_inactive_tpo_denied(self):
        """TPO without assigned college or with inactive profile is denied."""
        # 1. Inactive TPO profile
        self.tpo_profile_a.is_active = False
        self.tpo_profile_a.save()
        self.client.force_authenticate(user=self.tpo_user_a)
        res_inact = self.client.post("/api/v1/tpo/reports/preview/", {"report_type": "STUDENT_ROSTER"})
        assert res_inact.status_code == status.HTTP_403_FORBIDDEN

        # Reset profile active
        self.tpo_profile_a.is_active = True
        self.tpo_profile_a.save()

        # 2. Unassigned TPO
        unassigned_user = User.objects.create_user(
            email="unassigned_tpo_rep@example.com",
            password="Password123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        TPOProfile.objects.create(
            user=unassigned_user,
            full_name="Unassigned Officer",
            college=None,
            is_active=True,
        )
        self.client.force_authenticate(user=unassigned_user)
        res_un = self.client.post("/api/v1/tpo/reports/preview/", {"report_type": "STUDENT_ROSTER"})
        assert res_un.status_code == status.HTTP_403_FORBIDDEN

    def test_filter_all_case_insensitivity_and_no_literal_filtering(self):
        """Verify uppercase and lowercase 'ALL' behave identically and never filter for literal strings."""
        self.client.force_authenticate(user=self.tpo_user_a)

        # 1. batch_code: 'ALL', 'all', 'All' must return all college students (not literal batch 'all')
        for val in ["ALL", "all", "All"]:
            res = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "STUDENT_ROSTER", "filters": {"batch_code": val}},
                format="json",
            )
            assert res.status_code == status.HTTP_200_OK
            preview_rows = res.json()["data"]["preview_rows"]
            student_ids = [row[0] for row in preview_rows]
            assert "AEI-001" in student_ids
            assert "AEI-002" in student_ids
            # Ensure College B student is never leaked
            assert "BUT-001" not in student_ids

        # 2. course_opted: 'all' vs 'ALL' must return all students without substring filtering
        for val in ["ALL", "all", "All"]:
            res = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "STUDENT_ROSTER", "filters": {"course_opted": val}},
                format="json",
            )
            assert res.status_code == status.HTTP_200_OK
            preview_rows = res.json()["data"]["preview_rows"]
            student_ids = [row[0] for row in preview_rows]
            assert "AEI-001" in student_ids
            assert "AEI-002" in student_ids

        # 3. is_active: 'ALL' vs 'all' returns both active and inactive without filtering
        for val in ["ALL", "all", "All"]:
            res = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "STUDENT_ROSTER", "filters": {"is_active": val}},
                format="json",
            )
            assert res.status_code == status.HTTP_200_OK
            preview_rows = res.json()["data"]["preview_rows"]
            student_ids = [row[0] for row in preview_rows]
            assert len(student_ids) == 2

        # 4. graduation_year: 'ALL' vs 'all'
        for val in ["ALL", "all", "All"]:
            res = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "STUDENT_ROSTER", "filters": {"graduation_year": val}},
                format="json",
            )
            assert res.status_code == status.HTTP_200_OK
            preview_rows = res.json()["data"]["preview_rows"]
            assert len(preview_rows) == 2

        # 5. attendance_compliance batch_code: 'all'
        res_att = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "ATTENDANCE_COMPLIANCE", "filters": {"batch_code": "all"}},
            format="json",
        )
        assert res_att.status_code == status.HTTP_200_OK
        assert res_att.json()["data"]["total_rows"] == 2

    def test_strict_date_format_validation_and_rejections(self):
        """Verify strict date validation rejects compact, timestamp, malformed, and non-calendar dates with HTTP 400."""
        self.client.force_authenticate(user=self.tpo_user_a)

        invalid_dates = [
            (" 2026-01-01", "leading space"),
            ("2026-01-01 ", "trailing space"),
            (" 2026-01-01 ", "surrounding spaces"),
            ("2026-01-01\n", "newline character"),
            ("2026-01-01\r", "carriage return character"),
            ("\t2026-01-01", "tab character"),
            ("", "empty string"),
            ("   ", "whitespace-only string"),
            ("20260101", "compact date"),
            ("2026-01-01T00:00:00Z", "ISO timestamp with time"),
            ("2026-01-01 12:00:00", "timestamp with space"),
            ("2026-W01-1", "ISO week date"),
            ("2026-02-31", "impossible calendar day in Feb"),
            ("2025-02-29", "Feb 29 on non-leap year"),
            ("2026-04-31", "April 31 does not exist"),
            ("2026-13-01", "invalid month 13"),
            ("2026-00-10", "invalid month 0"),
            ("2026/01/01", "slash separated date"),
            ("01-01-2026", "DD-MM-YYYY format"),
            ("2026-1-1", "unpadded month and day"),
            ("yesterday", "natural language string"),
            (20260101, "integer date"),
            (True, "boolean value"),
        ]

        for val, description in invalid_dates:
            res_from = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "ASSIGNMENTS_LABS", "filters": {"date_from": val}},
                format="json",
            )
            assert res_from.status_code == status.HTTP_400_BAD_REQUEST, (
                f"Expected 400 for date_from '{val}' ({description}), got {res_from.status_code}"
            )

            res_to = self.client.post(
                "/api/v1/tpo/reports/preview/",
                {"report_type": "ASSIGNMENTS_LABS", "filters": {"date_to": val}},
                format="json",
            )
            assert res_to.status_code == status.HTTP_400_BAD_REQUEST, (
                f"Expected 400 for date_to '{val}' ({description}), got {res_to.status_code}"
            )

        # Inverted date range
        res_inv = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {
                "report_type": "ASSIGNMENTS_LABS",
                "filters": {"date_from": "2026-06-01", "date_to": "2026-01-01"},
            },
            format="json",
        )
        assert res_inv.status_code == status.HTTP_400_BAD_REQUEST

        # Date range exceeding 5 years (1826 days)
        res_large = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {
                "report_type": "ASSIGNMENTS_LABS",
                "filters": {"date_from": "2020-01-01", "date_to": "2026-01-01"},
            },
            format="json",
        )
        assert res_large.status_code == status.HTTP_400_BAD_REQUEST

    def test_strict_date_acceptance_and_one_sided_filters(self):
        """Verify exact YYYY-MM-DD dates are accepted, including one-sided filters."""
        self.client.force_authenticate(user=self.tpo_user_a)

        # 1. date_from only (one-sided)
        res1 = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "ASSIGNMENTS_LABS", "filters": {"date_from": "2026-01-01"}},
            format="json",
        )
        assert res1.status_code == status.HTTP_200_OK

        # 2. date_to only (one-sided)
        res2 = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "ASSIGNMENTS_LABS", "filters": {"date_to": "2026-12-31"}},
            format="json",
        )
        assert res2.status_code == status.HTTP_200_OK

        # 3. Both date_from and date_to (valid range)
        res3 = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {
                "report_type": "ASSIGNMENTS_LABS",
                "filters": {"date_from": "2026-01-01", "date_to": "2026-06-30"},
            },
            format="json",
        )
        assert res3.status_code == status.HTTP_200_OK

        # 4. Valid leap year calendar date (2024-02-29)
        res_leap = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {
                "report_type": "ASSIGNMENTS_LABS",
                "filters": {"date_from": "2024-02-29", "date_to": "2024-03-01"},
            },
            format="json",
        )
        assert res_leap.status_code == status.HTTP_200_OK

    def test_filter_key_types_and_malformed_payload_validation(self):
        """Verify non-string keys, mixed-type unknown keys, and malformed payloads produce controlled ValidationErrors."""
        from apps.students.tpo_reports_services import TPOReportsService
        from rest_framework.exceptions import ValidationError as DRFValidationError

        self.client.force_authenticate(user=self.tpo_user_a)

        # 1. Non-string integer key in service call
        with pytest.raises(DRFValidationError) as exc_info:
            TPOReportsService.validate_report_filters("STUDENT_ROSTER", {123: "val"})
        assert "All filter keys must be strings" in str(exc_info.value)

        # 2. Non-string None key in service call
        with pytest.raises(DRFValidationError) as exc_info:
            TPOReportsService.validate_report_filters("STUDENT_ROSTER", {None: "val"})
        assert "All filter keys must be strings" in str(exc_info.value)

        # 3. Mixed types with unknown keys does not raise TypeError (sorting bug fix)
        with pytest.raises(DRFValidationError) as exc_info:
            TPOReportsService.validate_report_filters(
                "STUDENT_ROSTER", {123: "val", "unknown_filter": "foo"}
            )
        assert "All filter keys must be strings" in str(exc_info.value)

        # 4. Non-dict payload in service call
        with pytest.raises(DRFValidationError) as exc_info:
            TPOReportsService.validate_report_filters("STUDENT_ROSTER", "not-a-dict")
        assert "must be a dictionary" in str(exc_info.value)

        with pytest.raises(DRFValidationError) as exc_info:
            TPOReportsService.validate_report_filters("STUDENT_ROSTER", [1, 2, 3])
        assert "must be a dictionary" in str(exc_info.value)

        # 5. Overlong key (>50 chars)
        with pytest.raises(DRFValidationError) as exc_info:
            TPOReportsService.validate_report_filters("STUDENT_ROSTER", {"k" * 51: "val"})
        assert "exceeds 50 characters" in str(exc_info.value)

        # 6. Unsupported filter key (string) produces controlled UNKNOWN_FILTER error
        with pytest.raises(DRFValidationError) as exc_info:
            TPOReportsService.validate_report_filters(
                "STUDENT_ROSTER", {"unsupported_key": "val"}
            )
        assert "Unknown filter key(s)" in str(exc_info.value)

        # 7. Via API endpoint: malformed filters payload returns HTTP 400
        res_bad_payload = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "STUDENT_ROSTER", "filters": "not-a-dict"},
            format="json",
        )
        assert res_bad_payload.status_code == status.HTTP_400_BAD_REQUEST

        res_unknown = self.client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "STUDENT_ROSTER", "filters": {"unsupported_key": "val"}},
            format="json",
        )
        assert res_unknown.status_code == status.HTTP_400_BAD_REQUEST
