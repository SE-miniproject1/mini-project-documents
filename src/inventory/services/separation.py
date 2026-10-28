"""Component separation (SRS REQ-15, BR-4, NFR-S1).

A tested whole blood unit is split into red cells, plasma and platelets. Each product
is a new unit with its own identifier and its own expiry date, counted from the original
collection date, and the whole blood unit is closed so it cannot be issued as well.
"""

from django.conf import settings
from django.db import transaction

from collection.models import TestName, TestResult
from inventory.models import BloodUnit, Component, InvalidTransitionError, Status
from inventory.services.id_generator import generate_unit_id
from inventory.services.shelf_life import expiry_date_for

CLOSE_REASON = "Separated into components"


class SeparationError(Exception):
    """The unit cannot be separated as asked. Nothing was changed."""


def separable_components():
    return list(settings.BBMS_SEPARATION)


@transaction.atomic
def separate_unit(unit, volumes, *, by=None, today=None):
    """Split `unit` into the components in `volumes` ({component: millilitres}).

    Returns the new child units. Raises `SeparationError` if the unit is not a released whole
    blood unit, if the volumes do not fit, or if any product would already be out of date.
    """
    from datetime import date

    today = today or date.today()
    locked = BloodUnit.objects.select_for_update().get(pk=unit.pk)
    unit.refresh_from_db()
    if locked.component_type != Component.WHOLE_BLOOD:
        raise SeparationError("Only a whole blood unit can be separated.")
    if locked.status != Status.AVAILABLE:
        raise SeparationError(
            f"The unit is {locked.status}. Only an Available unit can be separated."
        )
    if locked.expiry_date < today:
        raise SeparationError("The unit is past its expiry date.")
    # Defence in depth: an Available unit passed release, but check the panel again, since
    # the products will skip quarantine and rely on the parent's results.
    results = list(unit.tests.values_list("test_name", "result"))
    if {name for name, _ in results} != set(TestName.values) or any(
        result != TestResult.NON_REACTIVE for _, result in results
    ):
        raise SeparationError("The unit does not have a complete, non-reactive screening panel.")

    if not volumes:
        raise SeparationError("Choose at least one component.")
    allowed = settings.BBMS_SEPARATION
    for component, volume in volumes.items():
        if component not in allowed:
            raise SeparationError(
                f"{component} is not a component this unit can be separated into."
            )
        if volume <= 0:
            raise SeparationError(f"The volume for {component} must be more than zero.")
    if sum(volumes.values()) > unit.volume_ml:
        total = sum(volumes.values())
        raise SeparationError(
            f"The volumes add up to {total} ml, more than the unit's {unit.volume_ml} ml."
        )

    expired = [
        component
        for component in volumes
        if expiry_date_for(component, unit.collection_date) < today
    ]
    if expired:
        raise SeparationError(
            "Already past expiry when counted from collection: " + ", ".join(expired) + "."
        )

    children = []
    for component, volume in volumes.items():
        child = BloodUnit.objects.create(
            unit_id=generate_unit_id(),
            donor=unit.donor,
            parent_unit=unit,
            blood_group=unit.blood_group,
            component_type=component,
            volume_ml=volume,
            collection_date=unit.collection_date,
            expiry_date=expiry_date_for(component, unit.collection_date),
            bag_lot_number=unit.bag_lot_number,
            collection_site=unit.collection_site,
            storage_location=allowed[component]["storage"],
        )
        try:
            # Released on the parent's results, so the product skips quarantine.
            child.transition_to(Status.AVAILABLE, by=by, reason=f"Separated from {unit.unit_id}")
        except (
            InvalidTransitionError
        ) as problem:  # pragma: no cover - cannot happen from Quarantined
            raise SeparationError(str(problem)) from problem
        children.append(child)

    unit.transition_to(Status.DISCARDED, by=by, reason=CLOSE_REASON)
    return children
