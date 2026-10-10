"""Automated tests for TPO College Dashboard, Scoped Student Roster, and Performance APIs."""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import TPOProfile, User
from apps.assignments.models import CodeSubmission, CodingQuestion
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module
from apps.scoring.models import ScoreRecord
from apps.students.models import AttendanceRecord, College, StudentProfile

User = get_user_model()


@pytest.mark.django_db
class TestTPODashboardAndRosterAPIs:
    """Test suite covering Phase 4 TPO Dashboard, Scoped Student Roster, and Student Detail endpoints."""

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
            email="tpo_alpha@example.com",
            password="SecureTPOCreds123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        self.tpo_profile_a = TPOProfile.objects.create(
            user=self.tpo_user_a,
            full_name="Alpha TPO Officer",
            college=self.college_a,
            is_active=True,
        )

        # 3. Create TPO for College B
        self.tpo_user_b = User.objects.create_user(
            email="tpo_beta@example.com",
            password="SecureTPOCreds123!",
            role=User.RoleChoices.TPO,
            is_active=True,
        )
        self.tpo_profile_b = TPOProfile.objects.create(
            user=self.tpo_user_b,
            full_name="Beta TPO Officer",
            college=self.college_b,
            is_active=True,
        )

        # 4. Create Students for College A
        self.student_user_a1 = User.objects.create_user(
            email="student_a1@alpha.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
        )
        self.student_profile_a1 = StudentProfile.objects.create(
            user=self.student_user_a1,
            student_id_number="AEI2026001",
            full_name="Alice Alpha",
            college=self.college_a,
            college_name=self.college_a.name,
            batch_code="BATCH-2026-A",
            branch="Computer Science",
            course_opted="Full Stack Development",
            attendance_percentage=Decimal("92.50"),
            total_points=Decimal("350.00"),
            total_classes=40,
            attended_classes=37,
        )

        self.student_user_a2 = User.objects.create_user(
            email="student_a2@alpha.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=False,  # Inactive student
        )
        self.student_profile_a2 = StudentProfile.objects.create(
            user=self.student_user_a2,
            student_id_number="AEI2026002",
            full_name="Aaron Alpha",
            college=self.college_a,
            college_name=self.college_a.name,
            batch_code="BATCH-2026-B",
            branch="Information Science",
            course_opted="Cloud Computing",
            attendance_percentage=Decimal("80.00"),
            total_points=Decimal("150.00"),
            total_classes=40,
            attended_classes=32,
        )

        # 5. Create Student for College B
        self.student_user_b1 = User.objects.create_user(
            email="student_b1@beta.edu",
            password="Password123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
        )
        self.student_profile_b1 = StudentProfile.objects.create(
            user=self.student_user_b1,
            student_id_number="BUT2026001",
            full_name="Bob Beta",
            college=self.college_b,
            college_name=self.college_b.name,
            batch_code="BATCH-2026-A",
            branch="Mechanical Engineering",
            course_opted="Data Science",
            attendance_percentage=Decimal("70.00"),
            total_points=Decimal("500.00"),
        )

        # 6. Additional performance records for Student A1
        self.course = Course.objects.create(
            title="Python Mastery",
            slug="python-mastery",
            is_published=True,
        )
        self.enrollment = CourseEnrollment.objects.create(
            student=self.student_profile_a1,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )
        self.module = Module.objects.create(
            course=self.course,
            title="Module 1: Algorithms",
            slug="module-1-algorithms",
            order_index=1,
        )
        self.question = CodingQuestion.objects.create(
            module=self.module,
            title="Binary Search",
            slug="binary-search",
        )
        self.submission = CodeSubmission.objects.create(
            student=self.student_profile_a1,
            question=self.question,
            language="python",
            source_code="def binary_search(): pass",
            status=CodeSubmission.SubmissionStatus.ACCEPTED,
            score_awarded=Decimal("100.00"),
            passed_test_cases=5,
            total_test_cases=5,
        )
        self.score_rec = ScoreRecord.objects.create(
            student=self.student_profile_a1,
            source_type=ScoreRecord.SourceType.ASSIGNMENT,
            source_id=self.submission.id,
            points=Decimal("100.00"),
        )
        self.attendance = AttendanceRecord.objects.create(
            student_profile=self.student_profile_a1,
            date=timezone.localdate(),
            session_title="Algorithms Lab",
            status=AttendanceRecord.AttendanceStatus.PRESENT,
        )

    # --------------------------------------------------------------------------
    # DASHBOARD SUMMARY TESTS
    # --------------------------------------------------------------------------

    def test_tpo_can_retrieve_college_summary(self):
        """TPO A should retrieve summary data computed strictly from College A."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/college/summary/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]

        # Reconcile counts
        assert data["college"]["name"] == "Alpha Engineering Institute"
        assert data["total_students"] == 2
        assert data["active_students"] == 1
        assert data["inactive_students"] == 1
        assert data["total_submissions"] == 1
        assert data["accepted_submissions"] == 1
        assert len(data["top_performers"]) == 2
        assert data["top_performers"][0]["student_id_number"] == "AEI2026001"
        assert data["top_performers"][0]["total_points"] == 350.0

    def test_inactive_tpo_cannot_retrieve_summary(self):
        """Inactive TPO should be rejected."""
        self.tpo_user_a.is_active = False
        self.tpo_user_a.save()

        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/college/summary/")
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_unassigned_tpo_cannot_retrieve_summary(self):
        """TPO without an active college assignment is denied."""
        self.tpo_profile_a.college = None
        self.tpo_profile_a.save()

        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/college/summary/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_student_cannot_access_tpo_summary(self):
        """Students must receive 403 Forbidden on TPO endpoints."""
        self.client.force_authenticate(user=self.student_user_a1)
        response = self.client.get("/api/v1/tpo/college/summary/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_anonymous_cannot_access_tpo_summary(self):
        """Unauthenticated requests must receive 401 Unauthorized."""
        response = self.client.get("/api/v1/tpo/college/summary/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # --------------------------------------------------------------------------
    # STUDENT ROSTER TESTS
    # --------------------------------------------------------------------------

    def test_tpo_sees_only_assigned_college_students_in_roster(self):
        """TPO A should see Student A1 and A2, but NEVER Student B1."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/college/students/")

        assert response.status_code == status.HTTP_200_OK
        records = response.json()["data"]
        student_ids = [r["student_id_number"] for r in records]

        assert "AEI2026001" in student_ids
        assert "AEI2026002" in student_ids
        assert "BUT2026001" not in student_ids

    def test_tpo_roster_search_scoped_to_college(self):
        """Searching for Bob Beta from TPO A returns empty results."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get("/api/v1/tpo/college/students/?search=Bob")

        assert response.status_code == status.HTTP_200_OK
        records = response.json()["data"]
        assert len(records) == 0

    def test_tpo_roster_filter_by_batch_and_active_status(self):
        """Filter by batch code and active status."""
        self.client.force_authenticate(user=self.tpo_user_a)

        # Batch filter
        resp_batch = self.client.get("/api/v1/tpo/college/students/?batch_code=BATCH-2026-A")
        assert resp_batch.status_code == status.HTTP_200_OK
        assert len(resp_batch.json()["data"]) == 1
        assert resp_batch.json()["data"][0]["student_id_number"] == "AEI2026001"

        # Active filter
        resp_active = self.client.get("/api/v1/tpo/college/students/?is_active=true")
        assert resp_active.status_code == status.HTTP_200_OK
        assert len(resp_active.json()["data"]) == 1
        assert resp_active.json()["data"][0]["student_id_number"] == "AEI2026001"

    # --------------------------------------------------------------------------
    # STUDENT DETAIL TESTS & IDOR PROTECTION
    # --------------------------------------------------------------------------

    def test_tpo_can_view_assigned_student_detail(self):
        """TPO A can view detailed performance of Alice Alpha."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get(f"/api/v1/tpo/college/students/{self.student_profile_a1.id}/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()["data"]
        assert data["student_id_number"] == "AEI2026001"
        assert data["full_name"] == "Alice Alpha"
        assert len(data["enrollments"]) == 1
        assert data["enrollments"][0]["course_title"] == "Python Mastery"
        assert len(data["recent_submissions"]) == 1
        assert data["recent_submissions"][0]["score_awarded"] == 100.0
        assert data["score_breakdown"]["ASSIGNMENT"] == 100.0
        assert len(data["recent_attendance"]) == 1

    def test_tpo_cannot_view_other_college_student_detail_idor_denied(self):
        """TPO A requesting Bob Beta (College B) receives 404 (IDOR prevented)."""
        self.client.force_authenticate(user=self.tpo_user_a)
        response = self.client.get(f"/api/v1/tpo/college/students/{self.student_profile_b1.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["error"]["code"] == "STUDENT_NOT_FOUND"

    def test_tpo_student_endpoints_are_read_only(self):
        """TPOs cannot mutate student records via POST, PUT, PATCH, or DELETE."""
        self.client.force_authenticate(user=self.tpo_user_a)

        # Attempt to modify student
        patch_resp = self.client.patch(
            f"/api/v1/tpo/college/students/{self.student_profile_a1.id}/",
            {"full_name": "Tampered Name"},
            format="json",
        )
        assert patch_resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        post_resp = self.client.post(
            "/api/v1/tpo/college/students/",
            {"full_name": "New Student"},
            format="json",
        )
        assert post_resp.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
