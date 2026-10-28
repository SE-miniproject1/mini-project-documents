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
