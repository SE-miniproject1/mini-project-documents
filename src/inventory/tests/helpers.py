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
    path = {
        Status.QUARANTINED: [],
        Status.AVAILABLE: [Status.AVAILABLE],
        Status.RESERVED: [Status.AVAILABLE, Status.RESERVED],
        Status.ISSUED: [Status.AVAILABLE, Status.RESERVED, Status.ISSUED],
        Status.EXPIRED: [Status.EXPIRED],
        Status.DISCARDED: [Status.DISCARDED],
    }[Status(status)]
    for step in path:
        unit.transition_to(step, reason=discard_reason or "test discard")
    return unit
