from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.courses.models import Course, CourseEnrollment
from apps.students.models import StudentProfile

User = get_user_model()


class CourseModelTests(TestCase):
    """Test suite for Course and CourseEnrollment models."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="course.student@gqt.local", password="Password123!"
        )
        self.student = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-001",
            full_name="Test Student",
            batch_code="BATCH-2026-A",
        )
        self.course = Course.objects.create(
            title="Core Python Foundations",
            slug="core-python-foundations",
            description="Complete Python curriculum",
        )

    def test_course_soft_delete(self):
        self.course.delete()
        self.course.refresh_from_db()
        self.assertTrue(self.course.is_deleted)
        # Course still exists in database for academic record retention
        self.assertEqual(Course.objects.filter(id=self.course.id).count(), 1)

    def test_course_enrollment_relationship(self):
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.course, self.course)
        self.assertIn(enrollment, self.student.enrollments.all())
        self.assertIn(enrollment, self.course.enrollments.all())

    def test_unique_student_course_enrollment_constraint(self):
        CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
        )
        with self.assertRaises(IntegrityError):
            CourseEnrollment.objects.create(
                student=self.student,
                course=self.course,
            )
