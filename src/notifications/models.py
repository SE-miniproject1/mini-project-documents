"""The notification queue (SRS REQ-39 to REQ-41, SAD DD-6).

Each row is one message to one donor. Rows are written inside the transaction that decides
to notify, so a message exists exactly when that decision commits (NFR-P6). The dispatcher
sends them later, outside any user transaction (CI-6), and records how each one went.
"""

from django.db import models


class Kind(models.TextChoices):
    ELIGIBILITY = "Eligibility", "Eligibility reminder"
    CAMP_REMINDER = "Camp reminder", "Camp reminder"
    SHORTAGE_APPEAL = "Shortage appeal", "Shortage appeal"


class Channel(models.TextChoices):
    SMS = "SMS", "SMS"
    EMAIL = "Email", "Email"


class NotificationStatus(models.TextChoices):
    QUEUED = "Queued", "Queued"
    SENT = "Sent", "Sent"
    FAILED = "Failed", "Failed"


class Notification(models.Model):
    kind = models.CharField(max_length=20, choices=Kind.choices)
    donor = models.ForeignKey(
        "donors.Donor", on_delete=models.PROTECT, related_name="notifications"
    )
    # The address is copied at queue time, so the record shows where the message went.
    mobile_number = models.CharField(max_length=10, blank=True)
    email = models.EmailField(max_length=100, blank=True)
    subject = models.CharField(max_length=120)
    body = models.TextField()
    sms_body = models.CharField(max_length=160)
    # Set for messages that must go out at most once, such as one reminder per camp.
    dedup_key = models.CharField(max_length=80, unique=True, null=True, blank=True)

    status = models.CharField(
        max_length=10, choices=NotificationStatus.choices, default=NotificationStatus.QUEUED
    )
    channel = models.CharField(max_length=5, choices=Channel.choices, default=Channel.SMS)
    sent_via = models.CharField(max_length=5, choices=Channel.choices, blank=True)
    sms_attempts = models.PositiveSmallIntegerField(default=0)
    email_attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField()
    last_error = models.CharField(max_length=255, blank=True)
    gateway_status = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [
            models.Index(fields=["status", "next_attempt_at"], name="notification_due"),
            models.Index(fields=["donor", "kind", "created_at"], name="notification_by_donor"),
        ]

    def __str__(self):
        return f"{self.kind} to {self.donor_id} ({self.status})"
