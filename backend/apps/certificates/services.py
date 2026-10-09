"""Domain services for Achievement Badges, Milestone Rules, and Certificate Generation."""

import hashlib
import logging
import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.accounts.models import AuditLog, User
from apps.certificates.models import Badge, Certificate, StudentBadge
from apps.certificates.tasks import dispatch_async_certificate_generation
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, StudentModuleProgress
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService
from apps.projects.models import ProjectSubmission
from apps.students.models import StudentProfile

logger = logging.getLogger(__name__)


class AchievementService:
    """Core domain service for evaluating milestone rules and awarding achievement badges."""

    @classmethod
    @transaction.atomic
    def evaluate_achievements(
        cls,
        student: StudentProfile,
        event_type: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[StudentBadge]:
        """Evaluate all active milestone rules against student telemetry and unlock badges."""
        # Ensure default system badges exist
        cls.ensure_default_badges()

        active_badges = Badge.objects.filter(is_active=True)
        newly_unlocked: list[StudentBadge] = []

        # Gather student progress telemetry
        completed_modules_count = StudentModuleProgress.objects.filter(
            student=student, status=StudentModuleProgress.ModuleStatus.COMPLETED
        ).count()

        total_points = float(student.total_points)
        streak_days = student.current_streak_days

        approved_projects_count = ProjectSubmission.objects.filter(
            student=student, status=ProjectSubmission.SubmissionStatus.APPROVED
        ).count()

        for badge in active_badges:
            # Check if student already earned this badge
            if StudentBadge.objects.filter(student=student, badge=badge).exists():
                continue

            should_unlock = False

            if badge.criteria_type == Badge.CriteriaType.MODULE_COMPLETION:
                if completed_modules_count >= badge.criteria_threshold:
                    should_unlock = True

            elif badge.criteria_type == Badge.CriteriaType.POINTS_MILESTONE:
                if total_points >= badge.criteria_threshold:
                    should_unlock = True

            elif badge.criteria_type == Badge.CriteriaType.STREAK_MILESTONE:
                if streak_days >= badge.criteria_threshold:
                    should_unlock = True

            elif badge.criteria_type in [
                Badge.CriteriaType.PROJECT_COMPLETION,
                Badge.CriteriaType.PROJECT_EXCELLENCE,
            ]:
                if approved_projects_count >= badge.criteria_threshold:
                    should_unlock = True

            elif badge.criteria_type == Badge.CriteriaType.COURSE_COMPLETION:
                # Check if student has completed any enrolled course 100%
                completed_enrollment = CourseEnrollment.objects.filter(
                    student=student, status=CourseEnrollment.EnrollmentStatus.COMPLETED
                ).exists()
                if completed_enrollment:
                    should_unlock = True

            if should_unlock:
                student_badge, created = StudentBadge.objects.get_or_create(
                    student=student, badge=badge
                )
                if created:
                    newly_unlocked.append(student_badge)
                    logger.info("Student %s unlocked badge %s", student.id, badge.name)

                    # Emit in-app notification
                    NotificationService.send_notification(
                        recipient=student.user,
                        title=f"🏆 Achievement Unlocked: {badge.name}!",
                        body=f"Congratulations! You earned the '{badge.name}' badge: {badge.description}",
                        notification_type=Notification.NotificationType.ACHIEVEMENT,
                        action_url="/profile",
                        idempotency_key=f"badge_{badge.id}_{student.id}",
                        metadata={"badge_id": str(badge.id), "badge_slug": badge.slug},
                    )

        return newly_unlocked

    @classmethod
    def get_student_badges_summary(
        cls, student: StudentProfile
    ) -> list[dict[str, Any]]:
        """Return list of all badges annotated with student unlock status and progress."""
        cls.ensure_default_badges()
        active_badges = Badge.objects.filter(is_active=True).order_by(
            "criteria_threshold", "name"
        )
        earned_map = {
            sb.badge_id: sb.awarded_at
            for sb in StudentBadge.objects.filter(student=student)
        }

        completed_modules_count = StudentModuleProgress.objects.filter(
            student=student, status=StudentModuleProgress.ModuleStatus.COMPLETED
        ).count()
        total_points = float(student.total_points)
        streak_days = student.current_streak_days

        results = []
        for b in active_badges:
            is_unlocked = b.id in earned_map
            awarded_at = earned_map.get(b.id)

            current_val = 0
            if b.criteria_type == Badge.CriteriaType.MODULE_COMPLETION:
                current_val = completed_modules_count
            elif b.criteria_type == Badge.CriteriaType.POINTS_MILESTONE:
                current_val = total_points
            elif b.criteria_type == Badge.CriteriaType.STREAK_MILESTONE:
                current_val = streak_days
            elif b.criteria_type in [
                Badge.CriteriaType.PROJECT_COMPLETION,
                Badge.CriteriaType.PROJECT_EXCELLENCE,
            ]:
                current_val = ProjectSubmission.objects.filter(
                    student=student, status=ProjectSubmission.SubmissionStatus.APPROVED
                ).count()

            progress_percent = (
                100.0
                if is_unlocked
                else min(100.0, (current_val / max(1, b.criteria_threshold)) * 100.0)
            )

            results.append(
                {
                    "id": str(b.id),
                    "slug": b.slug,
                    "name": b.name,
                    "description": b.description,
                    "icon_url": b.icon_url,
                    "criteria_type": b.criteria_type,
                    "criteria_threshold": b.criteria_threshold,
                    "points_reward": b.points_reward,
                    "is_unlocked": is_unlocked,
                    "awarded_at": awarded_at,
                    "progress_percentage": round(progress_percent, 1),
                }
            )
        return results

    @classmethod
    def ensure_default_badges(cls) -> None:
        """Seed default institutional badges if database is fresh."""
        defaults = [
            {
                "slug": "first-step",
                "name": "First Step",
                "description": "Completed your first sequential curriculum module.",
                "criteria_type": Badge.CriteriaType.MODULE_COMPLETION,
                "criteria_threshold": 1,
                "points_reward": 25,
            },
            {
                "slug": "logic-builder",
                "name": "Logic Builder",
                "description": "Completed 5 core programming modules.",
                "criteria_type": Badge.CriteriaType.MODULE_COMPLETION,
                "criteria_threshold": 5,
                "points_reward": 50,
            },
            {
                "slug": "oop-architect",
                "name": "OOP Architect",
                "description": "Completed all Object-Oriented Programming and Interface modules.",
                "criteria_type": Badge.CriteriaType.MODULE_COMPLETION,
                "criteria_threshold": 17,
                "points_reward": 100,
            },
            {
                "slug": "streak-starter",
                "name": "Streak Starter",
                "description": "Maintained an active 3-day daily practice streak.",
                "criteria_type": Badge.CriteriaType.STREAK_MILESTONE,
                "criteria_threshold": 3,
                "points_reward": 30,
            },
            {
                "slug": "century-scorer",
                "name": "Century Club",
                "description": "Earned 100 or more aggregate points across assignments and tasks.",
                "criteria_type": Badge.CriteriaType.POINTS_MILESTONE,
                "criteria_threshold": 100,
                "points_reward": 50,
            },
            {
                "slug": "capstone-builder",
                "name": "Capstone Builder",
                "description": "Successfully passed and approved your course capstone project.",
                "criteria_type": Badge.CriteriaType.PROJECT_COMPLETION,
                "criteria_threshold": 1,
                "points_reward": 100,
            },
        ]

        for d in defaults:
            Badge.objects.get_or_create(slug=d["slug"], defaults=d)


class CertificateService:
    """Core domain service for Certificate issuance, duplicate prevention, and verification."""

    @classmethod
    @transaction.atomic
    def issue_certificate_if_eligible(
        cls,
        student: StudentProfile,
        course: Course,
    ) -> Certificate:
        """Issue an institutional certificate upon verified course completion (idempotent)."""
        # 1. Idempotency Check: Prevent duplicate certificate generation
        existing_cert = Certificate.objects.filter(
            student=student, course=course
        ).first()
        if existing_cert:
            logger.info(
                "Certificate already exists for student %s and course %s. Returning existing.",
                student.id,
                course.id,
            )
            return existing_cert

        # 2. Check Completion Eligibility
        total_modules = Module.objects.filter(course=course, is_published=True).count()
        completed_modules = StudentModuleProgress.objects.filter(
            student=student,
            module__course=course,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
        ).count()

        if total_modules > 0 and completed_modules < total_modules:
            raise ValidationError(
                f"Course requirements not fully met ({completed_modules}/{total_modules} modules completed)."
            )

        # 3. Generate deterministic unique Certificate ID and cryptographic Hash
        year = timezone.now().year
        unique_suffix = uuid.uuid4().hex[:8].upper()
        certificate_id = f"GQT-CERT-{year}-{unique_suffix}"

        raw_hash_str = (
            f"{student.id}:{course.id}:{certificate_id}:{timezone.now().isoformat()}"
        )
        verification_hash = hashlib.sha256(raw_hash_str.encode("utf-8")).hexdigest()

        # 4. Create Certificate Record with snapshot details
        certificate = Certificate.objects.create(
            certificate_id=certificate_id,
            student=student,
            course=course,
            student_name=student.full_name,
            course_title=course.title,
            title=f"Certificate of Completion in {course.title}",
            verification_hash=verification_hash,
            metadata={
                "student_id_number": student.student_id_number,
                "batch_code": student.batch_code,
                "completed_modules": completed_modules,
                "total_modules": total_modules,
                "score_points": float(student.total_points),
            },
        )

        # 5. Dispatch non-blocking asynchronous document generation
        dispatch_async_certificate_generation(str(certificate.id))

        # 6. Emit real-time notification
        NotificationService.send_notification(
            recipient=student.user,
            title=f"🎓 Certificate Issued: {course.title}",
            body=f"Your verified certificate of completion ({certificate.certificate_id}) is ready for download.",
            notification_type=Notification.NotificationType.CERTIFICATE,
            action_url="/profile",
            idempotency_key=f"cert_issued_{certificate.id}",
            metadata={"certificate_id": certificate.certificate_id},
        )

        # Also evaluate Course Completion badge
        AchievementService.evaluate_achievements(
            student, event_type="COURSE_COMPLETION"
        )

        return certificate

    @classmethod
    def verify_certificate(cls, certificate_identifier: str) -> dict[str, Any]:
        """Public verification endpoint resolving certificate authenticity."""
        clean_id = certificate_identifier.strip()
        from django.db.models import Q

        cert = (
            Certificate.objects.select_related("student", "course")
            .filter(
                Q(certificate_id__iexact=clean_id)
                | Q(verification_hash__iexact=clean_id)
            )
            .first()
        )

        if not cert:
            raise NotFound(
                "Certificate record not found. Please verify the identifier."
            )

        if cert.is_revoked:
            return {
                "is_valid": False,
                "status": "REVOKED",
                "message": "This certificate has been officially revoked by the academic institution.",
                "certificate_id": cert.certificate_id,
            }

        return {
            "is_valid": True,
            "status": "VERIFIED",
            "certificate_id": cert.certificate_id,
            "title": cert.title,
            "student_name": cert.student_name,
            "student_id_number": cert.student.student_id_number,
            "course_title": cert.course_title,
            "issued_at": cert.issued_at,
            "verification_hash": cert.verification_hash,
            "has_pdf": bool(cert.pdf_file),
            "download_url": f"/api/v1/students/certificates/{cert.id}/download/",
        }

    @classmethod
    def list_student_certificates(cls, student: StudentProfile):
        """List verified certificates earned by the student."""
        return Certificate.objects.filter(student=student, is_revoked=False).order_by(
            "-issued_at"
        )

    @classmethod
    def list_admin_certificates(
        cls,
        search: str | None = None,
        course_id: uuid.UUID | None = None,
        is_revoked: bool | None = None,
    ):
        """Admin listing with filtering."""
        qs = Certificate.objects.select_related("student", "course").order_by(
            "-issued_at"
        )
        if search:
            from django.db.models import Q

            qs = qs.filter(
                Q(certificate_id__icontains=search)
                | Q(student_name__icontains=search)
                | Q(course_title__icontains=search)
                | Q(student__student_id_number__icontains=search)
            )
        if course_id:
            qs = qs.filter(course_id=course_id)
        if is_revoked is not None:
            qs = qs.filter(is_revoked=is_revoked)
        return qs

    @classmethod
    @transaction.atomic
    def revoke_certificate(
        cls,
        certificate_id: uuid.UUID,
        admin_user: User,
        reason: str = "",
        ip_address: str | None = None,
    ) -> Certificate:
        """Revoke a certificate."""
        cert = get_object_or_404(Certificate, id=certificate_id)
        cert.is_revoked = True
        cert.save(update_fields=["is_revoked", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="CERTIFICATE_REVOKED",
            target_model="Certificate",
            target_id=str(cert.id),
            ip_address=ip_address,
            payload={"reason": reason, "certificate_id": cert.certificate_id},
        )
        return cert
