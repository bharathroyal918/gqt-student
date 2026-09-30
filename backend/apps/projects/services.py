"""Domain services for Capstone Project Submissions, Security Validation, and Review Workflows."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import AuditLog, User
from apps.common.exceptions import DomainException
from apps.courses.models import Course, CourseEnrollment
from apps.notifications.models import Notification
from apps.projects.models import Project, ProjectFeedback, ProjectFile, ProjectSubmission
from apps.projects.security import FileSecurityValidator, GitHubUrlValidator
from apps.scoring.services import ScoringService
from apps.students.models import StudentProfile


class ProjectAdminService:
    """Administrative service managing capstone projects, submission grading, and file access."""

    @classmethod
    def get_project(cls, project_id: str) -> Project:
        return get_object_or_404(
            Project.objects.select_related("course").prefetch_related("submissions"),
            id=project_id,
        )

    @classmethod
    def get_submission_detail(cls, submission_id: str) -> ProjectSubmission:
        return get_object_or_404(
            ProjectSubmission.objects.select_related(
                "project", "student", "student__user", "reviewed_by"
            ).prefetch_related("files", "feedbacks__reviewer"),
            id=submission_id,
        )

    @classmethod
    def get_submissions_queryset(
        cls,
        status: Optional[str] = None,
        project_id: Optional[str] = None,
        batch_code: Optional[str] = None,
        search: Optional[str] = None,
    ):
        qs = (
            ProjectSubmission.objects.select_related("project", "student", "student__user", "reviewed_by")
            .prefetch_related("files", "feedbacks__reviewer")
            .order_by("-submitted_at")
        )

        if status:
            qs = qs.filter(status=status.upper())

        if project_id:
            qs = qs.filter(project_id=project_id)

        if batch_code:
            qs = qs.filter(student__batch_code=batch_code.strip())

        if search:
            qs = qs.filter(
                Q(student__full_name__icontains=search)
                | Q(student__student_id_number__icontains=search)
                | Q(student__user__email__icontains=search)
                | Q(project__title__icontains=search)
                | Q(github_repository_url__icontains=search)
            )

        return qs

    @classmethod
    @transaction.atomic
    def create_project(
        cls,
        admin_user: User,
        title: str,
        description: str,
        deliverables_instructions: str,
        course_id: Optional[str] = None,
        max_score: Decimal = Decimal("10.00"),
        due_date: Optional[timezone.datetime] = None,
        is_active: bool = True,
        slug: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Project:
        p_slug = slug.strip().lower() if slug else slugify(title)
        if Project.objects.filter(slug=p_slug).exists():
            raise DomainException("A project with this slug already exists.")

        course = None
        if course_id:
            course = get_object_or_404(Course, id=course_id, is_deleted=False)

        project = Project.objects.create(
            title=title.strip(),
            slug=p_slug,
            description=description.strip(),
            deliverables_instructions=deliverables_instructions.strip(),
            course=course,
            max_score=max_score,
            due_date=due_date,
            is_active=is_active,
        )

        AuditLog.objects.create(
            actor=admin_user,
            action="PROJECT_CREATED",
            target_model="Project",
            target_id=str(project.id),
            ip_address=ip_address,
            payload={"title": project.title, "max_score": str(max_score)},
        )
        return project

    @classmethod
    @transaction.atomic
    def update_project(
        cls,
        project_id: str,
        admin_user: User,
        title: Optional[str] = None,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        deliverables_instructions: Optional[str] = None,
        course_id: Optional[str] = None,
        max_score: Optional[Decimal] = None,
        due_date: Optional[timezone.datetime] = None,
        is_active: Optional[bool] = None,
        ip_address: Optional[str] = None,
    ) -> Project:
        project = cls.get_project(project_id)
        update_fields = ["updated_at"]

        if title is not None:
            project.title = title.strip()
            update_fields.append("title")

        if slug is not None:
            p_slug = slug.strip().lower()
            if Project.objects.filter(slug=p_slug).exclude(id=project.id).exists():
                raise DomainException("A project with this slug already exists.")
            project.slug = p_slug
            update_fields.append("slug")

        if description is not None:
            project.description = description.strip()
            update_fields.append("description")

        if deliverables_instructions is not None:
            project.deliverables_instructions = deliverables_instructions.strip()
            update_fields.append("deliverables_instructions")

        if course_id is not None:
            if course_id == "":
                project.course = None
            else:
                project.course = get_object_or_404(Course, id=course_id, is_deleted=False)
            update_fields.append("course")

        if max_score is not None:
            project.max_score = max_score
            update_fields.append("max_score")

        if due_date is not None:
            project.due_date = due_date
            update_fields.append("due_date")

        if is_active is not None:
            project.is_active = is_active
            update_fields.append("is_active")

        project.save(update_fields=update_fields)

        AuditLog.objects.create(
            actor=admin_user,
            action="PROJECT_UPDATED",
            target_model="Project",
            target_id=str(project.id),
            ip_address=ip_address,
            payload={"updated_fields": update_fields},
        )
        return project

    @classmethod
    @transaction.atomic
    def review_submission(
        cls,
        submission_id: str,
        admin_user: User,
        status: str,
        score: Optional[Decimal] = None,
        feedback_text: str = "",
        suggested_changes: str = "",
        rating: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> ProjectSubmission:
        submission = cls.get_submission_detail(submission_id)

        if status not in ProjectSubmission.SubmissionStatus.values:
            raise DomainException(
                f"Invalid status. Allowed choices: {ProjectSubmission.SubmissionStatus.values}"
            )

        if score is not None:
            if score < Decimal("0.00") or score > submission.project.max_score:
                raise DomainException(
                    f"Score must be between 0.00 and {submission.project.max_score}."
                )

        submission.status = status
        submission.score = score
        submission.reviewed_at = timezone.now()
        submission.reviewed_by = admin_user
        submission.save(
            update_fields=["status", "score", "reviewed_at", "reviewed_by", "updated_at"]
        )

        if feedback_text or suggested_changes:
            ProjectFeedback.objects.create(
                submission=submission,
                reviewer=admin_user,
                feedback_text=feedback_text.strip(),
                suggested_changes=suggested_changes.strip(),
                rating=rating,
            )

        # Marks MUST flow through the central scoring service
        if score is not None and score > Decimal("0.00"):
            ScoringService.evaluate_project_submission(
                student=submission.student,
                project_id=str(submission.project.id),
                project_title=submission.project.title,
                score=score,
                max_score=submission.project.max_score,
                awarded_by=admin_user,
                feedback_notes=feedback_text,
            )

        AuditLog.objects.create(
            actor=admin_user,
            action="PROJECT_SUBMISSION_REVIEWED",
            target_model="ProjectSubmission",
            target_id=str(submission.id),
            ip_address=ip_address,
            payload={"status": status, "score": str(score) if score is not None else None},
        )
        return submission

    @classmethod
    def get_file_for_download(cls, file_id: str, requesting_user: User) -> ProjectFile:
        """Secure download helper verifying access authorization without leaking server internal paths."""
        project_file = get_object_or_404(
            ProjectFile.objects.select_related("submission__student__user"), id=file_id
        )

        is_admin = (
            getattr(requesting_user, "role", None) == User.RoleChoices.ADMIN
            or requesting_user.is_staff
            or requesting_user.is_superuser
        )
        is_owner = project_file.submission.student.user_id == requesting_user.id

        if not (is_admin or is_owner):
            raise DomainException("You do not have permission to access this file.")

        return project_file


class StudentProjectService:
    """Service providing student project browsing, secure deliverables upload, and feedback views."""

    @classmethod
    def get_assigned_projects(cls, student: StudentProfile) -> List[Dict[str, Any]]:
        enrolled_course_ids = CourseEnrollment.objects.filter(
            student=student, status=CourseEnrollment.EnrollmentStatus.ACTIVE
        ).values_list("course_id", flat=True)

        projects = (
            Project.objects.filter(is_active=True)
            .filter(Q(course_id__in=enrolled_course_ids) | Q(course__isnull=True))
            .select_related("course")
            .prefetch_related(
                Prefetch(
                    "submissions",
                    queryset=ProjectSubmission.objects.filter(student=student).prefetch_related(
                        "files", "feedbacks__reviewer"
                    ),
                    to_attr="student_submissions",
                )
            )
            .order_by("-created_at")
        )

        results = []
        for p in projects:
            sub_list = getattr(p, "student_submissions", [])
            submission = sub_list[0] if sub_list else None

            results.append(cls._serialize_student_project_summary(p, submission))

        return results

    @classmethod
    def get_project_detail(cls, student: StudentProfile, project_id: str) -> Dict[str, Any]:
        enrolled_course_ids = CourseEnrollment.objects.filter(
            student=student, status=CourseEnrollment.EnrollmentStatus.ACTIVE
        ).values_list("course_id", flat=True)

        project = (
            Project.objects.filter(is_active=True, id=project_id)
            .filter(Q(course_id__in=enrolled_course_ids) | Q(course__isnull=True))
            .select_related("course")
            .prefetch_related(
                Prefetch(
                    "submissions",
                    queryset=ProjectSubmission.objects.filter(student=student).prefetch_related(
                        "files", "feedbacks__reviewer"
                    ),
                    to_attr="student_submissions",
                )
            )
            .first()
        )

        if not project:
            raise DomainException("Project not found or not assigned to your enrolled curriculum.")

        sub_list = getattr(project, "student_submissions", [])
        submission = sub_list[0] if sub_list else None

        return cls._serialize_student_project_detail(project, submission)

    @classmethod
    @transaction.atomic
    def submit_project(
        cls,
        student: StudentProfile,
        project_id: str,
        github_repository_url: str,
        live_demo_url: str = "",
        notes: str = "",
        uploaded_files: Optional[List[UploadedFile]] = None,
        ip_address: Optional[str] = None,
    ) -> ProjectSubmission:
        enrolled_course_ids = CourseEnrollment.objects.filter(
            student=student, status=CourseEnrollment.EnrollmentStatus.ACTIVE
        ).values_list("course_id", flat=True)

        project = (
            Project.objects.filter(is_active=True, id=project_id)
            .filter(Q(course_id__in=enrolled_course_ids) | Q(course__isnull=True))
            .first()
        )
        if not project:
            raise DomainException("Project not found or not assigned to your enrolled curriculum.")

        # 1. Normalize and validate GitHub URL
        normalized_github_url = GitHubUrlValidator.normalize_github_url(github_repository_url)
        if not normalized_github_url and not uploaded_files:
            raise DomainException("Either a valid GitHub repository URL or project files must be provided.")

        # 2. Validate all uploaded files before committing
        validated_file_meta = []
        if uploaded_files:
            for file_obj in uploaded_files:
                clean_name, size_bytes, mime_type = FileSecurityValidator.validate_file(file_obj)
                validated_file_meta.append((file_obj, clean_name, size_bytes, mime_type))

        # 3. Create or update submission record
        submission, created = ProjectSubmission.objects.get_or_create(
            project=project,
            student=student,
            defaults={
                "github_repository_url": normalized_github_url,
                "live_demo_url": live_demo_url.strip(),
                "notes": notes.strip(),
                "status": ProjectSubmission.SubmissionStatus.SUBMITTED,
            },
        )

        if not created:
            submission.github_repository_url = normalized_github_url
            submission.live_demo_url = live_demo_url.strip()
            submission.notes = notes.strip()
            submission.status = ProjectSubmission.SubmissionStatus.SUBMITTED
            submission.save(
                update_fields=["github_repository_url", "live_demo_url", "notes", "status", "updated_at"]
            )

        # 4. Save validated files
        for file_obj, clean_name, size_bytes, mime_type in validated_file_meta:
            ProjectFile.objects.create(
                submission=submission,
                file=file_obj,
                file_name=clean_name,
                file_size_bytes=size_bytes,
                mime_type=mime_type,
            )

        # 5. Audit Log & Notifications
        AuditLog.objects.create(
            actor=student.user,
            action="PROJECT_SUBMITTED",
            target_model="ProjectSubmission",
            target_id=str(submission.id),
            ip_address=ip_address,
            payload={
                "project_title": project.title,
                "github_url": normalized_github_url,
                "files_count": len(validated_file_meta),
            },
        )

        Notification.objects.create(
            recipient=student.user,
            title=f"Project Submitted: {project.title}",
            body=f"Your submission for '{project.title}' has been received and is under review.",
            notification_type=Notification.NotificationType.SYSTEM_NOTICE,
            action_url=f"/projects/{project.id}",
        )

        return submission

    @classmethod
    def _serialize_student_project_summary(
        cls, project: Project, submission: Optional[ProjectSubmission]
    ) -> Dict[str, Any]:
        return {
            "id": str(project.id),
            "title": project.title,
            "slug": project.slug,
            "description": project.description,
            "course_id": str(project.course.id) if project.course else None,
            "course_title": project.course.title if project.course else None,
            "max_score": float(project.max_score),
            "due_date": project.due_date.isoformat() if project.due_date else None,
            "has_submitted": submission is not None,
            "submission_id": str(submission.id) if submission else None,
            "status": submission.status if submission else "PENDING",
            "score": float(submission.score) if submission and submission.score is not None else None,
            "submitted_at": submission.submitted_at.isoformat() if submission else None,
        }

    @classmethod
    def _serialize_student_project_detail(
        cls, project: Project, submission: Optional[ProjectSubmission]
    ) -> Dict[str, Any]:
        data = cls._serialize_student_project_summary(project, submission)
        data["deliverables_instructions"] = project.deliverables_instructions

        if submission:
            data["submission_detail"] = {
                "id": str(submission.id),
                "github_repository_url": submission.github_repository_url,
                "live_demo_url": submission.live_demo_url,
                "notes": submission.notes,
                "status": submission.status,
                "score": float(submission.score) if submission.score is not None else None,
                "submitted_at": submission.submitted_at.isoformat(),
                "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
                "files": [
                    {
                        "id": str(f.id),
                        "file_name": f.file_name,
                        "file_size_bytes": f.file_size_bytes,
                        "mime_type": f.mime_type,
                        "download_url": f"/api/v1/projects/files/{f.id}/download/",
                        "uploaded_at": f.uploaded_at.isoformat(),
                    }
                    for f in submission.files.all()
                ],
                "feedbacks": [
                    {
                        "id": str(fb.id),
                        "reviewer_name": fb.reviewer.get_full_name() or fb.reviewer.email,
                        "feedback_text": fb.feedback_text,
                        "suggested_changes": fb.suggested_changes,
                        "rating": fb.rating,
                        "created_at": fb.created_at.isoformat(),
                    }
                    for fb in submission.feedbacks.all()
                ],
            }
        else:
            data["submission_detail"] = None

        return data
