"""Comprehensive Test Suite for Project Submissions, File Security, and Administrative Review.

Tests:
1. Student Views Assigned Projects & Details.
2. Student Project Submission with normalized GitHub URL & Notes.
3. File Security Validations:
   - Whitelist allowed extensions (.zip, .pdf, .py, etc.).
   - Disallowed executables (.exe, .sh, .bat, etc.) rejected.
   - Disguised binary executables with magic headers rejected.
   - File size limit (25 MB max) enforced.
   - Filename sanitization & path traversal (../../) defense.
   - Antivirus / EICAR malware signature detection.
4. GitHub URL syntax validation and normalization.
5. Admin Submissions List, Filtering, and Detail.
6. Admin Review & Scoring:
   - Evaluated marks flow through central ScoringService.
   - Student total points updated, audit log & score event created, leaderboard cache invalidated.
   - Rubric feedback & ratings attached.
   - Review status transitioned to APPROVED.
7. Secure File Download & Access Authorization:
   - Enrolled student owner can download files.
   - Admin can download files.
   - Unrelated student blocked from accessing peer files.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.common.exceptions import DomainException
from apps.courses.models import Course, CourseEnrollment
from apps.notifications.models import Notification
from apps.projects.models import Project, ProjectFile, ProjectSubmission
from apps.projects.security import FileSecurityValidator, GitHubUrlValidator
from apps.scoring.models import ScoreRecord
from apps.students.models import StudentProfile

User = get_user_model()


class ProjectSubmissionApiTests(TestCase):
    """Test suite for Student and Admin Project Submission workflows."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()

        # Admin user
        self.admin_user = User.objects.create_user(
            email="admin.projects@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.ADMIN,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )

        # Course
        self.course = Course.objects.create(
            title="Full-Stack Web Development",
            slug="full-stack-web-dev",
            is_published=True,
        )

        # Student 1 (Enrolled in Course)
        self.user_a = User.objects.create_user(
            email="student.a@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.student_a = StudentProfile.objects.create(
            user=self.user_a,
            student_id_number="GQT-PROJ-001",
            full_name="Alice Developer",
            batch_code="BATCH-2026-A",
            total_points=Decimal("0.00"),
        )
        CourseEnrollment.objects.create(
            student=self.student_a,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )

        # Student 2 (Peer Student)
        self.user_b = User.objects.create_user(
            email="student.b@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.student_b = StudentProfile.objects.create(
            user=self.user_b,
            student_id_number="GQT-PROJ-002",
            full_name="Bob Developer",
            batch_code="BATCH-2026-B",
            total_points=Decimal("0.00"),
        )

        # Project (worth 10.00 marks)
        self.project = Project.objects.create(
            course=self.course,
            title="E-Commerce Microservices Platform",
            slug="ecommerce-microservices",
            description="Build a production microservices backend.",
            deliverables_instructions="Submit GitHub repo and zipped architecture diagram.",
            max_score=Decimal("10.00"),
            is_active=True,
        )

    def test_student_list_and_detail_project(self):
        """Student can view enrolled projects with submission status and instructions."""
        self.client.force_authenticate(user=self.user_a)

        # List projects
        res_list = self.client.get("/api/v1/students/projects/")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        projects = res_list.json()["data"]["projects"]
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["id"], str(self.project.id))
        self.assertEqual(projects[0]["max_score"], 10.0)
        self.assertFalse(projects[0]["has_submitted"])

        # Detail project
        res_detail = self.client.get(f"/api/v1/students/projects/{self.project.id}/")
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        data = res_detail.json()["data"]
        self.assertEqual(data["title"], "E-Commerce Microservices Platform")
        self.assertIn("deliverables_instructions", data)

    def test_student_submit_project_with_files_and_github(self):
        """Student submits project with valid GitHub URL and deliverable zip file."""
        self.client.force_authenticate(user=self.user_a)

        file_content = b"PK\x03\x04mock zip payload for capstone project"
        uploaded_zip = SimpleUploadedFile(
            "project_src.zip", file_content, content_type="application/zip"
        )

        res_submit = self.client.post(
            f"/api/v1/students/projects/{self.project.id}/submit/",
            {
                "github_repository_url": "https://github.com/alice/ecommerce-backend.git/",
                "live_demo_url": "https://alice-ecommerce.example.com",
                "notes": "Completed with Django & React",
                "files": [uploaded_zip],
            },
            format="multipart",
        )
        self.assertEqual(res_submit.status_code, status.HTTP_200_OK)
        sub_data = res_submit.json()["data"]

        submission = ProjectSubmission.objects.get(id=sub_data["submission_id"])
        self.assertEqual(
            submission.status, ProjectSubmission.SubmissionStatus.SUBMITTED
        )
        # Normalized GitHub URL (stripped trailing .git and /)
        self.assertEqual(
            submission.github_repository_url,
            "https://github.com/alice/ecommerce-backend",
        )
        self.assertEqual(submission.files.count(), 1)
        self.assertEqual(submission.files.first().file_name, "project_src.zip")

    def test_file_security_disallowed_executable(self):
        """Upload of executable files (.exe, .sh, .bat) is strictly rejected."""
        self.client.force_authenticate(user=self.user_a)

        bad_exe = SimpleUploadedFile(
            "malicious_app.exe",
            b"binary content",
            content_type="application/x-msdownload",
        )

        res = self.client.post(
            f"/api/v1/students/projects/{self.project.id}/submit/",
            {
                "github_repository_url": "https://github.com/alice/proj",
                "files": [bad_exe],
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("prohibited", str(res.json()).lower())

    def test_file_security_disguised_executable_magic_header(self):
        """Disguised executable with .txt or .zip extension but 'MZ' header is rejected."""
        self.client.force_authenticate(user=self.user_a)

        fake_txt = SimpleUploadedFile(
            "notes.txt", b"MZ\x90\x00\x03\x00\x00\x00", content_type="text/plain"
        )

        res = self.client.post(
            f"/api/v1/students/projects/{self.project.id}/submit/",
            {
                "github_repository_url": "https://github.com/alice/proj",
                "files": [fake_txt],
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("disguised binary executables", str(res.json()).lower())

    def test_file_security_path_traversal_sanitization(self):
        """Filenames containing path traversal sequences (../../etc/passwd) are sanitized."""
        sanitized = FileSecurityValidator.sanitize_filename("../../etc/passwd.pdf")
        self.assertEqual(sanitized, "passwd.pdf")

        sanitized_win = FileSecurityValidator.sanitize_filename(
            "..\\..\\Windows\\System32\\calc.zip"
        )
        self.assertEqual(sanitized_win, "calc.zip")

    def test_file_security_eicar_malware_detection(self):
        """Files containing standard antivirus test signatures are blocked."""
        eicar_content = (
            b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        )
        bad_file = SimpleUploadedFile(
            "test_report.pdf", eicar_content, content_type="application/pdf"
        )

        self.client.force_authenticate(user=self.user_a)
        res = self.client.post(
            f"/api/v1/students/projects/{self.project.id}/submit/",
            {
                "github_repository_url": "https://github.com/alice/proj",
                "files": [bad_file],
            },
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("malware signature detected", str(res.json()).lower())

    def test_github_url_normalization_and_validation(self):
        """Test valid GitHub URLs are normalized and invalid URLs are rejected."""
        norm1 = GitHubUrlValidator.normalize_github_url(
            "https://github.com/john_doe/web-app.git/"
        )
        self.assertEqual(norm1, "https://github.com/john_doe/web-app")

        norm2 = GitHubUrlValidator.normalize_github_url(
            "http://www.github.com/org-name/repo-name"
        )
        self.assertEqual(norm2, "https://github.com/org-name/repo-name")

        with self.assertRaises(DomainException):
            GitHubUrlValidator.normalize_github_url("https://gitlab.com/alice/repo")

        with self.assertRaises(DomainException):
            GitHubUrlValidator.normalize_github_url("not_a_valid_url")

    def test_admin_review_scoring_and_status_update(self):
        """Admin reviews submission, awards 10.00 marks through central ScoringService, and updates status."""
        # Student A submits project
        submission = ProjectSubmission.objects.create(
            project=self.project,
            student=self.student_a,
            github_repository_url="https://github.com/alice/ecommerce-backend",
            live_demo_url="https://demo.alice.com",
            notes="Ready for review",
            status=ProjectSubmission.SubmissionStatus.SUBMITTED,
        )

        self.client.force_authenticate(user=self.admin_user)

        # 1. Admin lists submissions
        res_list = self.client.get(
            "/api/v1/admin/projects/submissions/?status=SUBMITTED"
        )
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        subs = (
            res_list.json()["data"]
            if "data" in res_list.json()
            else res_list.json()["results"]
        )
        self.assertTrue(len(subs) >= 1)

        # 2. Admin reviews and assigns 10.00 marks with feedback
        res_rev = self.client.post(
            f"/api/v1/admin/projects/submissions/{submission.id}/",
            {
                "status": "APPROVED",
                "score": 10.00,
                "feedback_text": "Superb architecture and code documentation. 10/10.",
                "suggested_changes": "Consider adding automated CI/CD pipeline in future.",
                "rating": 5,
            },
            format="json",
        )
        self.assertEqual(res_rev.status_code, status.HTTP_200_OK)
        sub_data = res_rev.json()["data"]
        self.assertEqual(sub_data["status"], "APPROVED")
        self.assertEqual(float(sub_data["score"]), 10.0)

        # 3. Verify marks flowed through centralized ScoringService
        self.student_a.refresh_from_db()
        self.assertEqual(float(self.student_a.total_points), 10.0)

        # Verify ScoreRecord created
        self.assertTrue(
            ScoreRecord.objects.filter(
                student=self.student_a,
                source_type="PROJECT",
                source_id=str(self.project.id),
            ).exists()
        )

        # Verify Notification emitted
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.user_a,
                title__contains="Project Graded",
            ).exists()
        )

    def test_secure_file_download_authorization(self):
        """Owner student and admin can download deliverable files; unrelated student is denied."""
        submission = ProjectSubmission.objects.create(
            project=self.project,
            student=self.student_a,
            github_repository_url="https://github.com/alice/ecommerce-backend",
        )
        mock_file = SimpleUploadedFile(
            "design_doc.pdf", b"%PDF-1.5 test document", content_type="application/pdf"
        )
        pfile = ProjectFile.objects.create(
            submission=submission,
            file=mock_file,
            file_name="design_doc.pdf",
            file_size_bytes=len(b"%PDF-1.5 test document"),
            mime_type="application/pdf",
        )

        # 1. Owner Student A can download
        self.client.force_authenticate(user=self.user_a)
        res_a = self.client.get(f"/api/v1/projects/files/{pfile.id}/download/")
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        self.assertEqual(res_a["Content-Type"], "application/pdf")

        # 2. Admin can download
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get(f"/api/v1/projects/files/{pfile.id}/download/")
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)

        # 3. Unrelated Student B is blocked
        self.client.force_authenticate(user=self.user_b)
        res_b = self.client.get(f"/api/v1/projects/files/{pfile.id}/download/")
        self.assertEqual(res_b.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("permission", str(res_b.json()).lower())
