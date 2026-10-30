"""Account lockout after repeated failed sign-ins (SRS NFR-SEC4).

Five consecutive failures lock the account for 15 minutes and the holder is
told by email. A successful sign-in resets the count.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


def is_locked(user, now=None):
    now = now or timezone.now()
    return bool(user.locked_until and user.locked_until > now)


def minutes_remaining(user, now=None):
    now = now or timezone.now()
    if not is_locked(user, now):
        return 0
    seconds = (user.locked_until - now).total_seconds()
    return max(1, int(-(-seconds // 60)))


def register_failure(user):
    """Count a failed attempt. Locks the account when the threshold is reached."""
    user.failed_login_count += 1
    if user.failed_login_count >= settings.BBMS_LOCKOUT_THRESHOLD:
        user.failed_login_count = 0
        user.locked_until = timezone.now() + timedelta(minutes=settings.BBMS_LOCKOUT_MINUTES)
        user.save(update_fields=["failed_login_count", "locked_until"])
        logger.warning("account locked user_id=%s", user.pk)
        transaction.on_commit(lambda: _notify_locked(user))
        return True
    user.save(update_fields=["failed_login_count"])
    return False


def reset(user):
    if user.failed_login_count or user.locked_until:
        user.failed_login_count = 0
        user.locked_until = None
        user.save(update_fields=["failed_login_count", "locked_until"])


def _notify_locked(user):
    """Never let a mail failure affect sign-in (SRS CI-6)."""
    try:
        send_mail(
            "Your Blood Bank account was locked",
            (
                f"Hello {user.get_username()},\n\n"
                f"There were {settings.BBMS_LOCKOUT_THRESHOLD} failed sign-in attempts on your "
                f"account. It is locked for {settings.BBMS_LOCKOUT_MINUTES} minutes. If this was "
                "not you, change your password after the lock ends.\n"
            ),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
    except Exception:  # noqa: BLE001 - delivery problems must not break authentication
        logger.exception("lockout email failed user_id=%s", user.pk)
