"""Donation camps and donor enrolment (SRS REQ-32 to REQ-37, Appendix B.6)."""

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class CampStatus(models.TextChoices):
    SCHEDULED = "Scheduled", "Scheduled"
    COMPLETED = "Completed", "Completed"
    CANCELLED = "Cancelled", "Cancelled"


class Camp(models.Model):
    camp_id = models.CharField(max_length=10, unique=True, editable=False)
    name = models.CharField(max_length=80)
    venue_address = models.CharField(max_length=150)
    camp_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    organiser_name = models.CharField(max_length=60)
    organiser_contact = models.CharField(max_length=10)
    target_units = models.PositiveSmallIntegerField()
    units_collected = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=15, choices=CampStatus.choices, default=CampStatus.SCHEDULED
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["camp_date", "start_time", "camp_id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")), name="camp_end_after_start"
            ),
            models.CheckConstraint(condition=Q(target_units__gte=1), name="camp_target_positive"),
        ]

    def __str__(self):
        return f"{self.camp_id} {self.name} ({self.camp_date:%d-%m-%Y})"


class Enrolment(models.Model):
    camp = models.ForeignKey(Camp, on_delete=models.PROTECT, related_name="enrolments")
    donor = models.ForeignKey("donors.Donor", on_delete=models.PROTECT, related_name="enrolments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["enrolled_at", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["camp", "donor"], name="one_enrolment_per_donor_camp"),
        ]
