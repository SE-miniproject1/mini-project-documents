"""Queue and send donor notifications (SRS REQ-39, NFR-P6, CI-4, CI-6).

`enqueue` only writes a row, so it is safe inside any transaction: the message exists once
that transaction commits and never if it rolls back. `dispatch_due` runs in the worker
(`manage.py dispatch_notifications`) and talks to the gateways. A gateway failure is
recorded on the row and never reaches the code that asked for the message.

SMS is tried `BBMS_NOTIFY_SMS_ATTEMPTS` times, waiting longer after each failure. After the
last failure the message goes by email and the SMS failure stays on the record. Email is
retried the same way and the row is marked Failed if every attempt fails.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.html import escape, linebreaks

from .models import Channel, Notification, NotificationStatus
from .sms import get_backend

logger = logging.getLogger(__name__)


def enqueue(kind, donor, *, subject, body, sms_body, dedup_key=None):
    """Queue one message to `donor`. Returns the row, or None if `dedup_key` was already used."""
    fields = {
        "kind": kind,
        "donor": donor,
        "mobile_number": donor.mobile_number or "",
        "email": donor.email or "",
        "subject": subject,
        "body": body,
        "sms_body": sms_body[:160],
        "dedup_key": dedup_key,
        "channel": Channel.SMS if donor.mobile_number else Channel.EMAIL,
        "next_attempt_at": timezone.now(),
    }
    if dedup_key is None:
        return Notification.objects.create(**fields)
    try:
        with transaction.atomic():
            return Notification.objects.create(**fields)
    except IntegrityError:
        return None


def _retry_delay(attempts):
    """Seconds to wait after the `attempts`-th failure; grows with each failure."""
    delays = settings.BBMS_NOTIFY_RETRY_SECONDS
    return delays[min(attempts, len(delays)) - 1]


def _send_email(notification):
    message = EmailMultiAlternatives(
        notification.subject,
        notification.body,
        settings.DEFAULT_FROM_EMAIL,
        [notification.email],
    )
    message.attach_alternative(linebreaks(escape(notification.body)), "text/html")
    message.send()


def _attempt(notification, now):
    """One delivery attempt. Updates the row in memory; the caller saves it."""
    limit = settings.BBMS_NOTIFY_SMS_ATTEMPTS
    if notification.channel == Channel.SMS:
        notification.sms_attempts += 1
        try:
            notification.gateway_status = get_backend().send(
                notification.mobile_number, notification.sms_body
            )
        except Exception as exc:  # noqa: BLE001 - any gateway problem counts as a failure
            notification.last_error = f"SMS attempt {notification.sms_attempts}: {exc}"[:255]
            logger.warning("sms failed id=%s error=%s", notification.pk, exc)
            if notification.sms_attempts < limit:
                notification.next_attempt_at = now + timedelta(
                    seconds=_retry_delay(notification.sms_attempts)
                )
                return
            if not notification.email:
                notification.status = NotificationStatus.FAILED
                return
            # Fall back to email straight away, keeping the SMS failure on the record.
            notification.channel = Channel.EMAIL
        else:
            notification.status = NotificationStatus.SENT
            notification.sent_via = Channel.SMS
            notification.sent_at = now
            return

    notification.email_attempts += 1
    try:
        _send_email(notification)
    except Exception as exc:  # noqa: BLE001 - see above
        notification.last_error = f"Email attempt {notification.email_attempts}: {exc}"[:255]
        logger.warning("email failed id=%s error=%s", notification.pk, exc)
        if notification.email_attempts < limit:
            notification.next_attempt_at = now + timedelta(
                seconds=_retry_delay(notification.email_attempts)
            )
        else:
            notification.status = NotificationStatus.FAILED
        return
    notification.status = NotificationStatus.SENT
    notification.sent_via = Channel.EMAIL
    notification.sent_at = now


def dispatch_due(now=None, limit=100):
    """Try every queued message whose next attempt is due. Returns how many were tried."""
    now = now or timezone.now()
    tried = 0
    due = Notification.objects.filter(
        status=NotificationStatus.QUEUED, next_attempt_at__lte=now
    ).order_by("next_attempt_at", "pk")
    for pk in list(due.values_list("pk", flat=True)[:limit]):
        with transaction.atomic():
            # Two workers must not send the same message twice.
            notification = (
                Notification.objects.select_for_update(skip_locked=True)
                .filter(pk=pk, status=NotificationStatus.QUEUED)
                .first()
            )
            if notification is None:
                continue
            _attempt(notification, now)
            notification.save()
        tried += 1
    return tried
