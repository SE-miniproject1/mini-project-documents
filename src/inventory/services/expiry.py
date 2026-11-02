"""Expiry handling (SRS REQ-19, REQ-20, NFR-S2).

Two jobs run on a schedule. One marks units that have passed their expiry date as Expired.
The other tells staff which units will expire soon. Between runs the console and the
allocation check already ignore an out-of-date unit, because `issuable()` looks at the
date as well as the status.
"""

import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import send_mail

from accounts.models import Role, User
from inventory.models import BloodUnit, InvalidTransitionError, Status

logger = logging.getLogger(__name__)

# Any unit that has not reached its end can run out of time, tested or not (SRS REQ-19).
EXPIRABLE = (Status.QUARANTINED, Status.AVAILABLE, Status.RESERVED)
EXPIRY_REASON = "Passed expiry date"


def expire_due_units(today=None, by=None):
    """Mark every unit past its expiry date Expired. Returns how many were changed."""
    today = today or date.today()
    expired = 0
    for unit in BloodUnit.objects.filter(status__in=EXPIRABLE, expiry_date__lt=today):
        try:
            unit.transition_to(Status.EXPIRED, by=by, reason=EXPIRY_REASON)
        except InvalidTransitionError:
            # Someone moved it on since the list was read. Leave it to them.
            logger.info("expiry skipped unit_id=%s", unit.unit_id)
            continue
        expired += 1
        logger.info("unit expired unit_id=%s", unit.unit_id)
    return expired


def near_expiry_units(today=None, window=None):
    """Available units that expire within the window, soonest first (SRS REQ-20)."""
    today = today or date.today()
    window = settings.BBMS_NEAR_EXPIRY_DAYS if window is None else window
    units = list(
        BloodUnit.objects.filter(
            status=Status.AVAILABLE,
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=window),
        ).order_by("expiry_date", "unit_id")
    )
    for unit in units:
        unit.days_left = (unit.expiry_date - today).days
    return units


def digest_recipients():
    return list(
        User.objects.filter(role__in=[Role.STAFF, Role.ADMIN], is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )


def send_expiry_digest(today=None):
    """One email to staff listing units about to expire. Sends nothing if there are none."""
    today = today or date.today()
    units = near_expiry_units(today)
    if not units:
        return False
    recipients = digest_recipients()
    if not recipients:
        logger.error("expiry digest has no recipients")
        return False
    lines = [
        f"{unit.unit_id}  {unit.blood_group:<3} {unit.get_component_type_display():<24} "
        f"expires {unit.expiry_date:%d-%m-%Y} ({unit.days_left} day"
        f"{'' if unit.days_left == 1 else 's'} left)"
        for unit in units
    ]
    try:
        send_mail(
            f"{len(units)} blood unit(s) expiring within {settings.BBMS_NEAR_EXPIRY_DAYS} days",
            "These available units expire soon. Use or transfer them first.\n\n"
            + "\n".join(lines)
            + "\n",
            settings.DEFAULT_FROM_EMAIL,
            recipients,
        )
    except Exception:  # noqa: BLE001 - a mail problem must not stop the expiry job
        logger.exception("expiry digest failed")
        return False
    return True
