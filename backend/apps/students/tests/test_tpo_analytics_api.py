"""Automated tests for Phase 5 TPO Academic Performance & Learning Analytics APIs."""

from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import TPOProfile, User
from apps.assignments.models import CodeSubmission, CodingQuestion
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.scoring.models import ScoreRecord
from apps.students.models import AttendanceRecord, College, StudentProfile

User = get_user_model()


@pytest.mark.django_db
class TestTPOAnalyticsAPIs:
    """Test suite covering Phase 5 TPO Analytics endpoints and isolation rules."""

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
            email="tpo_alpha_analytics@example.com",
            password="SecureTPOCreds123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        self.tpo_profile_a = TPOProfile.objects.create(
            user=self.tpo_user_a,
            full_name="Alpha Analytics Officer",
            college=self.college_a,
            is_active=True,
        )

        # 3. Create TPO for College B
        self.tpo_user_b = User.objects.create_user(
            email="tpo_beta_analytics@example.com",
            password="SecureTPOCreds123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        self.tpo_profile_b = TPOProfile.objects.create(
            user=self.tpo_user_b,
            full_name="Beta Analytics Officer",
            college=self.college_b,
            is_active=True,
        )

        # 4. Create Students for College A
        # Student A1: High performer
        self.student_user_a1 = User.objects.create_user(
            email="alice@alpha.edu",
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

        # Student A2: Needs support (Low attendance, zero submissions, 0 points)
        self.student_user_a2 = User.objects.create_user(
            email="aaron@alpha.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
        )
        self.student_a2 = StudentProfile.objects.create(
            user=self.student_user_a2,
            student_id_number="AEI-002",
            full_name="Aaron Alpha",
            college=self.college_a,
            college_name=self.college_a.name,
            batch_code="BATCH-2026-B",
            branch="Information Science",
            course_opted="Full Stack Development",
            attendance_percentage=Decimal("65.00"),
            total_points=Decimal("0.00"),
            total_classes=50,
            attended_classes=32,
            current_streak_days=0,
            highest_streak_days=0,
        )

        # Student A3: Legacy record (college FK is NULL, college_name matches)
        self.student_user_a3 = User.objects.create_user(
            email="alex@alpha.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
        )
        self.student_a3 = StudentProfile.objects.create(
            user=self.student_user_a3,
            student_id_number="AEI-003",
            full_name="Alex Alpha Legacy",
            college=None,
            college_name=self.college_a.name,
            batch_code="BATCH-2026-A",
            branch="Computer Science",
            course_opted="Full Stack Development",
            attendance_percentage=Decimal("78.00"),
            total_points=Decimal("200.00"),
            total_classes=50,
            attended_classes=39,
            current_streak_days=2,
            highest_streak_days=5,
        )

        # Student B1: Conflicting Record (college FK is College B, but text says College A)
        self.student_user_b1 = User.objects.create_user(
            email="bob@beta.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
        )
        self.student_b1 = StudentProfile.objects.create(
            user=self.student_user_b1,
            student_id_number="BUT-001",
            full_name="Bob Beta Conflicting",
            college=self.college_b,
            college_name=self.college_a.name,  # Conflicting text field
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

        # 5. Setup Course, Module, Questions, Submissions, ScoreRecords, Progress
        self.course = Course.objects.create(
            title="Full Stack Python",
            slug="full-stack-python",
            is_published=True,
        )
        self.module_1 = Module.objects.create(
            course=self.course,
            title="Module 1: Django Fundamentals",
            slug="module-1-django",
            order_index=1,
            is_published=True,
        )
        self.module_2 = Module.objects.create(
            course=self.course,
            title="Module 2: REST Framework",
            slug="module-2-rest",
            order_index=2,
            is_published=True,
        )

        # Enrollments
        CourseEnrollment.objects.create(
            student=self.student_a1,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )
        CourseEnrollment.objects.create(
            student=self.student_a3,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.COMPLETED,
        )

        # Module progress
        StudentModuleProgress.objects.create(
            student=self.student_a1,
            module=self.module_1,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
        )
        StudentModuleProgress.objects.create(
            student=self.student_a3,
            module=self.module_1,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
        )
        StudentModuleProgress.objects.create(
            student=self.student_a3,
            module=self.module_2,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
        )

        # Coding questions and submissions
        self.question_1 = CodingQuestion.objects.create(
            module=self.module_1,
            title="Two Sum",
            slug="two-sum",
        )
        self.question_2 = CodingQuestion.objects.create(
            module=self.module_1,
            title="Reverse String",
            slug="reverse-string",
        )

        # Alice: 1 accepted submission
        self.sub_alice = CodeSubmission.objects.create(
            student=self.student_a1,
            question=self.question_1,
            language="python",
            source_code="def two_sum(): pass",
            status=CodeSubmission.SubmissionStatus.ACCEPTED,
            score_awarded=Decimal("100.00"),
            passed_test_cases=5,
            total_test_cases=5,
        )
        ScoreRecord.objects.create(
            student=self.student_a1,
            source_type=ScoreRecord.SourceType.ASSIGNMENT,
            source_id=self.sub_alice.id,
            points=Decimal("100.00"),
        )

        # Alex: 1 wrong answer, 1 pending submission
        self.sub_alex_1 = CodeSubmission.objects.create(
            student=self.student_a3,
            question=self.question_2,
            language="python",
            source_code="wrong",
            status=CodeSubmission.SubmissionStatus.WRONG_ANSWER,
            score_awarded=Decimal("0.00"),
            passed_test_cases=2,
            total_test_cases=5,
        )
        self.sub_alex_2 = CodeSubmission.objects.create(
            student=self.student_a3,
            question=self.question_2,
            language="python",
            source_code="pending",
            status=CodeSubmission.SubmissionStatus.PENDING,
            score_awarded=Decimal("0.00"),
            passed_test_cases=0,
            total_test_cases=5,
        )

        # Attendance Record for College A
        AttendanceRecord.objects.create(
            student_profile=self.student_a1,
            date=timezone.localdate(),
            session_title="Django Architecture",
            status=AttendanceRecord.AttendanceStatus.PRESENT,
        )

    # --------------------------------------------------------------------------
    # SECURITY & SCOPING TESTS
    # --------------------------------------------------------------------------

    def test_security_gate_conflicting_foreign_key_not_leaked(self):
        """Bob Beta has college=College B but college_name='Alpha'.

        Authoritative rule: TPO A must NOT see Bob Beta.
        """
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/analytics/learning-progress/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        # Total students in College A should be exactly 3 (Alice, Aaron, and Alex Legacy), NOT Bob.
        assert data["total_students"] == 3
        student_ids = [s["student_id_number"] for s in data["student_progress"]]
        assert "BUT-001" not in student_ids
        assert "AEI-001" in student_ids
        assert "AEI-002" in student_ids
        assert "AEI-003" in student_ids

    def test_security_gate_legacy_record_without_foreign_key_supported(self):
        """Alex Alpha has college=None but college_name='Alpha Engineering Institute'.

        Authoritative rule: Legitimate legacy record is included for TPO A.
        """
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/analytics/leaderboard/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        ids = [item["student_id_number"] for item in data]
        assert "AEI-003" in ids

    # --------------------------------------------------------------------------
    # LEARNING PROGRESS TESTS
    # --------------------------------------------------------------------------

    def test_learning_progress_metrics_accuracy(self):
        """Check course enrollments, module completion breakdown, and student progress statuses."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/analytics/learning-progress/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert data["total_students"] == 3
        assert data["total_courses"] == 1
        assert data["total_modules"] == 2

        # Check course progression
        course_stat = data["course_progression"][0]
        assert course_stat["course_title"] == "Full Stack Python"
        assert course_stat["enrolled_count"] == 2
        assert course_stat["completed_count"] == 1
        assert course_stat["in_progress_count"] == 1

        # Check module completion
        mod_1_stat = next(m for m in data["module_completion"] if m["module_title"] == "Module 1: Django Fundamentals")
        assert mod_1_stat["completed_count"] == 2

        # Check student progress statuses
        progress_map = {s["student_id_number"]: s for s in data["student_progress"]}
        # Alex completed 2 of 2 modules -> COMPLETED
        assert progress_map["AEI-003"]["completed_modules"] == 2
        assert progress_map["AEI-003"]["progress_percentage"] == 100.0
        assert progress_map["AEI-003"]["status"] == "COMPLETED"

        # Alice completed 1 of 2 modules -> ON_TRACK
        assert progress_map["AEI-001"]["completed_modules"] == 1
        assert progress_map["AEI-001"]["progress_percentage"] == 50.0
        assert progress_map["AEI-001"]["status"] == "ON_TRACK"

        # Aaron completed 0 modules and has 0 streak -> NOT_STARTED
        assert progress_map["AEI-002"]["completed_modules"] == 0
        assert progress_map["AEI-002"]["progress_percentage"] == 0.0
        assert progress_map["AEI-002"]["status"] == "NOT_STARTED"

    # --------------------------------------------------------------------------
    # ASSIGNMENTS & LABS TESTS
    # --------------------------------------------------------------------------

    def test_assignments_and_labs_metrics_and_verdicts(self):
        """Test unique participants, attempts, pass rate denominator, and pending exclusion."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/analytics/assignments-labs/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert data["total_students"] == 3
        assert data["participating_students"] == 2  # Alice and Alex
        assert data["unattempted_students"] == 1   # Aaron
        assert data["total_attempts"] == 3
        assert data["unique_questions_attempted"] == 2
        assert data["accepted_submissions"] == 1
        assert data["rejected_submissions"] == 1
        assert data["pending_submissions"] == 1

        # Denominator for pass rate must exclude pending submissions: 1 / (1 + 1) = 50.0%
        assert data["pass_rate_percentage"] == 50.0

        # Verdict breakdown
        assert data["verdict_breakdown"]["ACCEPTED"] == 1
        assert data["verdict_breakdown"]["WRONG_ANSWER"] == 1
        assert data["verdict_breakdown"]["PENDING_OR_QUEUED"] == 1

        # Language stats
        assert len(data["language_stats"]) == 1
        assert data["language_stats"][0]["language"] == "python"
        assert data["language_stats"][0]["total_submissions"] == 3

    # --------------------------------------------------------------------------
    # ATTENDANCE ANALYTICS TESTS
    # --------------------------------------------------------------------------

    def test_attendance_analytics_distribution_and_threshold(self):
        """Test college average, threshold (75%), distribution bands, and critical list."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/analytics/attendance/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert data["total_students"] == 3
        # Average from model calculation: (45/50 + 32/50 + 39/50) / 3 = (90 + 64 + 78) / 3 = 77.33%
        assert data["college_average_attendance"] == 77.33
        assert data["policy_threshold_percentage"] == 75.0

        bands = data["distribution_bands"]
        assert bands["excellent_gte_85"]["count"] == 1      # Alice (90%)
        assert bands["satisfactory_75_to_84"]["count"] == 1  # Alex (78%)
        assert bands["critical_below_75"]["count"] == 1      # Aaron (65%)

        # Critical students list
        assert len(data["critical_students"]) == 1
        assert data["critical_students"][0]["student_id_number"] == "AEI-002"
        assert data["has_session_records"] is True

    # --------------------------------------------------------------------------
    # PERFORMANCE TRENDS TESTS
    # --------------------------------------------------------------------------

    def test_performance_trends_with_records(self):
        """Test historical monthly aggregates."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/analytics/trends/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert data["has_sufficient_history"] is True
        assert len(data["monthly_score_trends"]) >= 1
        assert len(data["monthly_submission_trends"]) >= 1

    def test_performance_trends_empty_college_returns_honest_unavailable_state(self):
        """College with no records returns honest unavailable state rather than mock charts."""
        empty_college = College.objects.create(
            name="Empty Tech Institute",
            code="ETI-999",
            is_active=True,
        )
        empty_tpo_user = User.objects.create_user(
            email="empty_tpo@example.com",
            password="SecureTPOCreds123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        TPOProfile.objects.create(
            user=empty_tpo_user,
            full_name="Empty Officer",
            college=empty_college,
            is_active=True,
        )

        self.client.force_authenticate(user=empty_tpo_user)
        response = self.client.get("/api/v1/tpo/analytics/trends/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert data["has_sufficient_history"] is False
        assert "No student records" in data["unavailable_reason"]
        assert len(data["monthly_score_trends"]) == 0
        assert len(data["monthly_submission_trends"]) == 0

    # --------------------------------------------------------------------------
    # STUDENTS NEEDING SUPPORT TESTS
    # --------------------------------------------------------------------------

    def test_students_needing_support_flags_transparent_reasons(self):
        """Aaron has attendance < 75% and zero submissions and stalled progress."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/analytics/students-needing-support/")
        assert response.status_code == status.HTTP_200_OK

        flagged = response.json()["data"]
        assert len(flagged) >= 1

        aaron_record = next(s for s in flagged if s["student_id_number"] == "AEI-002")
        reasons_codes = [r["code"] for r in aaron_record["reasons"]]
        assert "LOW_ATTENDANCE" in reasons_codes
        assert "ZERO_SUBMISSIONS" in reasons_codes
        assert "STALLED_PROGRESS" in reasons_codes

    def test_students_needing_support_filter_by_risk_type(self):
        """Filter by LOW_ATTENDANCE risk type."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/analytics/students-needing-support/?risk_type=LOW_ATTENDANCE")
        assert response.status_code == status.HTTP_200_OK

        flagged = response.json()["data"]
        assert len(flagged) == 1
        assert flagged[0]["student_id_number"] == "AEI-002"

    # --------------------------------------------------------------------------
    # LEADERBOARD TESTS
    # --------------------------------------------------------------------------

    def test_leaderboard_college_isolation_and_tie_breaking(self):
        """Leaderboard strictly includes College A students and orders by points, attendance, streak."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/analytics/leaderboard/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()["data"]
        assert len(data) == 3
        # Rank 1: Alice (500 pts)
        assert data[0]["student_id_number"] == "AEI-001"
        assert data[0]["rank"] == 1
        assert data[0]["total_points"] == 500.0

        # Rank 2: Alex (200 pts)
        assert data[1]["student_id_number"] == "AEI-003"
        assert data[1]["rank"] == 2

        # Rank 3: Aaron (0 pts)
        assert data[2]["student_id_number"] == "AEI-002"
        assert data[2]["rank"] == 3

        # Bob Beta (College B) must never appear
        ids = [s["student_id_number"] for s in data]
        assert "BUT-001" not in ids
