"""Shortage appeals (SRS REQ-41).

When Available stock of a blood group is below its configured minimum (REQ-46, D-50), every
Eligible donor of that group is asked to donate, except a donor who was already asked in
the last 30 days. A threshold of 0 means no threshold.
"""

from datetime import date, timedelta

from django.utils import timezone

from core import config
from donors.models import Donor, Eligibility
from inventory.models import BloodUnit
from notifications.dispatcher import enqueue
from notifications.models import Kind, Notification

SUPPRESSION_DAYS = 30


def short_groups(today=None):
    """{group: (available, threshold)} for every group below its minimum."""
    today = today or date.today()
    short = {}
    for group in config.BLOOD_GROUPS:
        threshold = config.min_stock(group)
        if threshold <= 0:
            continue
        available = BloodUnit.objects.issuable(today).filter(blood_group=group).count()
        if available < threshold:
            short[group] = (available, threshold)
    return short


def queue_shortage_appeals(today=None, now=None):
    """Queue appeals for every short group. Returns {group: donors asked}."""
    today = today or date.today()
    now = now or timezone.now()
    recently_asked = Notification.objects.filter(
        kind=Kind.SHORTAGE_APPEAL, created_at__gt=now - timedelta(days=SUPPRESSION_DAYS)
    ).values("donor")
    asked = {}
    for group in short_groups(today):
        donors = Donor.objects.filter(
            is_active=True, blood_group=group, eligibility_status=Eligibility.ELIGIBLE
        ).exclude(pk__in=recently_asked)
        count = 0
        for donor in donors:
            enqueue(
                Kind.SHORTAGE_APPEAL,
                donor,
                subject=f"Urgent: {group} blood is needed",
                body=(
                    f"Hello {donor.full_name},\n\n"
                    f"Stock of {group} blood is running low. As a {group} donor who is "
                    "eligible to donate, you could help a patient this week. Please visit "
                    "the blood bank or enrol in an upcoming camp.\n\n"
                    "We will not send you another appeal for at least 30 days.\n"
                ),
                sms_body=(
                    f"Blood Bank: {donor.full_name}, {group} blood is urgently needed. "
                    "Please donate if you can."
                ),
            )
            count += 1
        asked[group] = count
    return asked
