"""Creating camps and enrolling donors (SRS REQ-32 to REQ-35)."""

import logging
from datetime import date

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction

from audit.models import Event
from audit.services import record_event
from core.models import IdSequence
from donors.models import Eligibility
from donors.services.eligibility import next_eligible_date

from .models import Camp, CampStatus, Enrolment

logger = logging.getLogger(__name__)

SEQUENCE = "camp"
FIRST_NUMBER = 1000001


class CampError(Exception):
    """A camp action was refused. `field` names the field in error where there is one."""

    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field


def generate_camp_id():
    return f"CMP{IdSequence.next_value(SEQUENCE, FIRST_NUMBER)}"


def create_camp(
    user,
    *,
    name,
    venue_address,
    camp_date,
    start_time,
    end_time,
    organiser_name,
    organiser_contact,
    target_units,
    today=None,
):
    today = today or date.today()
    if camp_date < today:
        raise CampError("Camp date cannot be in the past.", "camp_date")
    if end_time <= start_time:
        raise CampError("End time must be later than the start time.", "end_time")
    if target_units < 1:
        raise CampError("Target units must be at least 1.", "target_units")
    camp = Camp.objects.create(
        camp_id=generate_camp_id(),
        name=name,
        venue_address=venue_address,
        camp_date=camp_date,
        start_time=start_time,
        end_time=end_time,
        organiser_name=organiser_name,
        organiser_contact=organiser_contact,
        target_units=target_units,
        created_by=user,
    )
    record_event(
        Event.CONFIG_CHANGE,
        actor=user,
        entity_type="Camp",
        entity_id=camp.camp_id,
        new=CampStatus.SCHEDULED,
        reason="Camp scheduled",
    )
    return camp


def upcoming_camps(today=None):
    """Scheduled camps that have not yet happened, soonest first (SRS REQ-34)."""
    return Camp.objects.filter(
        status=CampStatus.SCHEDULED, camp_date__gte=today or date.today()
    ).order_by("camp_date", "start_time", "camp_id")


def eligible_from(donor):
    """The first date the donor could donate again, or None if there is no barrier."""
    dates = []
    if donor.last_donation_date:
        dates.append(next_eligible_date(donor.last_donation_date))
    if donor.eligibility_status == Eligibility.TEMPORARY and donor.deferral_review_date:
        dates.append(donor.deferral_review_date)
    return max(dates) if dates else None


def enrol_donor(camp, donor, *, today=None):
    """Enrol `donor` if they will be eligible on the camp date (SRS REQ-35)."""
    today = today or date.today()
    if camp.status != CampStatus.SCHEDULED or camp.camp_date < today:
        raise CampError("This camp is not open for enrolment.")
    if not donor.is_active:
        raise CampError("The donor record is deactivated.")
    if donor.eligibility_status == Eligibility.PERMANENT:
        raise CampError("You cannot donate blood, so you cannot enrol in a camp.")
    barrier = eligible_from(donor)
    if donor.eligibility_status == Eligibility.TEMPORARY and not donor.deferral_review_date:
        raise CampError("You are temporarily deferred, so you cannot enrol yet.")
    if barrier and barrier > camp.camp_date:
        raise CampError(
            f"You will not be eligible by {camp.camp_date:%d-%m-%Y}. "
            f"You become eligible on {barrier:%d-%m-%Y}."
        )
    try:
        with transaction.atomic():
            enrolment = Enrolment.objects.create(camp=camp, donor=donor)
    except IntegrityError:
        raise CampError("You are already enrolled in this camp.") from None
    transaction.on_commit(lambda: send_confirmation(enrolment))
    return enrolment


def send_confirmation(enrolment):
    donor, camp = enrolment.donor, enrolment.camp
    address = donor.email
    if not address:
        return False
    try:
        send_mail(
            f"Enrolled: {camp.name}",
            f"You are enrolled in {camp.name} on {camp.camp_date:%d-%m-%Y}, "
            f"{camp.start_time:%H:%M} to {camp.end_time:%H:%M}, at {camp.venue_address}.\n",
            settings.DEFAULT_FROM_EMAIL,
            [address],
        )
    except Exception:  # noqa: BLE001 - a mail problem must not undo the enrolment
        logger.exception("camp confirmation failed for %s", enrolment.pk)
        return False
    return True
