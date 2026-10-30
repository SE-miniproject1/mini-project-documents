from django.dispatch import receiver

from inventory.models import Status
from inventory.signals import unit_status_changed

from .allocation import release_for_lost_unit


@receiver(unit_status_changed, dispatch_uid="requests_release_lost_unit")
def release_claim_when_reserved_unit_is_lost(sender, unit, previous, new, by, **kwargs):
    """Runs inside the transition's transaction (SRS REQ-19, D-42)."""
    if previous == Status.RESERVED and new in (Status.EXPIRED, Status.DISCARDED):
        release_for_lost_unit(unit, by=by, reason=f"Unit became {new}")
