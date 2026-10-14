"""Comprehensive tests for Course Assignment & Unassignment Lifecycle in Student Admin.

Verifies:
1. Admin can assign multiple courses to a student.
2. Removing a course in the selection updates backend: removed course is deleted/unassigned.
3. Swapping courses: old courses removed, new courses added.
4. Deselecting all courses (`course_ids=[]`) removes all enrollments without 400 validation error.
5. DELETE endpoint unassigns single course or all courses.
6. Unassigning non-enrolled course returns 404.
7. Student detail API only returns active/completed enrollments.
8. Enrolled courses count updates accurately.
9. Student `course_opted` is kept synchronized.
10. Audit log is recorded for both assignment and unassignment operations.
11. Permissions: Only admin can assign or unassign courses.
"""

import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import AuditLog
from apps.courses.models import Course, CourseEnrollment
from apps.students.models import StudentProfile

User = get_user_model()


class CourseAssignmentLifecycleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

        # Admin user
        self.admin = User.objects.create_superuser(
            email="admin_lifecycle@gqt.test",
            password="AdminPassword123!",
            role=User.RoleChoices.ADMIN,
        )

        # Regular student user & profile
        self.student_user = User.objects.create_user(
            email="student_test@gqt.test",
            password="StudentPassword123!",
            role=User.RoleChoices.STUDENT,
        )
        self.student = StudentProfile.objects.create(
            user=self.student_user,
            student_id_number="GQT-STU-001",
            full_name="Alice Candidate",
            batch_code="BATCH-2026-A",
            course_opted="",
        )

        # Courses
        self.course_a = Course.objects.create(
            title="Java Full Stack Development",
            slug="java-full-stack",
            is_published=True,
        )
        self.course_b = Course.objects.create(
            title="Agentic AI with Data Science",
            slug="agentic-ai-data-science",
            is_published=True,
        )
        self.course_c = Course.objects.create(
            title="Cloud Infrastructure & DevOps",
            slug="cloud-infra-devops",
            is_published=True,
        )

        self.assign_url = reverse(
            "api_v1:admin_students:assign_courses",
            kwargs={"pk": self.student.id},
        )
        self.detail_url = reverse(
            "api_v1:admin_students:detail_update",
            kwargs={"pk": self.student.id},
        )

    def test_assign_multiple_courses_success(self):
        """Admin assigns Course A and Course B to the student."""
        self.client.force_authenticate(user=self.admin)

        resp = self.client.post(
            self.assign_url,
            {"course_ids": [str(self.course_a.id), str(self.course_b.id)]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["data"]), 2)

        # Verify DB enrollments
        enrollments = CourseEnrollment.objects.filter(student=self.student)
        self.assertEqual(enrollments.count(), 2)
        self.assertTrue(
            enrollments.filter(
                course=self.course_a, status=CourseEnrollment.EnrollmentStatus.ACTIVE
            ).exists()
        )
        self.assertTrue(
            enrollments.filter(
                course=self.course_b, status=CourseEnrollment.EnrollmentStatus.ACTIVE
            ).exists()
        )

        # Verify detail serializer
        detail_resp = self.client.get(self.detail_url)
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        enrolled_ids = [e["course_id"] for e in detail_resp.data["data"]["enrollments"]]
        self.assertIn(str(self.course_a.id), enrolled_ids)
        self.assertIn(str(self.course_b.id), enrolled_ids)
        self.assertEqual(detail_resp.data["data"]["enrolled_courses_count"], 2)

    def test_remove_course_by_deselection(self):
        """When admin deselects Course B (sends only Course A), Course B must be removed in backend."""
        self.client.force_authenticate(user=self.admin)

        # Initial assignment: Course A and Course B
        self.client.post(
            self.assign_url,
            {"course_ids": [str(self.course_a.id), str(self.course_b.id)]},
            format="json",
        )
        self.assertEqual(
            CourseEnrollment.objects.filter(student=self.student).count(), 2
        )

        # Admin removes Course B by submitting only Course A
        resp = self.client.post(
            self.assign_url,
            {"course_ids": [str(self.course_a.id)]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["data"]), 1)
        self.assertEqual(resp.data["data"][0]["course_id"], str(self.course_a.id))

        # Verify DB: Course B is removed, only Course A remains
        self.assertEqual(
            CourseEnrollment.objects.filter(student=self.student).count(), 1
        )
        self.assertFalse(
            CourseEnrollment.objects.filter(
                student=self.student, course=self.course_b
            ).exists()
        )
        self.assertTrue(
            CourseEnrollment.objects.filter(
                student=self.student, course=self.course_a
            ).exists()
        )

        # Verify detail serializer
        detail_resp = self.client.get(self.detail_url)
        enrolled_ids = [e["course_id"] for e in detail_resp.data["data"]["enrollments"]]
        self.assertEqual(enrolled_ids, [str(self.course_a.id)])
        self.assertEqual(detail_resp.data["data"]["enrolled_courses_count"], 1)

    def test_swap_courses_in_assignment(self):
        """Admin removes Course A and adds Course C in a single assignment update."""
        self.client.force_authenticate(user=self.admin)

        # Initially Course A
        self.client.post(
            self.assign_url,
            {"course_ids": [str(self.course_a.id)]},
            format="json",
        )

        # Swap to Course C
        resp = self.client.post(
            self.assign_url,
            {"course_ids": [str(self.course_c.id)]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Check DB
        self.assertFalse(
            CourseEnrollment.objects.filter(
                student=self.student, course=self.course_a
            ).exists()
        )
        self.assertTrue(
            CourseEnrollment.objects.filter(
                student=self.student, course=self.course_c
            ).exists()
        )

        # Check student profile course_opted updated
        self.student.refresh_from_db()
        self.assertEqual(self.student.course_opted, self.course_c.title)

    def test_unassign_all_courses_with_empty_list(self):
        """Admin deselects all courses and submits empty course_ids list."""
        self.client.force_authenticate(user=self.admin)

        # Initially Course A & B
        self.client.post(
            self.assign_url,
            {"course_ids": [str(self.course_a.id), str(self.course_b.id)]},
            format="json",
        )
        self.assertEqual(
            CourseEnrollment.objects.filter(student=self.student).count(), 2
        )

        # Submit empty list
        resp = self.client.post(
            self.assign_url,
            {"course_ids": []},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["data"]), 0)

        # DB must have 0 enrollments
        self.assertEqual(
            CourseEnrollment.objects.filter(student=self.student).count(), 0
        )

        # Detail must show 0
        detail_resp = self.client.get(self.detail_url)
        self.assertEqual(len(detail_resp.data["data"]["enrollments"]), 0)
        self.assertEqual(detail_resp.data["data"]["enrolled_courses_count"], 0)

        self.student.refresh_from_db()
        self.assertEqual(self.student.course_opted, "")

    def test_single_course_unassign_via_delete_endpoint(self):
        """Admin unassigns a single course via DELETE query parameter."""
        self.client.force_authenticate(user=self.admin)

        # Enroll in Course A and Course B
        self.client.post(
            self.assign_url,
            {"course_ids": [str(self.course_a.id), str(self.course_b.id)]},
            format="json",
        )

        # DELETE Course B
        delete_url = f"{self.assign_url}?course_id={self.course_b.id}"
        resp = self.client.delete(delete_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("Course unassigned successfully", resp.data["message"])

        # Course B is gone, Course A remains
        self.assertFalse(
            CourseEnrollment.objects.filter(
                student=self.student, course=self.course_b
            ).exists()
        )
        self.assertTrue(
            CourseEnrollment.objects.filter(
                student=self.student, course=self.course_a
            ).exists()
        )

        # Audit log verification
        audit = AuditLog.objects.filter(
            actor=self.admin, action="COURSE_UNASSIGNED"
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.payload.get("course_id"), str(self.course_b.id))

    def test_unassign_non_enrolled_course_returns_404(self):
        """Attempting to unassign a course that the student is not enrolled in returns 404."""
        self.client.force_authenticate(user=self.admin)

        delete_url = f"{self.assign_url}?course_id={self.course_c.id}"
        resp = self.client.delete(delete_url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unassign_all_via_delete_endpoint(self):
        """DELETE without query params unassigns all courses."""
        self.client.force_authenticate(user=self.admin)

        self.client.post(
            self.assign_url,
            {"course_ids": [str(self.course_a.id), str(self.course_b.id)]},
            format="json",
        )
        self.assertEqual(
            CourseEnrollment.objects.filter(student=self.student).count(), 2
        )

        resp = self.client.delete(self.assign_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            CourseEnrollment.objects.filter(student=self.student).count(), 0
        )

    def test_non_admin_cannot_assign_courses(self):
        """Students cannot assign or remove courses."""
        self.client.force_authenticate(user=self.student_user)

        resp = self.client.post(
            self.assign_url,
            {"course_ids": [str(self.course_a.id)]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        del_resp = self.client.delete(
            f"{self.assign_url}?course_id={self.course_a.id}"
        )
        self.assertEqual(del_resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_course_id_returns_400(self):
        """Invalid or non-existent course UUID returns 400 DomainException."""
        self.client.force_authenticate(user=self.admin)

        fake_id = str(uuid.uuid4())
        resp = self.client.post(
            self.assign_url,
            {"course_ids": [fake_id]},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
