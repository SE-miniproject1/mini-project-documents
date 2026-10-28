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


class TestName(models.TextChoices):
    # The mandatory screening panel (SRS REQ-12, BR-5).
    HIV = "HIV", "HIV"
    HBV = "HBV", "Hepatitis B"
    HCV = "HCV", "Hepatitis C"
    SYPHILIS = "Syphilis", "Syphilis"
    MALARIA = "Malaria", "Malaria"


class TestResult(models.TextChoices):
    REACTIVE = "Reactive", "Reactive"
    NON_REACTIVE = "Non-Reactive", "Non-Reactive"


class ScreeningTest(models.Model):
    """One infectious-disease test result for a unit (SRS REQ-12 to REQ-14, Appendix B.3).

    Results are recorded once and never edited. A wrongly entered Non-Reactive result
    would let an unsafe unit through, so a correction is a new decision by a person with
    authority, not a silent edit.
    """

    __test__ = False  # not a test class, despite the name

    unit = models.ForeignKey("inventory.BloodUnit", on_delete=models.PROTECT, related_name="tests")
    test_name = models.CharField(max_length=25, choices=TestName.choices)
    result = models.CharField(max_length=15, choices=TestResult.choices)
    tested_on = models.DateField()
    tested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["unit", "test_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["unit", "test_name"], name="one_result_per_test_per_unit"
            ),
        ]

    def __str__(self):
        return f"{self.unit.unit_id} {self.test_name}: {self.result}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("A recorded test result cannot be edited.")
        super().save(*args, **kwargs)
