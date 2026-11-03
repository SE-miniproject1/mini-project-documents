from datetime import date, timedelta

from donors.tests.helpers import make_donor
from inventory.models import BloodUnit, Status
from inventory.services.id_generator import generate_unit_id


def make_unit(*, status=Status.QUARANTINED, donor=None, discard_reason="", **overrides):
    """A unit in any status, built the way the real flow would: Quarantined, then moved on.

    Statuses other than Quarantined are reached through the legitimate transitions so the
    helper never bypasses the rules it is used to test.
    """
    donor = donor or make_donor()
    fields = {
        "unit_id": generate_unit_id(),
        "donor": donor,
        "blood_group": donor.blood_group,
        "component_type": "Whole Blood",
        "volume_ml": 450,
        "collection_date": date.today() - timedelta(days=1),
        "expiry_date": date.today() + timedelta(days=34),
        "bag_lot_number": "BG-2026-0417",
    }
    fields.update(overrides)
    unit = BloodUnit.objects.create(**fields)
    return make_unit_move(unit, status, discard_reason)


def clear_screening(unit, result="Non-Reactive", *, skip=()):
    """Record a screening panel for `unit` the way the lab would (all five tests)."""
    from accounts.models import Role, User
    from accounts.tests.helpers import make_user
    from collection.models import ScreeningTest, TestName

    lab = User.objects.filter(username="lab01").first() or make_user("lab01", Role.STAFF)
    for name in TestName.values:
        if name not in skip:
            ScreeningTest.objects.create(
                unit=unit, test_name=name, result=result, tested_on=date.today(), tested_by=lab
            )
    return unit


def make_cleared_unit(status=Status.AVAILABLE, **kwargs):
    """A unit with a complete Non-Reactive panel, in any status."""
    unit = make_unit(status=Status.QUARANTINED, **kwargs)
    clear_screening(unit)
    return make_unit_move(unit, status, kwargs.get("discard_reason", ""))


def make_unit_move(unit, status, reason=""):
    """Move a Quarantined unit to `status` through the legitimate transitions."""
    path = {
        Status.QUARANTINED: [],
        Status.AVAILABLE: [Status.AVAILABLE],
        Status.RESERVED: [Status.AVAILABLE, Status.RESERVED],
        Status.ISSUED: [Status.AVAILABLE, Status.RESERVED, Status.ISSUED],
        Status.EXPIRED: [Status.EXPIRED],
        Status.DISCARDED: [Status.DISCARDED],
    }[Status(status)]
    for step in path:
        unit.transition_to(step, reason=reason or "test discard")
    return unit
