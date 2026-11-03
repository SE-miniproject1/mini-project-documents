"""Build the six reports from the database (SRS REQ-42, REQ-44, Appendix B.7).

`generate(slug, start, end, user)` checks the user may run the report, reads the rows for the
date range and returns a ReportResult. Every row is a tuple in the exact column order of its
ReportSpec. Hospital scoping comes from `access.hospital_scope`, never from the request.
"""

from collections import defaultdict
from datetime import date, datetime, time, timedelta

from django.core.exceptions import PermissionDenied
from django.db.models import Count, Max
from django.utils import timezone

from audit.models import AuditEntry, Event
from bloodrequests.models import BloodRequest
from camps.models import Camp
from collection.models import Donation, TestName, TestResult
from core import config
from donors.models import Donor
from inventory.models import BloodUnit, Status

from ..access import can_run, hospital_scope
from ..definitions import REPORTS
from .result import ReportResult

# NFR-P4 sets 12 months as the range a report must handle in 30 seconds.
MAX_RANGE_DAYS = 366


class ReportError(Exception):
    pass


def _aware_bounds(start, end):
    """[start 00:00, day after end 00:00) in local time, for datetime fields."""
    low = timezone.make_aware(datetime.combine(start, time.min))
    high = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min))
    return low, high


def screening_outcome(results):
    """Cleared, Reactive or Pending from a unit's (test, result) pairs."""
    if any(result != TestResult.NON_REACTIVE for _, result in results):
        return "Reactive"
    if {name for name, _ in results} >= set(TestName.values):
        return "Cleared"
    return "Pending"


def _registration(start, end, scope):
    donors = (
        Donor.objects.filter(registration_date__range=(start, end))
        .annotate(total=Count("donations"))
        .order_by("registration_date", "donor_id")
    )
    return [
        (
            d.donor_id,
            d.full_name,
            d.blood_group,
            d.mobile_number,
            d.city,
            d.registration_date,
            d.eligibility_status,
            d.last_donation_date,
            d.next_eligible_date,
            d.total,
        )
        for d in donors
    ]


def _collection(start, end, scope):
    low, high = _aware_bounds(start, end)
    donations = (
        Donation.objects.filter(collected_at__gte=low, collected_at__lt=high)
        .select_related("unit", "donor")
        .prefetch_related("unit__tests")
        .order_by("collected_at", "pk")
    )
    rows = []
    for d in donations:
        tests = [(t.test_name, t.result) for t in d.unit.tests.all()]
        rows.append(
            (
                d.unit.unit_id,
                d.donor.donor_id,
                d.unit.blood_group,
                d.unit.component_type,
                d.volume_ml,
                timezone.localtime(d.collected_at).date(),
                d.collection_site,
                d.bag_lot_number,
                screening_outcome(tests),
                d.unit.status,
            )
        )
    return rows


def _inventory(start, end, scope):
    """Stock as it stands at `end` (or today, if earlier), by group and component."""
    as_of = min(end, date.today())
    window = config.near_expiry_days()
    groups = defaultdict(lambda: defaultdict(int))
    locations, oldest = defaultdict(set), {}
    units = BloodUnit.objects.filter(collection_date__lte=as_of).exclude(
        status__in=(Status.ISSUED, Status.DISCARDED)
    )
    for unit in units:
        key = (unit.blood_group, unit.component_type)
        cell = groups[key]
        lapsed = unit.expiry_date < as_of or unit.status == Status.EXPIRED
        if lapsed:
            cell["expired"] += 1
            continue
        cell[unit.status] += 1
        if unit.status == Status.AVAILABLE:
            cell["volume"] += unit.volume_ml
            locations[key].add(unit.storage_location)
            oldest[key] = min(oldest.get(key, unit.expiry_date), unit.expiry_date)
            if unit.expiry_date <= as_of + timedelta(days=window):
                cell["near"] += 1
    return [
        (
            group,
            component,
            cell[Status.AVAILABLE],
            cell[Status.RESERVED],
            cell[Status.QUARANTINED],
            cell["near"],
            cell["expired"],
            ", ".join(sorted(locations[(group, component)])),
            oldest.get((group, component)),
            cell["volume"],
        )
        for (group, component), cell in sorted(groups.items())
    ]


def _expiry(start, end, scope):
    units = list(
        BloodUnit.objects.filter(expiry_date__range=(start, end)).order_by(
            "expiry_date", "unit_id"
        )
    )
    # Who moved each unit to its current status, from the audit log (SRS REQ-23).
    recorded = {}
    for entry in AuditEntry.objects.filter(
        event=Event.UNIT_STATUS,
        entity_type="BloodUnit",
        entity_id__in=[u.unit_id for u in units],
    ).order_by("occurred_at", "pk"):
        recorded[(entry.entity_id, entry.new_value)] = entry.actor_username or "system"
    today = date.today()
    return [
        (
            u.unit_id,
            u.blood_group,
            u.component_type,
            u.collection_date,
            u.expiry_date,
            (u.expiry_date - today).days,
            u.storage_location,
            u.status,
            u.discard_reason,
            recorded.get((u.unit_id, u.status), ""),
        )
        for u in units
    ]


def _request_issue(start, end, scope):
    low, high = _aware_bounds(start, end)
    requests = (
        BloodRequest.objects.filter(raised_on__gte=low, raised_on__lt=high)
        .select_related("hospital")
        .annotate(last_issue=Max("allocations__issued_at"))
        .order_by("raised_on", "request_id")
    )
    if scope is not None:
        requests = requests.filter(hospital=scope)
    return [
        (
            r.request_id,
            r.hospital.name,
            r.blood_group,
            r.component_type,
            r.quantity_requested,
            r.quantity_issued,
            r.urgency,
            timezone.localtime(r.raised_on),
            timezone.localtime(r.last_issue) if r.last_issue else None,
            r.status,
        )
        for r in requests
    ]


def _camp(start, end, scope):
    camps = (
        Camp.objects.filter(camp_date__range=(start, end))
        .annotate(enrolled=Count("enrolments", distinct=True))
        .order_by("camp_date", "camp_id")
    )
    attended = defaultdict(set)
    units = defaultdict(int)
    for site, donor in Donation.objects.filter(
        collection_site__in=[c.camp_id for c in camps]
    ).values_list("collection_site", "donor_id"):
        attended[site].add(donor)
        units[site] += 1
    rows = []
    for c in camps:
        collected = c.units_collected if c.units_collected is not None else units[c.camp_id]
        rows.append(
            (
                c.camp_id,
                c.name,
                c.camp_date,
                c.venue_address,
                c.organiser_name,
                c.enrolled,
                len(attended[c.camp_id]),
                c.target_units,
                collected,
                f"{collected * 100 / c.target_units:.1f}%",
            )
        )
    return rows


BUILDERS = {
    "registration": _registration,
    "collection": _collection,
    "inventory": _inventory,
    "expiry": _expiry,
    "request-issue": _request_issue,
    "camp": _camp,
}


def validate_range(start, end):
    if start is None or end is None:
        raise ReportError("Choose a start and an end date.")
    if end < start:
        raise ReportError("The end date is before the start date.")
    if (end - start).days >= MAX_RANGE_DAYS:
        raise ReportError("Choose a range of at most 12 months.")


def generate(slug, start, end, user, now=None):
    """Run report `slug` for `user` over [start, end]. Raises PermissionDenied or ReportError."""
    if slug not in REPORTS or not can_run(user, slug):
        raise PermissionDenied
    validate_range(start, end)
    scope = hospital_scope(user)
    spec = REPORTS[slug]
    rows = BUILDERS[slug](start, end, scope)
    return ReportResult(
        title=spec.title,
        columns=spec.columns,
        rows=tuple(rows),
        start=start,
        end=end,
        generated_by=user.username,
        generated_at=now or timezone.now(),
    )
