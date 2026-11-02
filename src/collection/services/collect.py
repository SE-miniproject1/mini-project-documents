"""Recording a donation (SRS REQ-9, REQ-10, REQ-11)."""

from django.db import transaction
from django.utils import timezone

from collection.models import Donation
from collection.services.guard import ensure_can_collect
from donors.models import Donor
from donors.services.eligibility import record_donation
from inventory.models import BloodUnit, Component, Status
from inventory.services.id_generator import generate_unit_id
from inventory.services.shelf_life import expiry_date_for


@transaction.atomic
def record_collection(
    donor, *, volume_ml, bag_lot_number, collection_site, recorded_by, collected_at=None
):
    """Take a donation from an eligible donor and create its Quarantined unit.

    The donor's row is locked and the guard is checked inside the transaction, so two
    people cannot both bleed the same donor, and a blocked donor leaves nothing behind.
    Raises `CollectionBlockedError` if the donor cannot donate.
    """
    donor = Donor.objects.select_for_update().get(pk=donor.pk)
    collected_at = collected_at or timezone.now()
    collected_on = timezone.localtime(collected_at).date()
    ensure_can_collect(donor, collected_on)

    unit = BloodUnit.objects.create(
        unit_id=generate_unit_id(),
        donor=donor,
        blood_group=donor.blood_group,
        component_type=Component.WHOLE_BLOOD,
        volume_ml=volume_ml,
        collection_date=collected_on,
        expiry_date=expiry_date_for(Component.WHOLE_BLOOD, collected_on),
        bag_lot_number=bag_lot_number,
        collection_site=collection_site,
        status=Status.QUARANTINED,
    )
    donation = Donation.objects.create(
        donor=donor,
        unit=unit,
        collected_at=collected_at,
        volume_ml=volume_ml,
        bag_lot_number=bag_lot_number,
        collection_site=collection_site,
        recorded_by=recorded_by,
    )
    record_donation(donor, collected_on)
    donor.save(
        update_fields=[
            "last_donation_date",
            "next_eligible_date",
            "eligibility_status",
            "deferral_reason",
            "deferral_review_date",
        ]
    )
    return donation, unit
