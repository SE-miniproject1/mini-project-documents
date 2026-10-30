"""A donation event (SRS REQ-9)."""

from django.conf import settings
from django.db import models


class Donation(models.Model):
    donor = models.ForeignKey("donors.Donor", on_delete=models.PROTECT, related_name="donations")
    unit = models.OneToOneField(
        "inventory.BloodUnit", on_delete=models.PROTECT, related_name="donation"
    )
    collected_at = models.DateTimeField()
    volume_ml = models.PositiveIntegerField()
    bag_lot_number = models.CharField(max_length=20)
    # "Centre", or the camp identifier when collected at a camp (SRS REQ-36).
    collection_site = models.CharField(max_length=30, default="Centre")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-collected_at"]

    def __str__(self):
        return f"{self.unit.unit_id} from {self.donor.donor_id}"
