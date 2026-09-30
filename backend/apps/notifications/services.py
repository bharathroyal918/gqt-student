"""Domain services for Notification management, Announcements, and Audience Resolution."""

import logging
from typing import Any, Dict, List, Optional
import uuid

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.accounts.models import AuditLog, User
from apps.common.exceptions import DomainException
from apps.courses.models import Course, CourseEnrollment
from apps.notifications.models import Announcement, Notification
from apps.notifications.tasks import dispatch_async_email_notification
from apps.students.models import StudentProfile

logger = logging.getLogger(__name__)


class NotificationService:
    """Core domain service for user notifications, unread counts, and idempotency."""

    @classmethod
    def send_notification(
        cls,
        recipient: User,
        title: str,
        body: str,
        notification_type: str = Notification.NotificationType.SYSTEM_NOTICE,
        action_url: str = "",
        idempotency_key: Optional[str] = None,
        send_email: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create a targeted in-app notification with duplicate prevention via idempotency."""
        # 1. Idempotency Check
        if idempotency_key:
            existing = Notification.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                logger.info(
                    "Notification with idempotency_key '%s' already exists. Returning existing.",
                    idempotency_key,
                )
                return existing

        # 2. Validate notification type
        if notification_type not in Notification.NotificationType.values:
            notification_type = Notification.NotificationType.SYSTEM_NOTICE

        # 3. Create in-app Notification
        notification = Notification.objects.create(
            recipient=recipient,
            title=title.strip()[:200],
            body=body.strip(),
            notification_type=notification_type,
            action_url=action_url.strip()[:500],
            idempotency_key=idempotency_key,
            metadata=metadata or {},
        )

        # 4. Asynchronous email delivery if requested
        if send_email and recipient.email:
            dispatch_async_email_notification(str(notification.id))

        return notification

    @classmethod
    def list_user_notifications(
        cls,
        user: User,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
    ):
        """Retrieve notifications for the authenticated user with optional filters."""
        qs = Notification.objects.filter(recipient=user).order_by("-created_at")
        if is_read is not None:
            qs = qs.filter(is_read=is_read)
        if notification_type:
            qs = qs.filter(notification_type=notification_type)
        return qs

    @classmethod
    def get_unread_count(cls, user: User) -> int:
        """Count unread notifications for the user."""
        return Notification.objects.filter(recipient=user, is_read=False).count()

    @classmethod
    @transaction.atomic
    def mark_as_read(cls, user: User, notification_id: uuid.UUID) -> Notification:
        """Mark a specific notification as read, validating ownership."""
        try:
            notification = Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            raise NotFound("Notification not found.")

        if notification.recipient_id != user.id:
            raise PermissionDenied("You do not have permission to modify this notification.")

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at", "updated_at"])

        return notification

    @classmethod
    @transaction.atomic
    def mark_all_as_read(cls, user: User) -> int:
        """Mark all unread notifications belonging to the user as read."""
        now = timezone.now()
        count = Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True,
            read_at=now,
            updated_at=now,
        )
        return count

    @classmethod
    @transaction.atomic
    def delete_notification(cls, user: User, notification_id: uuid.UUID) -> None:
        """Delete a notification belonging to the user."""
        try:
            notification = Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            raise NotFound("Notification not found.")

        if notification.recipient_id != user.id:
            raise PermissionDenied("You do not have permission to delete this notification.")

        notification.delete()


class AnnouncementAdminService:
    """Service managing platform broadcasts, audience resolution, and publishing."""

    @classmethod
    def get_announcement(cls, announcement_id: str) -> Announcement:
        return get_object_or_404(
            Announcement.objects.select_related("published_by", "target_course"),
            id=announcement_id,
        )

    @classmethod
    @transaction.atomic
    def create_announcement(
        cls,
        admin_user: User,
        title: str,
        content: str,
        target_audience: str = Announcement.TargetAudienceChoices.ALL,
        target_batch: str = "",
        target_course_id: Optional[uuid.UUID] = None,
        priority: str = Announcement.PriorityChoices.NORMAL,
        is_published: bool = True,
        expires_at: Optional[timezone.datetime] = None,
        send_email: bool = False,
        ip_address: Optional[str] = None,
    ) -> Announcement:
        if priority not in Announcement.PriorityChoices.values:
            raise DomainException(
                f"Invalid priority. Allowed choices: {Announcement.PriorityChoices.values}"
            )
        if target_audience not in Announcement.TargetAudienceChoices.values:
            target_audience = Announcement.TargetAudienceChoices.ALL

        target_course = None
        if target_course_id:
            target_course = Course.objects.filter(id=target_course_id).first()

        announcement = Announcement.objects.create(
            title=title.strip(),
            content=content.strip(),
            target_audience=target_audience,
            target_batch=target_batch.strip(),
            target_course=target_course,
            priority=priority,
            published_by=admin_user,
            is_active=True,
            is_published=is_published,
            published_at=timezone.now() if is_published else None,
            expires_at=expires_at,
        )

        AuditLog.objects.create(
            actor=admin_user,
            action="ANNOUNCEMENT_CREATED",
            target_model="Announcement",
            target_id=str(announcement.id),
            ip_address=ip_address,
            payload={
                "title": announcement.title,
                "target_audience": target_audience,
                "target_batch": target_batch or "GLOBAL",
                "priority": priority,
                "is_published": is_published,
            },
        )

        if is_published:
            cls.publish_announcement(
                announcement=announcement,
                admin_user=admin_user,
                send_email=send_email,
                ip_address=ip_address,
            )

        return announcement

    @classmethod
    @transaction.atomic
    def publish_announcement(
        cls,
        announcement: Announcement,
        admin_user: Optional[User] = None,
        send_email: bool = False,
        ip_address: Optional[str] = None,
    ) -> int:
        """Resolve target audience and fan-out in-app notifications and async emails."""
        # 1. Resolve Target Audience
        user_ids = cls._resolve_audience_users(announcement)
        delivery_count = 0
        email_count = 0

        users = User.objects.filter(id__in=user_ids)
        for user in users:
            idempotency_key = f"announcement_{announcement.id}_{user.id}"
            notif = NotificationService.send_notification(
                recipient=user,
                title=f"📢 {announcement.title}",
                body=announcement.content,
                notification_type=Notification.NotificationType.ADMIN_ANNOUNCEMENT,
                action_url="/notifications",
                idempotency_key=idempotency_key,
                send_email=send_email,
                metadata={"announcement_id": str(announcement.id), "priority": announcement.priority},
            )
            delivery_count += 1
            if send_email and user.email:
                email_count += 1

        # 2. Update announcement metrics
        announcement.is_published = True
        announcement.published_at = timezone.now()
        announcement.delivery_count = delivery_count
        announcement.email_sent_count = email_count
        announcement.save(
            update_fields=["is_published", "published_at", "delivery_count", "email_sent_count", "updated_at"]
        )

        if admin_user:
            AuditLog.objects.create(
                actor=admin_user,
                action="ANNOUNCEMENT_PUBLISHED",
                target_model="Announcement",
                target_id=str(announcement.id),
                ip_address=ip_address,
                payload={
                    "recipients_count": delivery_count,
                    "emails_queued": email_count,
                },
            )

        return delivery_count

    @classmethod
    def _resolve_audience_users(cls, announcement: Announcement) -> List[uuid.UUID]:
        """Resolve list of user IDs targeted by the announcement scope."""
        if announcement.target_audience == Announcement.TargetAudienceChoices.ALL:
            return list(
                StudentProfile.objects.filter(user__is_active=True).values_list("user_id", flat=True)
            )

        elif announcement.target_audience == Announcement.TargetAudienceChoices.BATCH:
            if not announcement.target_batch:
                return list(
                    StudentProfile.objects.filter(user__is_active=True).values_list("user_id", flat=True)
                )
            return list(
                StudentProfile.objects.filter(
                    batch_code__iexact=announcement.target_batch, user__is_active=True
                ).values_list("user_id", flat=True)
            )

        elif announcement.target_audience == Announcement.TargetAudienceChoices.COURSE and announcement.target_course:
            return list(
                CourseEnrollment.objects.filter(
                    course=announcement.target_course,
                    status=CourseEnrollment.EnrollmentStatus.ACTIVE,
                ).values_list("student__user_id", flat=True)
            )

        return list(
            StudentProfile.objects.filter(user__is_active=True).values_list("user_id", flat=True)
        )

    @classmethod
    @transaction.atomic
    def update_announcement(
        cls,
        announcement_id: str,
        admin_user: User,
        title: Optional[str] = None,
        content: Optional[str] = None,
        target_audience: Optional[str] = None,
        target_batch: Optional[str] = None,
        target_course_id: Optional[uuid.UUID] = None,
        priority: Optional[str] = None,
        expires_at: Optional[timezone.datetime] = None,
        is_active: Optional[bool] = None,
        ip_address: Optional[str] = None,
    ) -> Announcement:
        announcement = cls.get_announcement(announcement_id)
        update_fields = ["updated_at"]

        if title is not None:
            announcement.title = title.strip()
            update_fields.append("title")

        if content is not None:
            announcement.content = content.strip()
            update_fields.append("content")

        if target_audience is not None:
            announcement.target_audience = target_audience
            update_fields.append("target_audience")

        if target_batch is not None:
            announcement.target_batch = target_batch.strip()
            update_fields.append("target_batch")

        if target_course_id is not None:
            announcement.target_course = Course.objects.filter(id=target_course_id).first()
            update_fields.append("target_course")

        if priority is not None:
            if priority not in Announcement.PriorityChoices.values:
                raise DomainException("Invalid priority specified.")
            announcement.priority = priority
            update_fields.append("priority")

        if expires_at is not None:
            announcement.expires_at = expires_at
            update_fields.append("expires_at")

        if is_active is not None:
            announcement.is_active = is_active
            update_fields.append("is_active")

        announcement.save(update_fields=update_fields)

        AuditLog.objects.create(
            actor=admin_user,
            action="ANNOUNCEMENT_UPDATED",
            target_model="Announcement",
            target_id=str(announcement.id),
            ip_address=ip_address,
            payload={"updated_fields": update_fields},
        )
        return announcement

    @classmethod
    @transaction.atomic
    def delete_announcement(
        cls, announcement_id: str, admin_user: User, ip_address: Optional[str] = None
    ) -> None:
        announcement = cls.get_announcement(announcement_id)
        announcement.is_active = False
        announcement.save(update_fields=["is_active", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="ANNOUNCEMENT_DEACTIVATED",
            target_model="Announcement",
            target_id=str(announcement.id),
            ip_address=ip_address,
        )

    @classmethod
    def get_student_announcements(cls, user: User):
        """Fetch active, published announcements targeting the student's scope."""
        student = StudentProfile.objects.filter(user=user).first()
        now = timezone.now()

        base_qs = Announcement.objects.filter(
            is_active=True,
            is_published=True,
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        ).select_related("published_by")

        if not student:
            return base_qs.filter(target_audience=Announcement.TargetAudienceChoices.ALL)

        enrolled_course_ids = CourseEnrollment.objects.filter(
            student=student, status=CourseEnrollment.EnrollmentStatus.ACTIVE
        ).values_list("course_id", flat=True)

        return base_qs.filter(
            models.Q(target_audience=Announcement.TargetAudienceChoices.ALL)
            | models.Q(
                target_audience=Announcement.TargetAudienceChoices.BATCH,
                target_batch__iexact=student.batch_code,
            )
            | models.Q(
                target_audience=Announcement.TargetAudienceChoices.COURSE,
                target_course_id__in=enrolled_course_ids,
            )
        ).order_by("-created_at")
