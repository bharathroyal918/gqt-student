"""Asynchronous email delivery worker with retry handling and non-blocking execution."""

import concurrent.futures
import logging
import smtplib
import time

from django.conf import settings
from django.core.mail import send_mail
from django.db import DatabaseError
from django.utils import timezone

from apps.common.utils import mask_email

logger = logging.getLogger(__name__)

# Global thread pool executor for non-blocking asynchronous email dispatch
_email_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="email_dispatch_worker"
)


def _deliver_email_worker(
    notification_id: str, max_retries: int = 3, base_delay: float = 0.5
) -> bool:
    """Worker function executed in background thread with retry handling."""
    from apps.notifications.models import Notification

    try:
        notification = Notification.objects.select_related("recipient").get(
            id=notification_id
        )
    except Notification.DoesNotExist:
        logger.warning(
            "Notification %s not found for async email dispatch.", notification_id
        )
        return False

    recipient_email = getattr(notification.recipient, "email", None)
    if not recipient_email:
        logger.info(
            "Recipient for notification %s has no email address. Skipping email.",
            notification_id,
        )
        return False

    sender_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@gqt.local")
    subject = f"[GQT Portal] {notification.title}"
    recipient_name = getattr(notification.recipient, "email", "Student")
    if (
        hasattr(notification.recipient, "student_profile")
        and notification.recipient.student_profile
    ):
        recipient_name = (
            notification.recipient.student_profile.full_name or recipient_name
        )

    body = (
        f"Hello {recipient_name},\n\n"
        f"{notification.body}\n\n"
        f"Notification Type: {notification.get_notification_type_display()}\n"
        f"Time: {notification.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        f"---\n"
        f"GQT Student Portal — Automated Learning & Assessment System"
    )

    attempt = 0
    while attempt < max_retries:
        try:
            attempt += 1
            logger.info(
                "Dispatching async email for notification %s to %s (attempt %d/%d)",
                notification_id,
                mask_email(recipient_email),
                attempt,
                max_retries,
            )
            # Send email via Django email backend
            send_mail(
                subject=subject,
                message=body,
                from_email=sender_email,
                recipient_list=[recipient_email],
                fail_silently=False,
            )

            # Update notification record on success
            notification.email_sent = True
            notification.email_sent_at = timezone.now()
            notification.save(update_fields=["email_sent", "email_sent_at"])
            logger.info("Successfully sent email for notification %s", notification_id)
            return True

        except (
            smtplib.SMTPException,
            OSError,
            TimeoutError,
            DatabaseError,
            ValueError,
        ) as exc:
            logger.warning(
                "Failed to send email for notification %s on attempt %d: %s",
                notification_id,
                attempt,
                str(exc),
            )
            if attempt < max_retries:
                # Exponential backoff
                sleep_time = base_delay * (2 ** (attempt - 1))
                time.sleep(sleep_time)
            else:
                logger.error(
                    "All %d email delivery retries exhausted for notification %s.",
                    max_retries,
                    notification_id,
                )
                return False

    return False


def dispatch_async_email_notification(
    notification_id: str, max_retries: int = 3
) -> concurrent.futures.Future:
    """Submit email delivery job to the background thread pool non-blockingly."""
    return _email_executor.submit(_deliver_email_worker, notification_id, max_retries)
