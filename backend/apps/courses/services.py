"""Domain services for administrative course management."""

from typing import Optional
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from apps.accounts.models import AuditLog, User
from apps.common.exceptions import DomainException
from apps.courses.models import Course


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
        slug: Optional[str] = None,
        is_published: bool = False,
        order: int = 0,
        ip_address: Optional[str] = None,
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
        title: Optional[str] = None,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        is_published: Optional[bool] = None,
        order: Optional[int] = None,
        ip_address: Optional[str] = None,
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
        cls, course_id: str, admin_user: User, ip_address: Optional[str] = None
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
        cls, course_id: str, is_published: bool, admin_user: User, ip_address: Optional[str] = None
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
