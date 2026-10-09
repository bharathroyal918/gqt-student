"""Domain services for administrative course management."""

from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from apps.accounts.models import AuditLog, User
from apps.common.exceptions import DomainException
from apps.courses.models import (
    Course,
    CourseEnrollment,
    RecordedClass,
    StudentRecordedClassProgress,
)


class CourseAdminService:
    """Service handling institutional course lifecycles, archival, and publishing."""

    @classmethod
    def get_course(cls, course_id: str) -> Course:
        return get_object_or_404(Course, id=course_id)

    @classmethod
    @transaction.atomic
    def create_course(
        cls,
        admin_user: User,
        title: str,
        description: str = "",
        thumbnail_url: str = "",
        slug: str | None = None,
        is_published: bool = False,
        order: int = 0,
        ip_address: str | None = None,
    ) -> Course:
        course_slug = slug.strip().lower() if slug else slugify(title)
        if Course.objects.filter(slug=course_slug).exists():
            raise DomainException("A course with this slug already exists.")

        course = Course.objects.create(
            title=title.strip(),
            slug=course_slug,
            description=description.strip(),
            thumbnail_url=thumbnail_url.strip(),
            is_published=is_published,
            order=order,
            created_by=admin_user,
        )

        AuditLog.objects.create(
            actor=admin_user,
            action="COURSE_CREATED",
            target_model="Course",
            target_id=str(course.id),
            ip_address=ip_address,
            payload={
                "title": course.title,
                "slug": course.slug,
                "is_published": course.is_published,
            },
        )
        return course

    @classmethod
    @transaction.atomic
    def update_course(
        cls,
        course_id: str,
        admin_user: User,
        title: str | None = None,
        slug: str | None = None,
        description: str | None = None,
        thumbnail_url: str | None = None,
        is_published: bool | None = None,
        order: int | None = None,
        ip_address: str | None = None,
    ) -> Course:
        course = cls.get_course(course_id)
        update_fields = ["updated_at"]

        if title is not None:
            course.title = title.strip()
            update_fields.append("title")

        if slug is not None:
            course_slug = slug.strip().lower()
            if Course.objects.filter(slug=course_slug).exclude(id=course.id).exists():
                raise DomainException("A course with this slug already exists.")
            course.slug = course_slug
            update_fields.append("slug")

        if description is not None:
            course.description = description.strip()
            update_fields.append("description")

        if thumbnail_url is not None:
            course.thumbnail_url = thumbnail_url.strip()
            update_fields.append("thumbnail_url")

        if is_published is not None:
            course.is_published = is_published
            update_fields.append("is_published")

        if order is not None:
            course.order = order
            update_fields.append("order")

        course.save(update_fields=update_fields)

        AuditLog.objects.create(
            actor=admin_user,
            action="COURSE_UPDATED",
            target_model="Course",
            target_id=str(course.id),
            ip_address=ip_address,
            payload={"updated_fields": update_fields},
        )
        return course

    @classmethod
    @transaction.atomic
    def archive_course(
        cls, course_id: str, admin_user: User, ip_address: str | None = None
    ) -> Course:
        """Safely archives/soft-deletes a course without destroying academic enrollments."""
        course = cls.get_course(course_id)
        course.is_deleted = True
        course.is_published = False
        course.save(update_fields=["is_deleted", "is_published", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="COURSE_ARCHIVED",
            target_model="Course",
            target_id=str(course.id),
            ip_address=ip_address,
        )
        return course

    @classmethod
    @transaction.atomic
    def set_publish_status(
        cls,
        course_id: str,
        is_published: bool,
        admin_user: User,
        ip_address: str | None = None,
    ) -> Course:
        course = cls.get_course(course_id)
        if course.is_deleted:
            raise DomainException("Cannot publish an archived course.")

        course.is_published = is_published
        course.save(update_fields=["is_published", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="COURSE_PUBLISH_STATUS_CHANGED",
            target_model="Course",
            target_id=str(course.id),
            ip_address=ip_address,
            payload={"is_published": is_published},
        )
        return course


class CourseEnrollmentService:
    """Service handling student course enrollment allocations and permissions."""

    @classmethod
    @transaction.atomic
    def allocate_enrollment(
        cls,
        admin_user: User,
        course_id: str,
        student_id: str,
        status: str = CourseEnrollment.EnrollmentStatus.ACTIVE,
        ip_address: str | None = None,
    ) -> CourseEnrollment:
        from apps.students.models import StudentProfile

        course = get_object_or_404(Course, id=course_id)
        student = get_object_or_404(StudentProfile, id=student_id)

        enrollment, created = CourseEnrollment.objects.get_or_update_or_create = (
            CourseEnrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={"status": status},
            )
        )

        if not created and enrollment.status != status:
            enrollment.status = status
            enrollment.save(update_fields=["status", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="COURSE_ENROLLMENT_ALLOCATED",
            target_model="CourseEnrollment",
            target_id=str(enrollment.id),
            ip_address=ip_address,
            payload={
                "course_id": str(course.id),
                "course_title": course.title,
                "student_id": str(student.id),
                "student_name": student.full_name,
                "status": enrollment.status,
            },
        )
        return enrollment

    @classmethod
    @transaction.atomic
    def revoke_enrollment(
        cls,
        admin_user: User,
        course_id: str,
        student_id: str,
        ip_address: str | None = None,
    ) -> CourseEnrollment:

        enrollment = get_object_or_404(
            CourseEnrollment,
            course_id=course_id,
            student_id=student_id,
        )
        enrollment.status = CourseEnrollment.EnrollmentStatus.REVOKED
        enrollment.save(update_fields=["status", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="COURSE_ENROLLMENT_REVOKED",
            target_model="CourseEnrollment",
            target_id=str(enrollment.id),
            ip_address=ip_address,
            payload={
                "course_id": str(enrollment.course_id),
                "student_id": str(enrollment.student_id),
            },
        )
        return enrollment

    @classmethod
    def get_course_enrollments(cls, course_id: str):
        return (
            CourseEnrollment.objects.filter(course_id=course_id)
            .select_related("student", "student__user")
            .order_by("-enrolled_at")
        )


class RecordedClassAdminService:
    """Domain services for administrative recorded video lecture management."""

    @classmethod
    def get_recorded_class(cls, class_id: str) -> "RecordedClass":
        from apps.courses.models import RecordedClass

        return get_object_or_404(RecordedClass, id=class_id)

    @classmethod
    @transaction.atomic
    def create_recorded_class(
        cls,
        admin_user: User,
        course_id: str,
        title: str,
        slug: str | None = None,
        description: str = "",
        order_index: int | None = None,
        video_source_type: str = "YOUTUBE",
        youtube_url: str = "",
        video_file=None,
        video_url: str = "",
        duration_seconds: int = 0,
        duration_formatted: str = "",
        thumbnail_url: str = "",
        is_preview: bool = False,
        is_published: bool = True,
        notes: str = "",
        resources_url: str = "",
        module_id: str | None = None,
        ip_address: str | None = None,
    ) -> "RecordedClass":
        from apps.courses.models import Course, RecordedClass

        course = get_object_or_404(Course, id=course_id)

        # Auto-calculate order_index if not provided
        if order_index is None or order_index <= 0:
            max_order = (
                RecordedClass.objects.filter(course=course).aggregate(
                    models.Max("order_index")
                )["order_index__max"]
                or 0
            )
            order_index = max_order + 1

        class_slug = (
            slug.strip().lower()
            if slug
            else slugify(f"{course.slug}-{order_index}-{title[:40]}")
        )
        # Ensure slug uniqueness for course
        base_slug = class_slug
        counter = 1
        while RecordedClass.objects.filter(course=course, slug=class_slug).exists():
            class_slug = f"{base_slug}-{counter}"
            counter += 1

        recorded_class = RecordedClass.objects.create(
            course=course,
            module_id=module_id if module_id else None,
            title=title.strip(),
            slug=class_slug,
            description=description.strip(),
            order_index=order_index,
            video_source_type=video_source_type,
            youtube_url=youtube_url.strip(),
            video_file=video_file,
            video_url=video_url.strip(),
            duration_seconds=duration_seconds,
            duration_formatted=duration_formatted.strip() if duration_formatted else "",
            thumbnail_url=thumbnail_url.strip(),
            is_preview=is_preview,
            is_published=is_published,
            notes=notes.strip(),
            resources_url=resources_url.strip(),
            created_by=admin_user,
        )

        AuditLog.objects.create(
            actor=admin_user,
            action="RECORDED_CLASS_CREATED",
            target_model="RecordedClass",
            target_id=str(recorded_class.id),
            ip_address=ip_address,
            payload={
                "course_id": str(course.id),
                "title": recorded_class.title,
                "order_index": recorded_class.order_index,
                "video_source_type": recorded_class.video_source_type,
            },
        )
        return recorded_class

    @classmethod
    @transaction.atomic
    def update_recorded_class(
        cls,
        class_id: str,
        admin_user: User,
        title: str | None = None,
        slug: str | None = None,
        description: str | None = None,
        order_index: int | None = None,
        video_source_type: str | None = None,
        youtube_url: str | None = None,
        video_file=None,
        video_url: str | None = None,
        duration_seconds: int | None = None,
        duration_formatted: str | None = None,
        thumbnail_url: str | None = None,
        is_preview: bool | None = None,
        is_published: bool | None = None,
        notes: str | None = None,
        resources_url: str | None = None,
        module_id: str | None = None,
        ip_address: str | None = None,
    ) -> "RecordedClass":
        from apps.courses.models import RecordedClass

        recorded_class = cls.get_recorded_class(class_id)
        update_fields = ["updated_at"]

        if title is not None:
            recorded_class.title = title.strip()
            update_fields.append("title")

        if slug is not None:
            class_slug = slug.strip().lower()
            if (
                RecordedClass.objects.filter(
                    course=recorded_class.course, slug=class_slug
                )
                .exclude(id=recorded_class.id)
                .exists()
            ):
                raise DomainException(
                    "A recorded class with this slug already exists in this course."
                )
            recorded_class.slug = class_slug
            update_fields.append("slug")

        if description is not None:
            recorded_class.description = description.strip()
            update_fields.append("description")

        if order_index is not None:
            recorded_class.order_index = order_index
            update_fields.append("order_index")

        if video_source_type is not None:
            recorded_class.video_source_type = video_source_type
            update_fields.append("video_source_type")

        if youtube_url is not None:
            recorded_class.youtube_url = youtube_url.strip()
            update_fields.append("youtube_url")
            yt_id = recorded_class.extract_youtube_id(recorded_class.youtube_url)
            recorded_class.youtube_video_id = yt_id
            update_fields.append("youtube_video_id")
            if yt_id and not thumbnail_url and not recorded_class.thumbnail_url:
                recorded_class.thumbnail_url = (
                    f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"
                )
                update_fields.append("thumbnail_url")

        if video_file is not None:
            recorded_class.video_file = video_file
            update_fields.append("video_file")

        if video_url is not None:
            recorded_class.video_url = video_url.strip()
            update_fields.append("video_url")

        if duration_seconds is not None:
            recorded_class.duration_seconds = duration_seconds
            update_fields.append("duration_seconds")

        if duration_formatted is not None:
            recorded_class.duration_formatted = duration_formatted.strip()
            update_fields.append("duration_formatted")

        if thumbnail_url is not None:
            recorded_class.thumbnail_url = thumbnail_url.strip()
            update_fields.append("thumbnail_url")

        if is_preview is not None:
            recorded_class.is_preview = is_preview
            update_fields.append("is_preview")

        if is_published is not None:
            recorded_class.is_published = is_published
            update_fields.append("is_published")

        if notes is not None:
            recorded_class.notes = notes.strip()
            update_fields.append("notes")

        if resources_url is not None:
            recorded_class.resources_url = resources_url.strip()
            update_fields.append("resources_url")

        if module_id is not None:
            recorded_class.module_id = module_id if module_id else None
            update_fields.append("module")

        recorded_class.save(update_fields=update_fields)

        AuditLog.objects.create(
            actor=admin_user,
            action="RECORDED_CLASS_UPDATED",
            target_model="RecordedClass",
            target_id=str(recorded_class.id),
            ip_address=ip_address,
            payload={"updated_fields": update_fields},
        )
        return recorded_class

    @classmethod
    @transaction.atomic
    def delete_recorded_class(
        cls, class_id: str, admin_user: User, ip_address: str | None = None
    ):

        recorded_class = cls.get_recorded_class(class_id)
        class_id_str = str(recorded_class.id)
        title = recorded_class.title
        course_id = str(recorded_class.course_id)
        recorded_class.delete()

        AuditLog.objects.create(
            actor=admin_user,
            action="RECORDED_CLASS_DELETED",
            target_model="RecordedClass",
            target_id=class_id_str,
            ip_address=ip_address,
            payload={"title": title, "course_id": course_id},
        )

    @classmethod
    @transaction.atomic
    def reorder_recorded_classes(
        cls,
        course_id: str,
        order_items: list[dict],
        admin_user: User,
        ip_address: str | None = None,
    ):
        from apps.courses.models import RecordedClass

        for item in order_items:
            class_id = item.get("id")
            order_idx = item.get("order_index")
            if class_id and order_idx is not None:
                RecordedClass.objects.filter(id=class_id, course_id=course_id).update(
                    order_index=order_idx
                )

        AuditLog.objects.create(
            actor=admin_user,
            action="RECORDED_CLASSES_REORDERED",
            target_model="Course",
            target_id=str(course_id),
            ip_address=ip_address,
            payload={"items_count": len(order_items)},
        )


class RecordedClassStudentService:
    """Strong domain logic for student recorded class viewing, free preview limits, and progress tracking."""

    @staticmethod
    def is_student_enrolled_in_course(student_profile, course) -> bool:
        """Returns True if the student possesses an ACTIVE enrollment in the course."""
        if not student_profile:
            return False
        from apps.courses.models import CourseEnrollment

        return CourseEnrollment.objects.filter(
            student=student_profile,
            course=course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        ).exists()

    @classmethod
    def get_all_courses_catalog(cls, student_profile):
        """Lists all published curriculum courses with recorded class stats and enrollment indicator."""
        from apps.courses.models import (
            Course,
            CourseEnrollment,
            RecordedClass,
        )

        courses = Course.objects.filter(is_published=True, is_deleted=False).order_by(
            "order", "title"
        )

        # Get set of actively enrolled course IDs for this student
        enrolled_course_ids = set()
        if student_profile:
            enrolled_course_ids = set(
                CourseEnrollment.objects.filter(
                    student=student_profile,
                    status=CourseEnrollment.EnrollmentStatus.ACTIVE,
                ).values_list("course_id", flat=True)
            )

        result = []
        for course in courses:
            total_videos = RecordedClass.objects.filter(
                course=course, is_published=True
            ).count()
            is_enrolled = course.id in enrolled_course_ids

            completed_videos = 0
            if student_profile:
                completed_videos = StudentRecordedClassProgress.objects.filter(
                    student=student_profile,
                    recorded_class__course=course,
                    is_completed=True,
                ).count()

            progress_percent = (
                int((completed_videos / total_videos) * 100) if total_videos > 0 else 0
            )

            result.append(
                {
                    "id": str(course.id),
                    "title": course.title,
                    "slug": course.slug,
                    "description": course.description,
                    "thumbnail_url": course.thumbnail_url,
                    "is_enrolled": is_enrolled,
                    "enrollment_status": "ACTIVE" if is_enrolled else "NOT_ENROLLED",
                    "total_videos": total_videos,
                    "preview_videos_count": min(5, total_videos),
                    "completed_videos": completed_videos,
                    "progress_percentage": progress_percent,
                    "has_full_access": is_enrolled,
                    "free_preview_unrestricted": True,
                }
            )

        return result

    @classmethod
    def get_course_recorded_classes_playlist(cls, student_profile, course_id: str):
        """Returns the full ordered playlist of recorded classes for a course, applying strong lock boundaries."""
        from apps.courses.models import (
            Course,
            RecordedClass,
        )

        course = get_object_or_404(
            Course, id=course_id, is_published=True, is_deleted=False
        )
        is_enrolled = cls.is_student_enrolled_in_course(student_profile, course)

        classes_qs = (
            RecordedClass.objects.filter(course=course, is_published=True)
            .select_related("module")
            .order_by("order_index", "created_at")
        )

        # Get completed video IDs for this student
        completed_video_map = {}
        if student_profile:
            progress_records = StudentRecordedClassProgress.objects.filter(
                student=student_profile,
                recorded_class__course=course,
            )
            for prog in progress_records:
                completed_video_map[prog.recorded_class_id] = {
                    "is_completed": prog.is_completed,
                    "last_position_seconds": prog.last_position_seconds,
                }

        playlist = []
        for v in classes_qs:
            # First 5 videos are always free preview for all registered students.
            # Video 6 and beyond require active course enrollment/approval.
            is_unlocked = is_enrolled or v.is_free_preview

            prog_info = completed_video_map.get(
                v.id, {"is_completed": False, "last_position_seconds": 0}
            )

            video_data = {
                "id": str(v.id),
                "course_id": str(course.id),
                "course_title": course.title,
                "module_id": str(v.module_id) if v.module_id else None,
                "module_title": v.module.title if v.module else None,
                "title": v.title,
                "slug": v.slug,
                "order_index": v.order_index,
                "duration_seconds": v.duration_seconds,
                "duration_formatted": v.duration_formatted,
                "thumbnail_url": v.thumbnail_url,
                "is_preview": v.is_free_preview,
                "is_locked": not is_unlocked,
                "is_completed": prog_info["is_completed"],
                "last_position_seconds": prog_info["last_position_seconds"],
                "lock_reason": None if is_unlocked else "ENROLLMENT_REQUIRED",
            }

            if is_unlocked:
                # Provide full video metadata & streaming source info
                video_data["description"] = v.description
                video_data["video_source_type"] = v.video_source_type
                video_data["youtube_video_id"] = v.youtube_video_id
                video_data["youtube_url"] = v.youtube_url
                video_data["video_url"] = v.video_url
                video_data["video_file_url"] = v.video_file.url if v.video_file else ""
                video_data["notes"] = v.notes
                video_data["resources_url"] = v.resources_url
            else:
                # Omit video streaming keys completely so unauthorized users cannot tamper
                video_data["description"] = (
                    (v.description[:140] + "...")
                    if v.description
                    else "Course enrollment required to view full lesson."
                )
                video_data["video_source_type"] = "LOCKED"
                video_data["youtube_video_id"] = ""
                video_data["youtube_url"] = ""
                video_data["video_url"] = ""
                video_data["video_file_url"] = ""
                video_data["notes"] = ""
                video_data["resources_url"] = ""

            playlist.append(video_data)

        total_videos = len(playlist)
        completed_count = sum(1 for item in playlist if item["is_completed"])

        return {
            "course": {
                "id": str(course.id),
                "title": course.title,
                "slug": course.slug,
                "description": course.description,
                "thumbnail_url": course.thumbnail_url,
                "is_enrolled": is_enrolled,
                "enrollment_status": "ACTIVE" if is_enrolled else "NOT_ENROLLED",
                "total_videos": total_videos,
                "preview_videos_limit": 5,
                "completed_videos": completed_count,
                "progress_percentage": int((completed_count / total_videos) * 100)
                if total_videos > 0
                else 0,
            },
            "videos": playlist,
        }

    @classmethod
    def get_recorded_class_stream(cls, student_profile, course_id: str, video_id: str):
        """Returns the streaming details for a single video, strictly rejecting unauthorized access to locked videos."""
        from apps.courses.models import (
            Course,
            RecordedClass,
        )

        course = get_object_or_404(
            Course, id=course_id, is_published=True, is_deleted=False
        )
        video = get_object_or_404(
            RecordedClass, id=video_id, course=course, is_published=True
        )

        is_enrolled = cls.is_student_enrolled_in_course(student_profile, course)
        is_unlocked = is_enrolled or video.is_free_preview

        if not is_unlocked:
            raise DomainException(
                "Access Denied: This recorded class is locked. First 5 videos are free; full curriculum access requires course enrollment approval by administrator."
            )

        prog, _ = StudentRecordedClassProgress.objects.get_or_create(
            student=student_profile,
            recorded_class=video,
        )

        return {
            "id": str(video.id),
            "course_id": str(course.id),
            "course_title": course.title,
            "title": video.title,
            "slug": video.slug,
            "description": video.description,
            "order_index": video.order_index,
            "video_source_type": video.video_source_type,
            "youtube_url": video.youtube_url,
            "youtube_video_id": video.youtube_video_id,
            "video_url": video.video_url,
            "video_file_url": video.video_file.url if video.video_file else "",
            "duration_seconds": video.duration_seconds,
            "duration_formatted": video.duration_formatted,
            "thumbnail_url": video.thumbnail_url,
            "is_preview": video.is_free_preview,
            "is_locked": False,
            "notes": video.notes,
            "resources_url": video.resources_url,
            "is_completed": prog.is_completed,
            "last_position_seconds": prog.last_position_seconds,
        }

    @classmethod
    @transaction.atomic
    def record_video_progress(
        cls,
        student_profile,
        video_id: str,
        last_position_seconds: int = 0,
        is_completed: bool | None = None,
    ):
        """Records student watch position and marks video as completed."""
        from django.utils import timezone

        from apps.courses.models import RecordedClass

        video = get_object_or_404(RecordedClass, id=video_id, is_published=True)

        prog, _ = StudentRecordedClassProgress.objects.get_or_create(
            student=student_profile,
            recorded_class=video,
        )

        if last_position_seconds > 0:
            prog.last_position_seconds = last_position_seconds

        if is_completed is not None:
            prog.is_completed = is_completed
            if is_completed and not prog.completed_at:
                prog.completed_at = timezone.now()

        prog.save()
        return {
            "video_id": str(video.id),
            "last_position_seconds": prog.last_position_seconds,
            "is_completed": prog.is_completed,
            "completed_at": prog.completed_at.isoformat()
            if prog.completed_at
            else None,
        }
