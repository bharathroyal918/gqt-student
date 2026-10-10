"""Phase 7: End-to-End Production Readiness, Security Audit & Regression Test Matrix."""

from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import AuditLog, TPOProfile
from apps.assignments.models import CodeSubmission, CodingQuestion
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.students.models import AttendanceRecord, College, StudentProfile

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def setup_phase7_data(db):
    """Create comprehensive multi-college, multi-student, multi-role test fixture."""
    # 1. Colleges
    college_a = College.objects.create(
        name="Apex Institute of Technology",
        code="AIT",
        city="Bangalore",
        state="Karnataka",
        is_active=True,
    )
    college_b = College.objects.create(
        name="Beacon Engineering College",
        code="BEC",
        city="Hyderabad",
        state="Telangana",
        is_active=True,
    )
    inactive_college = College.objects.create(
        name="Closed Technical Institute",
        code="CTI",
        city="Chennai",
        state="Tamil Nadu",
        is_active=False,
    )

    # 2. Admin User
    admin_user = User.objects.create_user(
        email="admin.phase7@gqt.local",
        password="AdminSecurePassword123!",
        role=User.RoleChoices.ADMIN,
        is_active=True,
    )

    # 3. TPO Users
    tpo_user_a = User.objects.create_user(
        email="tpo.apex@gqt.local",
        password="TPOSecurePassword123!",
        role=User.RoleChoices.TPO,
        is_active=True,
    )
    tpo_profile_a = TPOProfile.objects.create(
        user=tpo_user_a,
        college=college_a,
        full_name="Rajesh Sharma",
        designation="Head of Training & Placements",
        department="Computer Science",
        is_active=True,
        assigned_by=admin_user,
        assigned_at=timezone.now(),
    )

    tpo_user_b = User.objects.create_user(
        email="tpo.beacon@gqt.local",
        password="TPOSecurePassword123!",
        role=User.RoleChoices.TPO,
        is_active=True,
    )
    tpo_profile_b = TPOProfile.objects.create(
        user=tpo_user_b,
        college=college_b,
        full_name="Priya Patel",
        designation="Senior Placement Officer",
        department="Information Technology",
        is_active=True,
        assigned_by=admin_user,
        assigned_at=timezone.now(),
    )

    tpo_user_unassigned = User.objects.create_user(
        email="tpo.unassigned@gqt.local",
        password="TPOSecurePassword123!",
        role=User.RoleChoices.TPO,
        is_active=True,
    )
    tpo_profile_unassigned = TPOProfile.objects.create(
        user=tpo_user_unassigned,
        college=None,
        full_name="Vikram Singh",
        designation="Placement Coordinator",
        is_active=True,
    )

    tpo_user_inactive = User.objects.create_user(
        email="tpo.inactive@gqt.local",
        password="TPOSecurePassword123!",
        role=User.RoleChoices.TPO,
        is_active=True,
    )
    tpo_profile_inactive = TPOProfile.objects.create(
        user=tpo_user_inactive,
        college=college_a,
        full_name="Inactive Officer",
        designation="Former TPO",
        is_active=False,
    )

    # 4. Student Users for College A
    student_u1 = User.objects.create_user(
        email="student.apex1@gqt.local",
        password="StudentPassword123!",
        role=User.RoleChoices.STUDENT,
        is_active=True,
    )
    student_p1 = StudentProfile.objects.create(
        user=student_u1,
        college=college_a,
        college_name=college_a.name,
        student_id_number="AIT-CS-001",
        full_name="Aarav Kumar",
        batch_code="2025-CS-A",
        branch="Computer Science",
        course_opted="Full Stack Java",
        attendance_percentage=Decimal("88.50"),
        total_points=Decimal("250.00"),
        current_streak_days=7,
        highest_streak_days=10,
    )

    student_u2_support = User.objects.create_user(
        email="student.apex2@gqt.local",
        password="StudentPassword123!",
        role=User.RoleChoices.STUDENT,
        is_active=True,
    )
    student_p2_support = StudentProfile.objects.create(
        user=student_u2_support,
        college=college_a,
        college_name=college_a.name,
        student_id_number="AIT-CS-002",
        full_name="Sneha Rao",
        batch_code="2025-CS-A",
        branch="Computer Science",
        course_opted="Full Stack Java",
        attendance_percentage=Decimal("62.00"),  # Low attendance
        total_points=Decimal("20.00"),
        current_streak_days=0,
        highest_streak_days=5,
    )

    # Legacy text-only student for College A
    student_u_legacy = User.objects.create_user(
        email="student.legacy@gqt.local",
        password="StudentPassword123!",
        role=User.RoleChoices.STUDENT,
        is_active=True,
    )
    student_p_legacy = StudentProfile.objects.create(
        user=student_u_legacy,
        college=None,
        college_name="Apex Institute of Technology",
        student_id_number="AIT-LEGACY-003",
        full_name="Legacy Student",
        batch_code="2025-CS-A",
        branch="Computer Science",
        attendance_percentage=Decimal("80.00"),
        total_points=Decimal("150.00"),
        current_streak_days=3,
        highest_streak_days=5,
    )

    # 5. Student Users for College B
    student_u_b = User.objects.create_user(
        email="student.beacon1@gqt.local",
        password="StudentPassword123!",
        role=User.RoleChoices.STUDENT,
        is_active=True,
    )
    student_p_b = StudentProfile.objects.create(
        user=student_u_b,
        college=college_b,
        college_name=college_b.name,
        student_id_number="BEC-IT-001",
        full_name="Karthik Reddy",
        batch_code="2025-IT-B",
        branch="Information Technology",
        course_opted="Python AI/ML",
        attendance_percentage=Decimal("94.00"),
        total_points=Decimal("500.00"),
        current_streak_days=15,
        highest_streak_days=20,
    )

    # Conflicting student: Relational FK = College B, but text = Apex Institute of Technology
    student_u_conflict = User.objects.create_user(
        email="student.conflict@gqt.local",
        password="StudentPassword123!",
        role=User.RoleChoices.STUDENT,
        is_active=True,
    )
    student_p_conflict = StudentProfile.objects.create(
        user=student_u_conflict,
        college=college_b,
        college_name="Apex Institute of Technology",
        student_id_number="BEC-CONFLICT-002",
        full_name="Conflict Student",
        batch_code="2025-IT-B",
        branch="Information Technology",
        attendance_percentage=Decimal("90.00"),
        total_points=Decimal("300.00"),
        current_streak_days=4,
        highest_streak_days=8,
    )

    # Courses & Modules
    course_java = Course.objects.create(
        title="Full Stack Java Development",
        slug="full-stack-java-p7",
        is_published=True,
    )
    mod1 = Module.objects.create(
        course=course_java,
        title="Java Core Fundamentals",
        slug="java-core-p7",
        order_index=1,
        is_published=True,
    )
    mod2 = Module.objects.create(
        course=course_java,
        title="Spring Boot & Microservices",
        slug="spring-boot-p7",
        order_index=2,
        is_published=True,
    )

    CourseEnrollment.objects.create(
        student=student_p1,
        course=course_java,
        status=CourseEnrollment.EnrollmentStatus.ACTIVE,
    )
    StudentModuleProgress.objects.create(
        student=student_p1,
        module=mod1,
        status=StudentModuleProgress.ModuleStatus.COMPLETED,
    )

    # Coding Questions & Submissions
    question = CodingQuestion.objects.create(
        module=mod1,
        title="Two Sum Problem",
        slug="two-sum-problem-p7",
        difficulty=CodingQuestion.DifficultyChoices.EASY,
        points=Decimal("50.00"),
        is_active=True,
    )
    CodeSubmission.objects.create(
        student=student_p1,
        question=question,
        language="java",
        source_code="class Solution {}",
        status=CodeSubmission.SubmissionStatus.ACCEPTED,
        score_awarded=Decimal("50.00"),
        passed_test_cases=5,
        total_test_cases=5,
    )

    return {
        "colleges": {"a": college_a, "b": college_b, "inactive": inactive_college},
        "admin": admin_user,
        "tpos": {
            "a": tpo_user_a,
            "b": tpo_user_b,
            "unassigned": tpo_user_unassigned,
            "inactive": tpo_user_inactive,
        },
        "profiles": {
            "tpo_a": tpo_profile_a,
            "tpo_b": tpo_profile_b,
            "tpo_unassigned": tpo_profile_unassigned,
            "tpo_inactive": tpo_profile_inactive,
        },
        "students": {
            "a1": student_p1,
            "a2_support": student_p2_support,
            "a_legacy": student_p_legacy,
            "b1": student_p_b,
            "conflict": student_p_conflict,
        },
        "student_users": {
            "a1": student_u1,
            "b1": student_u_b,
        },
        "course": course_java,
        "question": question,
    }


@pytest.mark.django_db
class TestPhase7RoleAndPermissionIsolation:
    """Security audit of role isolation, unauthenticated access, and privilege escalation prevention."""

    def test_anonymous_access_denied_on_all_tpo_endpoints(self, api_client, setup_phase7_data):
        endpoints = [
            ("/api/v1/tpo/me/", "GET"),
            ("/api/v1/tpo/college/", "GET"),
            ("/api/v1/tpo/college/summary/", "GET"),
            ("/api/v1/tpo/college/students/", "GET"),
            (f"/api/v1/tpo/college/students/{setup_phase7_data['students']['a1'].id}/", "GET"),
            ("/api/v1/tpo/analytics/learning-progress/", "GET"),
            ("/api/v1/tpo/analytics/assignments-labs/", "GET"),
            ("/api/v1/tpo/analytics/attendance/", "GET"),
            ("/api/v1/tpo/analytics/trends/", "GET"),
            ("/api/v1/tpo/analytics/students-needing-support/", "GET"),
            ("/api/v1/tpo/analytics/leaderboard/", "GET"),
            ("/api/v1/tpo/reports/types/", "GET"),
            ("/api/v1/tpo/reports/preview/", "POST"),
            ("/api/v1/tpo/reports/export/", "POST"),
        ]
        for url, method in endpoints:
            if method == "GET":
                response = api_client.get(url)
            else:
                response = api_client.post(url, {"report_type": "STUDENT_ROSTER"})
            assert response.status_code == 401, f"Expected 401 for anonymous access to {url}, got {response.status_code}"

    def test_student_cannot_access_tpo_endpoints(self, api_client, setup_phase7_data):
        api_client.force_authenticate(user=setup_phase7_data["student_users"]["a1"])
        endpoints = [
            "/api/v1/tpo/me/",
            "/api/v1/tpo/college/summary/",
            "/api/v1/tpo/college/students/",
            "/api/v1/tpo/reports/types/",
        ]
        for url in endpoints:
            response = api_client.get(url)
            assert response.status_code == 403, f"Expected 403 for student accessing {url}, got {response.status_code}"

    def test_tpo_cannot_access_admin_endpoints(self, api_client, setup_phase7_data):
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["a"])
        tpo_a_id = setup_phase7_data["profiles"]["tpo_a"].id
        admin_endpoints = [
            "/api/v1/admin/tpos/",
            f"/api/v1/admin/tpos/{tpo_a_id}/",
            f"/api/v1/admin/tpos/{tpo_a_id}/reassign-college/",
            f"/api/v1/admin/tpos/{tpo_a_id}/audit-history/",
        ]
        for url in admin_endpoints:
            response = api_client.get(url)
            assert response.status_code == 403, f"Expected 403 for TPO accessing admin {url}, got {response.status_code}"

    def test_inactive_tpo_profile_denied(self, api_client, setup_phase7_data):
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["inactive"])
        response = api_client.get("/api/v1/tpo/college/summary/")
        assert response.status_code == 403

    def test_unassigned_tpo_denied_dashboard_and_reports(self, api_client, setup_phase7_data):
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["unassigned"])
        response = api_client.get("/api/v1/tpo/college/summary/")
        assert response.status_code == 403

    def test_tpo_student_endpoints_are_read_only(self, api_client, setup_phase7_data):
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["a"])
        student_id = setup_phase7_data["students"]["a1"].id
        url = f"/api/v1/tpo/college/students/{student_id}/"

        post_res = api_client.post(url, {"full_name": "Tampered Name"})
        assert post_res.status_code == 405

        patch_res = api_client.patch(url, {"total_points": 9999})
        assert patch_res.status_code == 405

        delete_res = api_client.delete(url)
        assert delete_res.status_code == 405


@pytest.mark.django_db
class TestPhase7CollegeIsolationAndCrossCollegeProtection:
    """Strict verification of multi-tenant institution isolation across all endpoints."""

    def test_conflicting_relational_foreign_key_not_leaked(self, api_client, setup_phase7_data):
        """Student with FK=College B but text='Apex Institute' must NEVER appear in College A."""
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["a"])

        # 1. Roster check
        roster_res = api_client.get("/api/v1/tpo/college/students/")
        assert roster_res.status_code == 200
        student_ids = [s["id"] for s in roster_res.data["data"]]
        assert str(setup_phase7_data["students"]["conflict"].id) not in student_ids

        # 2. Report Export check
        export_res = api_client.post(
            "/api/v1/tpo/reports/export/",
            {"report_type": "STUDENT_ROSTER", "format": "JSON"},
            format="json",
        )
        assert export_res.status_code == 200
        json_data = export_res.json()
        exported_ids = [r["Student ID"] for r in json_data["data"]]
        assert "BEC-CONFLICT-002" not in exported_ids

    def test_legitimate_legacy_record_included(self, api_client, setup_phase7_data):
        """Student with FK=NULL but text='Apex Institute of Technology' IS included."""
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["a"])
        roster_res = api_client.get("/api/v1/tpo/college/students/")
        assert roster_res.status_code == 200
        student_ids = [s["id"] for s in roster_res.data["data"]]
        assert str(setup_phase7_data["students"]["a_legacy"].id) in student_ids

    def test_cross_college_student_detail_idor_denied(self, api_client, setup_phase7_data):
        """TPO of College A attempting to inspect College B student by UUID receives 404."""
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["a"])
        college_b_student_id = setup_phase7_data["students"]["b1"].id
        response = api_client.get(f"/api/v1/tpo/college/students/{college_b_student_id}/")
        assert response.status_code == 404
        assert response.data["error"]["code"] == "STUDENT_NOT_FOUND"

    def test_immediate_reassignment_isolation(self, api_client, setup_phase7_data):
        """When TPO A is reassigned to College B, they immediately see only College B data."""
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["a"])

        # Initial: College A (sees AIT-CS-001)
        res1 = api_client.get("/api/v1/tpo/college/students/")
        ids1 = [s["id"] for s in res1.data["data"]]
        assert str(setup_phase7_data["students"]["a1"].id) in ids1
        assert str(setup_phase7_data["students"]["b1"].id) not in ids1

        # Admin reassigns TPO A to College B
        tpo_prof = setup_phase7_data["profiles"]["tpo_a"]
        tpo_prof.college = setup_phase7_data["colleges"]["b"]
        tpo_prof.save()

        # Immediate check on subsequent request: sees College B, zero College A
        res2 = api_client.get("/api/v1/tpo/college/students/")
        ids2 = [s["id"] for s in res2.data["data"]]
        assert str(setup_phase7_data["students"]["b1"].id) in ids2
        assert str(setup_phase7_data["students"]["a1"].id) not in ids2


@pytest.mark.django_db
class TestPhase7ReportExportSecurityAndAuditing:
    """Security audit of formula injection, encoding, format validation, and audit trail."""

    def test_formula_injection_mitigated_in_csv_export(self, api_client, setup_phase7_data):
        """Ensure dangerous prefix characters are safely escaped in CSV cells."""
        # Create student with formula injection vector in full name
        hacked_user = User.objects.create_user(
            email="hacker@gqt.local",
            password="HackerPass123!",
            role=User.RoleChoices.STUDENT,
        )
        StudentProfile.objects.create(
            user=hacked_user,
            college=setup_phase7_data["colleges"]["a"],
            student_id_number="AIT-FORMULA-001",
            full_name="=SUM(1+1)*cmd|' /C calc'!A0",
            batch_code="2025-CS-A",
            attendance_percentage=Decimal("75.00"),
            total_points=Decimal("100.00"),
            current_streak_days=0,
            highest_streak_days=0,
        )

        api_client.force_authenticate(user=setup_phase7_data["tpos"]["a"])
        response = api_client.post(
            "/api/v1/tpo/reports/export/",
            {"report_type": "STUDENT_ROSTER", "format": "CSV"},
            format="json",
        )
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/csv")
        csv_text = response.content.decode("utf-8-sig")

        # Cell must be prepended with single quote
        assert "'=SUM(1+1)*cmd|' /C calc'!A0" in csv_text

    def test_utf8_bom_present_in_csv_export(self, api_client, setup_phase7_data):
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["a"])
        response = api_client.post(
            "/api/v1/tpo/reports/export/",
            {"report_type": "STUDENT_ROSTER", "format": "CSV"},
            format="json",
        )
        assert response.status_code == 200
        # Check UTF-8 BOM bytes (\xef\xbb\xbf)
        assert response.content.startswith(b"\xef\xbb\xbf")

    def test_audit_log_recorded_for_preview_and_export(self, api_client, setup_phase7_data):
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["a"])
        AuditLog.objects.filter(actor=setup_phase7_data["tpos"]["a"]).delete()

        # 1. Preview
        prev_res = api_client.post(
            "/api/v1/tpo/reports/preview/",
            {"report_type": "ATTENDANCE_COMPLIANCE"},
            format="json",
        )
        assert prev_res.status_code == 200

        # 2. Export
        exp_res = api_client.post(
            "/api/v1/tpo/reports/export/",
            {"report_type": "ATTENDANCE_COMPLIANCE", "format": "JSON"},
            format="json",
        )
        assert exp_res.status_code == 200

        # Verify Audit Log
        logs = AuditLog.objects.filter(actor=setup_phase7_data["tpos"]["a"]).order_by("created_at")
        assert logs.count() == 2
        assert logs[0].action == "TPO_REPORT_PREVIEW"
        assert logs[1].action == "TPO_REPORT_EXPORT"
        assert logs[0].payload["report_type"] == "ATTENDANCE_COMPLIANCE"


@pytest.mark.django_db
class TestPhase7DataIntegrityAndParity:
    """Verifies metric consistency across dashboard, analytics, and exports."""

    def test_metric_parity_between_dashboard_and_summary_report(self, api_client, setup_phase7_data):
        api_client.force_authenticate(user=setup_phase7_data["tpos"]["a"])

        # 1. Dashboard summary
        dash_res = api_client.get("/api/v1/tpo/college/summary/")
        assert dash_res.status_code == 200
        dash_data = dash_res.data["data"]

        # 2. Report export
        exp_res = api_client.post(
            "/api/v1/tpo/reports/export/",
            {"report_type": "COLLEGE_SUMMARY", "format": "JSON"},
            format="json",
        )
        assert exp_res.status_code == 200
        exp_records = exp_res.json()["data"]

        # Cross-verify key institutional metrics
        total_students_row = next(r for r in exp_records if r["Metric Name"] == "Total Registered Students")
        assert int(total_students_row["Metric Value"]) == dash_data["total_students"]

        active_students_row = next(r for r in exp_records if r["Metric Name"] == "Active Students")
        assert int(active_students_row["Metric Value"]) == dash_data["active_students"]
