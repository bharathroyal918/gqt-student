"""Database & PostgreSQL Architecture Integration Tests.

Verifies:
1. UUID primary key generation and integrity.
2. Decimal score precision arithmetic across domain scoring models.
3. Transaction atomicity and rollback safety (transaction.atomic).
4. Relational foreign key cascades and integrity constraints.
5. UniqueConstraints and CheckConstraints on academic/scoring entities.
6. Database health check metrics and latency reporting.
"""

from decimal import Decimal
import uuid
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.courses.models import Course, CourseEnrollment
from apps.scoring.models import ScoreRecord
from apps.students.models import StudentProfile


class DatabaseArchitectureIntegrationTests(TestCase):
    """Verifies relational integrity, UUID handling, and decimal score precision."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="db.test@gqt.local",
            password="StrongPassword123!",
            role="STUDENT",
        )
        self.student = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-DB-001",
            full_name="Database Test Student",
            batch_code="BATCH-2026-TEST",
            college_name="National Institute of Technology",
            total_points=Decimal("0.00"),
        )
        self.course = Course.objects.create(
            title="Database Integration Test Course",
            slug="db-integration-course",
            description="Testing PostgreSQL relational mappings.",
        )

    def test_uuid_primary_key_generation(self):
        """All entities must generate valid UUIDv4 primary keys."""
        self.assertIsInstance(self.user.id, uuid.UUID)
        self.assertIsInstance(self.student.id, uuid.UUID)
        self.assertIsInstance(self.course.id, uuid.UUID)

    def test_decimal_score_precision_arithmetic(self):
        """Point tallies and score records must preserve exact decimal precision without float rounding errors."""
        initial_points = Decimal("200.00")
        deduction = Decimal("33.33")
        bonus = Decimal("15.55")

        self.student.total_points = initial_points - deduction + bonus
        self.student.save(update_fields=["total_points"])

        refreshed = StudentProfile.objects.get(id=self.student.id)
        self.assertEqual(refreshed.total_points, Decimal("182.22"))
        self.assertIsInstance(refreshed.total_points, Decimal)

    def test_unique_constraint_enforcement(self):
        """Duplicate academic IDs or unique constraint violations must raise IntegrityError."""
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                duplicate_user = User.objects.create_user(
                    email="duplicate@gqt.local",
                    password="Password123!",
                    role="STUDENT",
                )
                StudentProfile.objects.create(
                    user=duplicate_user,
                    student_id_number="GQT-DB-001",  # Duplicate ID
                    full_name="Duplicate Student",
                    batch_code="BATCH-2026-TEST",
                )

    def test_course_enrollment_unique_constraint(self):
        """A student cannot have multiple concurrent enrollment records for the exact same course."""
        CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            status="ACTIVE",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CourseEnrollment.objects.create(
                    student=self.student,
                    course=self.course,
                    status="ACTIVE",
                )

    def test_transaction_atomic_rollback(self):
        """Database transactions must roll back cleanly on exception without partial commits."""
        initial_count = ScoreRecord.objects.count()

        try:
            with transaction.atomic():
                ScoreRecord.objects.create(
                    student=self.student,
                    source_type="ASSIGNMENT",
                    source_id=uuid.uuid4(),
                    points=Decimal("50.00"),
                    policy_applied="FULL",
                )
                raise ValueError("Simulated failure during multi-table mutation")
        except ValueError:
            pass

        final_count = ScoreRecord.objects.count()
        self.assertEqual(initial_count, final_count, "Rolled back transaction must leave no orphan records")

    def test_foreign_key_cascade_behavior(self):
        """Deleting a User cascades to StudentProfile and related CourseEnrollment records."""
        CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            status="ACTIVE",
        )
        student_id = self.student.id

        self.user.delete()

        self.assertFalse(StudentProfile.objects.filter(id=student_id).exists())
        self.assertFalse(CourseEnrollment.objects.filter(student_id=student_id).exists())


class DatabaseHealthEndpointTests(APITestCase):
    """Verifies the database health probe returns clean metrics without credential leakage."""

    def test_database_health_probe_success(self):
        response = self.client.get("/api/v1/health/database/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["status"], "healthy")
        self.assertIn("latency_ms", data["data"])
        self.assertIn("engine", data["data"])

        # Security check: Ensure no connection strings or passwords leaked
        raw_body = str(response.content)
        self.assertNotIn("postgres:", raw_body)
        self.assertNotIn("password", raw_body.lower())
        self.assertNotIn("supabase.co", raw_body)
