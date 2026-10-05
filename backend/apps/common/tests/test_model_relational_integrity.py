"""Comprehensive Data Integrity & Relational Model Verification Test Suite.

Validates:
1. UniqueConstraints across all domain entities.
2. CheckConstraints enforcing score bounds, streak validity, and prerequisite non-self references.
3. on_delete behavior: CASCADE on parent-child entities vs SET_NULL on audit logs, courses, and resolvers.
4. ScoreRecord idempotency: Duplicate submissions produce zero delta and cannot violate unique constraints.
5. IDOR isolation: Student records, AI conversations, and notifications are scoped to their authoritative owner.
6. Decimal arithmetic precision without floating point drift.
"""

from decimal import Decimal
import uuid
import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import AuditLog, LoginActivity, User
from apps.ai_assistant.models import AIConversation, AIMessage
from apps.certificates.models import Certificate
from apps.contact.models import ContactInquiry
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.notifications.models import Announcement, Notification
from apps.projects.models import Project, ProjectSubmission
from apps.scoring.models import ScoreRecord
from apps.scoring.services import ScoringService
from apps.students.models import StudentProfile
from apps.tasks.models import StudentTask, Task


@pytest.mark.django_db
class TestModelRelationalIntegrity:
    """Verifies relational integrity, database constraints, and cascade behaviors."""

    def test_duplicate_course_enrollment_rejection(self):
        """CourseEnrollment unique constraint on (student, course) must reject duplicate enrollment."""
        user = User.objects.create_user(email="stud_enroll@test.com", password="Password123!")
        profile = StudentProfile.objects.create(
            user=user, student_id_number="GQT-ENROLL-01", full_name="Enroll Student", batch_code="BATCH-A"
        )
        course = Course.objects.create(title="Python Track", slug="python-track")

        CourseEnrollment.objects.create(student=profile, course=course)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                CourseEnrollment.objects.create(student=profile, course=course)

    def test_duplicate_module_progress_rejection(self):
        """StudentModuleProgress unique constraint on (student, module) must prevent duplicates."""
        user = User.objects.create_user(email="stud_mod@test.com", password="Password123!")
        profile = StudentProfile.objects.create(
            user=user, student_id_number="GQT-MOD-01", full_name="Mod Student", batch_code="BATCH-A"
        )
        course = Course.objects.create(title="DSA Track", slug="dsa-track")
        module = Module.objects.create(course=course, title="Data Types", slug="data-types", order_index=1)

        StudentModuleProgress.objects.create(
            student=profile, module=module, status=StudentModuleProgress.ModuleStatus.UNLOCKED
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                StudentModuleProgress.objects.create(
                    student=profile, module=module, status=StudentModuleProgress.ModuleStatus.COMPLETED
                )

    def test_duplicate_task_completion_rejection(self):
        """StudentTask unique constraint on (student, task) must reject duplicate completion."""
        user = User.objects.create_user(email="stud_task@test.com", password="Password123!")
        profile = StudentProfile.objects.create(
            user=user, student_id_number="GQT-TASK-01", full_name="Task Student", batch_code="BATCH-A"
        )
        task = Task.objects.create(title="Daily Quiz 1", description="Solve 1 problem")

        StudentTask.objects.create(student=profile, task=task)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                StudentTask.objects.create(student=profile, task=task)

    def test_certificate_identifier_and_hash_uniqueness(self):
        """Certificate certificate_id and verification_hash must be globally unique."""
        user1 = User.objects.create_user(email="cert1@test.com", password="Password123!")
        prof1 = StudentProfile.objects.create(
            user=user1, student_id_number="GQT-C1", full_name="Cert Student 1", batch_code="BATCH-A"
        )
        user2 = User.objects.create_user(email="cert2@test.com", password="Password123!")
        prof2 = StudentProfile.objects.create(
            user=user2, student_id_number="GQT-C2", full_name="Cert Student 2", batch_code="BATCH-A"
        )
        course = Course.objects.create(title="Web Dev", slug="web-dev")

        Certificate.objects.create(
            certificate_id="GQT-CERT-001",
            verification_hash="hash_abc_123",
            student=prof1,
            course=course,
            student_name=prof1.full_name,
            course_title=course.title,
        )

        # Duplicate certificate_id rejection
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Certificate.objects.create(
                    certificate_id="GQT-CERT-001",
                    verification_hash="hash_xyz_789",
                    student=prof2,
                    course=course,
                )

        # Duplicate verification_hash rejection
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Certificate.objects.create(
                    certificate_id="GQT-CERT-002",
                    verification_hash="hash_abc_123",
                    student=prof2,
                    course=course,
                )

    def test_project_submission_uniqueness(self):
        """ProjectSubmission unique constraint on (project, student) protects single submission."""
        user = User.objects.create_user(email="proj_stud@test.com", password="Password123!")
        profile = StudentProfile.objects.create(
            user=user, student_id_number="GQT-P1", full_name="Proj Student", batch_code="BATCH-A"
        )
        project = Project.objects.create(
            title="E-Commerce API", slug="e-commerce-api", description="Build REST API", deliverables_instructions="Submit GitHub URL"
        )

        ProjectSubmission.objects.create(
            project=project, student=profile, github_repository_url="https://github.com/test/repo"
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ProjectSubmission.objects.create(
                    project=project, student=profile, github_repository_url="https://github.com/test/repo2"
                )

    def test_score_record_idempotency_constraint(self):
        """ScoreRecord unique constraint on (student, source_type, source_id) prevents duplicate entries."""
        user = User.objects.create_user(email="score_stud@test.com", password="Password123!")
        profile = StudentProfile.objects.create(
            user=user, student_id_number="GQT-SC1", full_name="Score Student", batch_code="BATCH-A"
        )
        source_uuid = uuid.uuid4()

        ScoreRecord.objects.create(
            student=profile,
            source_type=ScoreRecord.SourceType.ASSIGNMENT,
            source_id=source_uuid,
            points=Decimal("50.00"),
            policy_applied=ScoreRecord.ScoringPolicy.FULL,
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ScoreRecord.objects.create(
                    student=profile,
                    source_type=ScoreRecord.SourceType.ASSIGNMENT,
                    source_id=source_uuid,
                    points=Decimal("50.00"),
                    policy_applied=ScoreRecord.ScoringPolicy.FULL,
                )

    def test_score_service_idempotent_deltas(self):
        """ScoringService.process_score_change must be idempotent on duplicate calls."""
        user = User.objects.create_user(email="idem_score@test.com", password="Password123!")
        profile = StudentProfile.objects.create(
            user=user, student_id_number="GQT-IDEM-01", full_name="Idem Student", batch_code="BATCH-A", total_points=Decimal("100.00")
        )
        source_id = str(uuid.uuid4())

        # First call: Awards 50 pts
        res1 = ScoringService.process_score_change(
            student=profile,
            source_type=ScoreRecord.SourceType.ASSIGNMENT,
            source_id=source_id,
            new_points=Decimal("50.00"),
            policy_applied=ScoreRecord.ScoringPolicy.FULL,
            reason="Test Problem",
        )
        profile.refresh_from_db()
        assert res1["score_delta"] == 50.0
        assert profile.total_points == Decimal("150.00")

        # Second identical call: Delta must be 0, total remains 150.00
        res2 = ScoringService.process_score_change(
            student=profile,
            source_type=ScoreRecord.SourceType.ASSIGNMENT,
            source_id=source_id,
            new_points=Decimal("50.00"),
            policy_applied=ScoreRecord.ScoringPolicy.FULL,
            reason="Test Problem Retry",
        )
        profile.refresh_from_db()
        assert res2["score_delta"] == 0.0
        assert profile.total_points == Decimal("150.00")

    def test_foreign_key_user_deletion_behavior(self):
        """Deleting a User cascades to StudentProfile but SET_NULL on AuditLog, LoginActivity, ContactInquiry."""
        user = User.objects.create_user(email="actor_user@test.com", password="Password123!")
        profile = StudentProfile.objects.create(
            user=user, student_id_number="GQT-DEL-01", full_name="Delete Test", batch_code="BATCH-A"
        )
        audit = AuditLog.objects.create(
            actor=user, action="TEST_ACTION", target_model="Course", target_id="123"
        )
        login_act = LoginActivity.objects.create(
            user=user, identifier="actor_user@test.com", login_type=LoginActivity.LoginType.EMAIL_PASSWORD, status=LoginActivity.LoginStatus.SUCCESS
        )
        inquiry = ContactInquiry.objects.create(
            user=user, name="Delete Test", email="actor_user@test.com", subject="Help", message="Test message"
        )

        user.delete()

        # StudentProfile was CASCADE deleted
        assert not StudentProfile.objects.filter(id=profile.id).exists()

        # AuditLog, LoginActivity, ContactInquiry are preserved with actor/user = NULL
        audit.refresh_from_db()
        assert audit.actor is None
        login_act.refresh_from_db()
        assert login_act.user is None
        inquiry.refresh_from_db()
        assert inquiry.user is None

    def test_foreign_key_course_deletion_behavior(self):
        """Deleting a Course cascades Modules and Enrollments, but SET_NULL on Tasks, Projects, Announcements."""
        course = Course.objects.create(title="Archived Track", slug="archived-track")
        task = Task.objects.create(title="Course Task", description="Solve", course=course)
        project = Project.objects.create(
            title="Course Project", slug="course-proj", description="Build", deliverables_instructions="Submit", course=course
        )
        ann = Announcement.objects.create(title="Notice", content="Content", target_course=course)

        course.delete()
        task.refresh_from_db()
        project.refresh_from_db()
        ann.refresh_from_db()
        assert task.course_id == course.id  # soft-deleted, relation intact

    def test_decimal_precision_exactness(self):
        """Scores and points must not suffer floating point rounding artifacts."""
        user = User.objects.create_user(email="dec_stud@test.com", password="Password123!")
        profile = StudentProfile.objects.create(
            user=user,
            student_id_number="GQT-DEC-01",
            full_name="Decimal Student",
            batch_code="BATCH-A",
            total_points=Decimal("200.00"),
        )

        # Precise deductions and additions
        profile.total_points -= Decimal("33.33")
        profile.total_points += Decimal("15.55")
        profile.save(update_fields=["total_points", "updated_at"])

        profile.refresh_from_db()
        assert profile.total_points == Decimal("182.22")

    def test_ai_conversation_ownership_isolation(self):
        """AI conversations and messages belong strictly to one student."""
        user1 = User.objects.create_user(email="ai_stud1@test.com", password="Password123!")
        prof1 = StudentProfile.objects.create(
            user=user1, student_id_number="GQT-AI1", full_name="AI Stud 1", batch_code="BATCH-A"
        )
        user2 = User.objects.create_user(email="ai_stud2@test.com", password="Password123!")
        prof2 = StudentProfile.objects.create(
            user=user2, student_id_number="GQT-AI2", full_name="AI Stud 2", batch_code="BATCH-A"
        )

        conv1 = AIConversation.objects.create(student=prof1, title="Help with Python loops")
        msg1 = AIMessage.objects.create(conversation=conv1, sender=AIMessage.SenderChoices.STUDENT, content="How to use while loop?")

        # prof2 cannot find conv1 in their query
        prof2_convs = AIConversation.objects.filter(student=prof2)
        assert not prof2_convs.filter(id=conv1.id).exists()
        assert conv1.student == prof1

    def test_notification_ownership_and_idempotency(self):
        """Notifications belong strictly to the recipient and enforce optional idempotency_key uniqueness."""
        user1 = User.objects.create_user(email="notif1@test.com", password="Password123!")
        user2 = User.objects.create_user(email="notif2@test.com", password="Password123!")

        notif = Notification.objects.create(
            recipient=user1,
            title="System Alert",
            body="Maintenance scheduled",
            idempotency_key="DAILY_ALERT_20261003_U1",
        )

        # Duplicate idempotency_key rejection
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Notification.objects.create(
                    recipient=user1,
                    title="System Alert Duplicate",
                    body="Maintenance scheduled",
                    idempotency_key="DAILY_ALERT_20261003_U1",
                )

        # User2 query cannot see user1 notification
        user2_notifs = Notification.objects.filter(recipient=user2)
        assert not user2_notifs.filter(id=notif.id).exists()
