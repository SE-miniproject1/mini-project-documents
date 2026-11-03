from django.db import transaction

from audit.models import Event
from audit.services import record_event
from inventory.models import BloodUnit, InvalidTransitionError, Status


class ActionError(Exception):
    """A transfer or discard request cannot be completed."""


@transaction.atomic
def transfer_unit(unit, destination, *, by):
    destination = destination.strip()
    if not destination:
        raise ActionError("Enter a destination storage location.")
    current = BloodUnit.objects.select_for_update().get(pk=unit.pk)
    if current.status in (Status.ISSUED, Status.DISCARDED):
        raise ActionError(f"A {current.status} unit cannot be transferred.")
    if current.storage_location == destination:
        raise ActionError("Choose a different destination from the current location.")
    source = current.storage_location
    current.storage_location = destination
    current.save(update_fields=["storage_location"])
    record_event(
        Event.LOCATION_TRANSFER,
        actor=by,
        entity_type="BloodUnit",
        entity_id=current.unit_id,
        previous=source,
        new=destination,
        reason="Storage location transfer",
    )
    unit.storage_location = destination
    return unit


@transaction.atomic
def discard_unit(unit, reason, *, by):
    reason = reason.strip()
    if not reason:
        raise ActionError("A discard reason is required.")
    current = BloodUnit.objects.select_for_update().get(pk=unit.pk)
    if current.status in (Status.ISSUED, Status.DISCARDED):
        raise ActionError(f"A {current.status} unit cannot be discarded.")
    try:
        current.transition_to(Status.DISCARDED, by=by, reason=reason)
    except InvalidTransitionError as problem:
        raise ActionError(str(problem)) from problem
    unit.status = current.status
    unit.discard_reason = current.discard_reason
    return unit
