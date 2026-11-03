"""Hospital availability search (SRS REQ-38, NFR-SEC7)."""

from datetime import date

from django.db.models import Count

from inventory.models import BloodUnit


def availability_search(blood_group=None, component_type=None, today=None):
    """Return available quantities by blood group and component only.

    No unit identifiers, donor identifiers or donor details are selected.
    """
    units = BloodUnit.objects.issuable(today or date.today())

    if blood_group:
        units = units.filter(blood_group=blood_group)

    if component_type:
        units = units.filter(component_type=component_type)

    return list(
        units.values("blood_group", "component_type")
        .annotate(quantity=Count("id"))
        .order_by("blood_group", "component_type")
    )
