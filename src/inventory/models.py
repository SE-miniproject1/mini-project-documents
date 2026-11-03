"""Blood unit and its status rules (SRS REQ-11, REQ-16, NFR-S1 to NFR-S4, NFR-S7).

A unit's status changes only through `transition_to`. That one path checks the move is
allowed, takes a row lock, writes the change and announces it in the same transaction,
so nothing can put an untested, expired or already-issued unit into circulation.
"""

from datetime import date

from django.db import models, transaction
from django.db.models import Q

from .signals import unit_status_changed


class Status(models.TextChoices):
    QUARANTINED = "Quarantined", "Quarantined"
    AVAILABLE = "Available", "Available"
    RESERVED = "Reserved", "Reserved"
    ISSUED = "Issued", "Issued"
    EXPIRED = "Expired", "Expired"
    DISCARDED = "Discarded", "Discarded"


class Component(models.TextChoices):
    WHOLE_BLOOD = "Whole Blood", "Whole Blood"
    PRBC = "PRBC", "Packed Red Blood Cells"
    FFP = "FFP", "Fresh Frozen Plasma"
    PLATELETS = "Platelets", "Platelet Concentrate"
    CRYO = "Cryoprecipitate", "Cryoprecipitate"


# The complete set of permitted moves. Anything not listed is refused (SRS NFR-S7).
ALLOWED_TRANSITIONS = {
    Status.QUARANTINED: {Status.AVAILABLE, Status.DISCARDED, Status.EXPIRED},
    Status.AVAILABLE: {Status.RESERVED, Status.EXPIRED, Status.DISCARDED},
    Status.RESERVED: {Status.ISSUED, Status.AVAILABLE, Status.EXPIRED, Status.DISCARDED},
    Status.EXPIRED: {Status.DISCARDED},
    Status.ISSUED: set(),  # an issued unit is final, it can never be discarded (REQ-22)
    Status.DISCARDED: set(),
}

QUARANTINE_LOCATION = "QUARANTINE"


class InvalidTransitionError(Exception):
    """The requested status change is not permitted."""


class UnitQuerySet(models.QuerySet):
    def issuable(self, today=None):
        """Units that may be offered, counted or allocated (SRS REQ-11, NFR-S2).

        Only Available units qualify, and one past its expiry date does not, even if the
        nightly job has not yet marked it Expired.
        """
        return self.filter(status=Status.AVAILABLE, expiry_date__gte=today or date.today())


class BloodUnit(models.Model):
    unit_id = models.CharField(max_length=12, unique=True, editable=False)
    donor = models.ForeignKey("donors.Donor", on_delete=models.PROTECT, related_name="units")
    parent_unit = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children"
    )
    blood_group = models.CharField(max_length=3)
    component_type = models.CharField(max_length=25, choices=Component.choices)
    volume_ml = models.PositiveIntegerField()
    collection_date = models.DateField()
    expiry_date = models.DateField()
    storage_location = models.CharField(max_length=30, default=QUARANTINE_LOCATION)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.QUARANTINED)
    bag_lot_number = models.CharField(max_length=20)
    collection_site = models.CharField(max_length=30, default="Centre")
    discard_reason = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UnitQuerySet.as_manager()

    class Meta:
        ordering = ["unit_id"]
        indexes = [
            # The stock grid and the availability search filter on these together.
            models.Index(
                fields=["status", "blood_group", "component_type"], name="unit_stock_idx"
            ),
            models.Index(fields=["status", "expiry_date"], name="unit_expiry_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(expiry_date__gte=models.F("collection_date")),
                name="unit_expiry_not_before_collection",
            ),
            # A discarded unit always says why (SRS REQ-22).
            models.CheckConstraint(
                condition=~Q(status="Discarded") | ~Q(discard_reason=""),
                name="unit_discard_has_reason",
            ),
            models.CheckConstraint(
                condition=Q(status__in=[s.value for s in Status]), name="unit_status_valid"
            ),
        ]

    def __str__(self):
        return f"{self.unit_id} {self.component_type} {self.blood_group} ({self.status})"

    @classmethod
    def from_db(cls, db, field_names, values):
        unit = super().from_db(db, field_names, values)
        unit._loaded = {
            "status": unit.__dict__.get("status"),
            "unit_id": unit.__dict__.get("unit_id"),
        }
        return unit

    def save(self, *args, **kwargs):
        loaded = getattr(self, "_loaded", None)
        if self._state.adding:
            # SRS REQ-11: every new unit starts in quarantine.
            if self.status != Status.QUARANTINED:
                raise InvalidTransitionError("A new unit must be created Quarantined.")
        elif loaded is not None:
            if self.unit_id != loaded["unit_id"]:
                raise ValueError("A unit identifier cannot be changed.")
            if self.status != loaded["status"] and not getattr(self, "_via_transition", False):
                raise InvalidTransitionError("Change a unit's status with transition_to().")
        super().save(*args, **kwargs)
        self._loaded = {"status": self.status, "unit_id": self.unit_id}

    def can_transition_to(self, new_status):
        return new_status in ALLOWED_TRANSITIONS[Status(self.status)]

    def transition_to(self, new_status, *, by=None, reason=""):
        """Move the unit to `new_status`, or raise `InvalidTransitionError`."""
        new_status = Status(new_status)
        with transaction.atomic():
            # Lock the row so two people acting on the same unit cannot both succeed (NFR-S4).
            current = BloodUnit.objects.select_for_update().get(pk=self.pk)
            if current.status != self.status:
                raise InvalidTransitionError(
                    f"The unit is now {current.status}; it changed since it was loaded."
                )
            if new_status not in ALLOWED_TRANSITIONS[Status(current.status)]:
                raise InvalidTransitionError(
                    f"A {current.status} unit cannot become {new_status}."
                )
            if new_status == Status.DISCARDED and not reason.strip():
                raise InvalidTransitionError("A reason is required to discard a unit.")

            previous = current.status
            self.status = new_status
            update_fields = ["status"]
            if new_status == Status.DISCARDED:
                self.discard_reason = reason.strip()[:60]
                update_fields.append("discard_reason")
            self._via_transition = True
            try:
                self.save(update_fields=update_fields)
            finally:
                self._via_transition = False
            unit_status_changed.send(
                sender=BloodUnit,
                unit=self,
                previous=previous,
                new=new_status,
                by=by,
                reason=reason,
            )
        return self
