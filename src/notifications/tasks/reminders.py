"""Eligibility and camp reminders (SRS REQ-40).

Run by `manage.py send_reminders`, normally every hour. Each reminder carries a dedup key,
so running the job again, or running it late, never sends the same reminder twice.
"""

from datetime import date, datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from camps.models import CampStatus, Enrolment
from donors.models import Donor, Eligibility
from notifications.dispatcher import enqueue
from notifications.models import Kind

# A donor whose date passed while the job was not running is still reminded, for a few days.
CATCH_UP_DAYS = 3


def queue_eligibility_reminders(today=None):
    """Tell each donor whose next eligible date has arrived. Returns how many were queued."""
    today = today or date.today()
    donors = Donor.objects.filter(
        is_active=True,
        next_eligible_date__lte=today,
        next_eligible_date__gte=today - timedelta(days=CATCH_UP_DAYS),
    ).filter(
        # A donation leaves the donor Temporarily Deferred until this date (D-17), and the
        # nightly job may not have cleared it yet. Any other deferral still applies.
        Q(eligibility_status=Eligibility.ELIGIBLE)
        | Q(eligibility_status=Eligibility.TEMPORARY, deferral_review_date__lte=today)
        | Q(eligibility_status=Eligibility.TEMPORARY, deferral_review_date__isnull=True)
    )
    queued = 0
    for donor in donors:
        when = f"{donor.next_eligible_date:%d-%m-%Y}"
        made = enqueue(
            Kind.ELIGIBILITY,
            donor,
            subject="You can donate blood again",
            body=(
                f"Hello {donor.full_name},\n\n"
                f"From {when} you are eligible to donate blood again. "
                "Please visit the blood bank or enrol in a donation camp.\n\n"
                f"Donor ID: {donor.donor_id}\n"
            ),
            sms_body=f"Blood Bank: {donor.full_name}, you can donate again from {when}.",
            dedup_key=f"eligible:{donor.donor_id}:{donor.next_eligible_date:%Y%m%d}",
        )
        queued += made is not None
    return queued


def camp_start(camp):
    return timezone.make_aware(datetime.combine(camp.camp_date, camp.start_time))


def queue_camp_reminders(now=None):
    """Remind enrolled donors of a camp starting in the next 24 hours. Returns the count."""
    now = now or timezone.now()
    horizon = now + timedelta(hours=24)
    enrolments = Enrolment.objects.select_related("camp", "donor").filter(
        camp__status=CampStatus.SCHEDULED,
        camp__camp_date__gte=timezone.localdate(now),
        camp__camp_date__lte=timezone.localdate(horizon),
        donor__is_active=True,
    )
    queued = 0
    for enrolment in enrolments:
        camp, donor = enrolment.camp, enrolment.donor
        if not now < camp_start(camp) <= horizon:
            continue
        when = f"{camp.camp_date:%d-%m-%Y} at {camp.start_time:%H:%M}"
        made = enqueue(
            Kind.CAMP_REMINDER,
            donor,
            subject=f"Reminder: {camp.name} tomorrow",
            body=(
                f"Hello {donor.full_name},\n\n"
                f"This is a reminder that you are enrolled in {camp.name} on {when}, "
                f"at {camp.venue_address}.\n\n"
                "Please eat a meal and drink water before you come.\n"
            ),
            sms_body=f"Blood Bank: {donor.full_name}, reminder: {camp.name} on {when}.",
            dedup_key=f"camp:{camp.camp_id}:{donor.donor_id}",
        )
        queued += made is not None
    return queued
