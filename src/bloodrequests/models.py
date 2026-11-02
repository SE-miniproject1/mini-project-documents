"""Hospital blood requests (SRS REQ-24 to REQ-31, Appendix B.4)."""

from django.conf import settings
from django.db import models
from django.db.models import Q


class Urgency(models.TextChoices):
    ROUTINE = "Routine", "Routine"
    URGENT = "Urgent", "Urgent"
    EMERGENCY = "Emergency", "Emergency"


class RequestStatus(models.TextChoices):
    PENDING = "Pending", "Pending"
    APPROVED = "Approved", "Approved"
    PARTIAL = "Partially Fulfilled", "Partially Fulfilled"
    FULFILLED = "Fulfilled", "Fulfilled"
    REJECTED = "Rejected", "Rejected"
    CANCELLED = "Cancelled", "Cancelled"


# Sorts Emergency first, then Urgent, then Routine (SRS REQ-26).
URGENCY_RANK = {Urgency.EMERGENCY: 0, Urgency.URGENT: 1, Urgency.ROUTINE: 2}


class BloodRequest(models.Model):
    request_id = models.CharField(max_length=11, unique=True, editable=False)
    hospital = models.ForeignKey(
        "accounts.Hospital", on_delete=models.PROTECT, related_name="blood_requests"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    blood_group = models.CharField(max_length=3)
    component_type = models.CharField(max_length=25)
    quantity_requested = models.PositiveSmallIntegerField()
    quantity_issued = models.PositiveSmallIntegerField(default=0)
    urgency = models.CharField(max_length=10, choices=Urgency.choices)
    required_by = models.DateTimeField()
    patient_reference = models.CharField(max_length=20)
    status = models.CharField(
        max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING
    )
    rejection_reason = models.CharField(max_length=100, blank=True)
    raised_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-raised_on"]
        indexes = [models.Index(fields=["status", "urgency", "required_by"], name="req_queue_idx")]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity_requested__gte=1), name="request_quantity_positive"
            ),
            models.CheckConstraint(
                condition=Q(quantity_issued__lte=models.F("quantity_requested")),
                name="request_issued_not_over_requested",
            ),
            models.CheckConstraint(
                condition=~Q(status="Rejected") | ~Q(rejection_reason=""),
                name="request_rejection_has_reason",
            ),
        ]

    def __str__(self):
        what = f"{self.blood_group} {self.component_type}"
        return f"{self.request_id} {self.quantity_requested} x {what}"

    @property
    def shortfall(self):
        return self.quantity_requested - self.quantity_issued

    @property
    def is_open(self):
        return self.status in (
            RequestStatus.PENDING,
            RequestStatus.APPROVED,
            RequestStatus.PARTIAL,
        )


class Allocation(models.Model):
    """One unit set aside for one request, then issued or released (SRS REQ-28, REQ-29).

    The row is the issue record: request, unit, issuing staff member, receiving hospital (via
    the request) and timestamp. A unit can have only one live (unreleased) allocation, which the
    database enforces, so two staff can never both claim it (SRS NFR-S3).
    """

    request = models.ForeignKey(BloodRequest, on_delete=models.PROTECT, related_name="allocations")
    unit = models.ForeignKey(
        "inventory.BloodUnit", on_delete=models.PROTECT, related_name="allocations"
    )
    allocated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    allocated_at = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    issued_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    release_reason = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["allocated_at", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["unit"],
                condition=Q(released_at__isnull=True),
                name="one_live_allocation_per_unit",
            ),
            models.CheckConstraint(
                condition=Q(issued_at__isnull=True) | Q(released_at__isnull=True),
                name="allocation_not_issued_and_released",
            ),
        ]

    def __str__(self):
        return f"{self.request.request_id} <- {self.unit.unit_id}"

    @property
    def state(self):
        if self.released_at:
            return "Released"
        return "Issued" if self.issued_at else "Reserved"
