from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase

from apps.courses.models import Course
from apps.projects.models import Project, ProjectFeedback, ProjectFile, ProjectSubmission
from apps.students.models import StudentProfile

User = get_user_model()


class ProjectModelTests(TestCase):
    """Test suite for Project, Submission, File, and Feedback models."""

    def setUp(self):
        self.student_user = User.objects.create_user(
            email="proj.student@gqt.local", password="Password123!"
        )
        self.admin_user = User.objects.create_superuser(
            email="reviewer@gqt.local", password="Password123!"
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            student_id_number="GQT-STU-006",
            full_name="Project Student",
            batch_code="BATCH-2026-A",
        )
        self.course = Course.objects.create(title="Full Stack Python", slug="full-stack-python")
        self.project = Project.objects.create(
            title="E-Commerce API Capstone",
            slug="ecommerce-api-capstone",
            description="Build a RESTful e-commerce API",
            deliverables_instructions="Submit GitHub repo and live Swagger URL",
            course=self.course,
            max_score=Decimal("100.00"),
        )

    def test_project_submission_and_feedback(self):
        submission = ProjectSubmission.objects.create(
            project=self.project,
            student=self.student,
            github_repository_url="https://github.com/student/ecommerce-api",
            live_demo_url="https://ecommerce.demo.com",
            status=ProjectSubmission.SubmissionStatus.SUBMITTED,
        )

        uploaded_file = SimpleUploadedFile(
            "architecture.pdf", b"%PDF-1.4 mock content", content_type="application/pdf"
        )
        pfile = ProjectFile.objects.create(
            submission=submission,
            file=uploaded_file,
            file_name="architecture.pdf",
            file_size_bytes=len(b"%PDF-1.4 mock content"),
            mime_type="application/pdf",
        )
        self.assertEqual(pfile.submission, submission)

        feedback = ProjectFeedback.objects.create(
            submission=submission,
            reviewer=self.admin_user,
            feedback_text="Excellent architecture and test coverage.",
            rating=5,
        )
        self.assertEqual(feedback.submission, submission)
        self.assertEqual(feedback.reviewer, self.admin_user)

    def test_unique_student_project_submission(self):
        ProjectSubmission.objects.create(
            project=self.project,
            student=self.student,
        )
        with self.assertRaises(IntegrityError):
            ProjectSubmission.objects.create(
                project=self.project,
                student=self.student,
            )
