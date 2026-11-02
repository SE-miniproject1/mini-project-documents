"""Allocating, issuing and releasing units (SRS REQ-28 to REQ-31, NFR-S1 to NFR-S4).

Every operation runs in one transaction. The request row is locked first, then the unit
rows in identifier order, so two staff working on the same request or the same unit are
serialised and cannot deadlock. A unit is re-checked under its lock, so what was true when
the screen was drawn does not matter.
"""

from datetime import date

from django.db import transaction
from django.utils import timezone

from audit.models import Event
from audit.services import record_event
from inventory.models import BloodUnit, Status

from .models import Allocation, BloodRequest, RequestStatus
from .workflow import WorkflowError, notify_hospital

ALLOCATABLE = (RequestStatus.APPROVED, RequestStatus.PARTIAL)
CANCELLABLE = (RequestStatus.PENDING, RequestStatus.APPROVED)


def candidate_units(blood_request, today=None):
    """Units that could be allocated now: exact group and component, Available, unexpired.

    Earliest expiry first, so older stock goes out before newer (SRS BR-8: exact match only).
    """
    return (
        BloodUnit.objects.issuable(today or date.today())
        .filter(
            blood_group=blood_request.blood_group,
            component_type=blood_request.component_type,
        )
        .order_by("expiry_date", "unit_id")
    )


def live_allocations(blood_request):
    return blood_request.allocations.filter(released_at__isnull=True).select_related("unit")


def reserved_allocations(blood_request):
    return live_allocations(blood_request).filter(issued_at__isnull=True)


def _audit(blood_request, unit, by, text, previous="", new=""):
    record_event(
        Event.ALLOCATION,
        actor=by,
        entity_type="Request",
        entity_id=blood_request.request_id,
        previous=previous,
        new=new,
        reason=f"{unit.unit_id}: {text}",
    )


def _lock_request(request, expected, action):
    current = BloodRequest.objects.select_for_update().get(pk=request.pk)
    if current.status not in expected:
        raise WorkflowError(f"Request {current.request_id} is {current.status}; cannot {action}.")
    return current


@transaction.atomic
def allocate_units(request, unit_ids, *, by, today=None):
    """Reserve the chosen units for an approved request. All or none."""
    today = today or date.today()
    current = _lock_request(request, ALLOCATABLE, "allocate units")
    unit_ids = sorted(set(unit_ids))
    if not unit_ids:
        raise WorkflowError("Choose at least one unit.")
    outstanding = current.quantity_requested - current.quantity_issued
    already = reserved_allocations(current).count()
    if len(unit_ids) + already > outstanding:
        raise WorkflowError(
            f"Only {outstanding - already} more unit(s) are needed; you chose {len(unit_ids)}."
        )
    units = {
        unit.unit_id: unit
        for unit in BloodUnit.objects.select_for_update()
        .filter(unit_id__in=unit_ids)
        .order_by("unit_id")
    }
    for unit_id in unit_ids:
        unit = units.get(unit_id)
        if unit is None:
            raise WorkflowError(f"Unit {unit_id} does not exist.")
        if unit.blood_group != current.blood_group:
            raise WorkflowError(
                f"Unit {unit_id} is {unit.blood_group}; this request needs {current.blood_group}."
            )
        if unit.component_type != current.component_type:
            raise WorkflowError(
                f"Unit {unit_id} is {unit.component_type}; "
                f"this request needs {current.component_type}."
            )
        if unit.expiry_date < today:
            raise WorkflowError(f"Unit {unit_id} has expired.")
        if unit.status != Status.AVAILABLE:
            raise WorkflowError(f"Unit {unit_id} is {unit.status}, not Available.")
    for unit_id in unit_ids:
        unit = units[unit_id]
        unit.transition_to(Status.RESERVED, by=by, reason=f"Reserved for {current.request_id}")
        Allocation.objects.create(request=current, unit=unit, allocated_by=by)
        _audit(current, unit, by, "reserved", Status.AVAILABLE, Status.RESERVED)
    return [units[i] for i in unit_ids]


@transaction.atomic
def issue_reserved(request, *, by, today=None):
    """Confirm issue of every reserved unit, then set Fulfilled or Partially Fulfilled."""
    today = today or date.today()
    current = _lock_request(request, ALLOCATABLE, "issue units")
    allocations = list(reserved_allocations(current).order_by("unit__unit_id"))
    if not allocations:
        raise WorkflowError("No units are reserved for this request.")
    now = timezone.now()
    for allocation in allocations:
        unit = BloodUnit.objects.select_for_update().get(pk=allocation.unit_id)
        if unit.status != Status.RESERVED:
            raise WorkflowError(f"Unit {unit.unit_id} is {unit.status}, not Reserved.")
        if unit.expiry_date < today:
            raise WorkflowError(f"Unit {unit.unit_id} has expired and cannot be issued.")
        unit.transition_to(Status.ISSUED, by=by, reason=f"Issued to {current.hospital.name}")
        allocation.issued_by = by
        allocation.issued_at = now
        allocation.save(update_fields=["issued_by", "issued_at"])
        _audit(
            current, unit, by, f"issued to {current.hospital.name}", Status.RESERVED, Status.ISSUED
        )
    previous = current.status
    current.quantity_issued += len(allocations)
    current.status = (
        RequestStatus.FULFILLED
        if current.quantity_issued >= current.quantity_requested
        else RequestStatus.PARTIAL
    )
    current.save(update_fields=["quantity_issued", "status", "updated_on"])
    record_event(
        Event.REQUEST_STATUS,
        actor=by,
        entity_type="Request",
        entity_id=current.request_id,
        previous=previous,
        new=current.status,
        reason=f"{current.quantity_issued} of {current.quantity_requested} issued",
    )
    text = f"Request {current.request_id}: {len(allocations)} unit(s) issued, "
    text += (
        "the request is fulfilled."
        if current.status == RequestStatus.FULFILLED
        else f"{current.shortfall} still outstanding."
    )
    transaction.on_commit(lambda: notify_hospital(current, text))
    return current


def _release(allocation, *, by, reason):
    unit = BloodUnit.objects.select_for_update().get(pk=allocation.unit_id)
    if unit.status == Status.RESERVED:
        unit.transition_to(Status.AVAILABLE, by=by, reason=reason)
    allocation.released_at = timezone.now()
    allocation.release_reason = reason[:60]
    allocation.save(update_fields=["released_at", "release_reason"])
    _audit(allocation.request, unit, by, reason, Status.RESERVED, unit.status)


@transaction.atomic
def release_allocation(allocation_id, *, by):
    """Give a reserved, not yet issued unit back to stock."""
    allocation = (
        Allocation.objects.select_for_update().select_related("request").get(pk=allocation_id)
    )
    if allocation.released_at or allocation.issued_at:
        raise WorkflowError("Only a reserved unit can be released.")
    _lock_request(allocation.request, ALLOCATABLE, "release units")
    _release(allocation, by=by, reason="Released by staff")


@transaction.atomic
def cancel_request(request, *, by):
    """The hospital cancels its own request before anything is issued (SRS REQ-31)."""
    current = _lock_request(request, CANCELLABLE, "be cancelled")
    if current.quantity_issued or current.allocations.filter(issued_at__isnull=False).exists():
        raise WorkflowError("A request with issued units cannot be cancelled.")
    for allocation in reserved_allocations(current).select_for_update():
        _release(allocation, by=by, reason="Request cancelled")
    previous = current.status
    current.status = RequestStatus.CANCELLED
    current.save(update_fields=["status", "updated_on"])
    record_event(
        Event.REQUEST_STATUS,
        actor=by,
        entity_type="Request",
        entity_id=current.request_id,
        previous=previous,
        new=current.status,
        reason="Cancelled by hospital",
    )
    return current


def release_for_lost_unit(unit, *, by=None, reason):
    """A reserved unit expired or was discarded: free its claim so the request can be served."""
    for allocation in Allocation.objects.select_for_update().filter(
        unit=unit, released_at__isnull=True, issued_at__isnull=True
    ):
        allocation.released_at = timezone.now()
        allocation.release_reason = reason[:60]
        allocation.save(update_fields=["released_at", "release_reason"])
        _audit(allocation.request, unit, by, reason, Status.RESERVED, unit.status)
