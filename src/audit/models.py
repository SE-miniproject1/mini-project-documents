"""The audit log (SRS REQ-23, NFR-SEC10, SEC-OBJ-2).

Every unit status change, sign-in, sign-out, failed sign-in, lockout, authorisation
failure and configuration change leaves one entry saying who, when, from where, and
what changed. Entries can be added and read. Nothing in the application can edit or
delete one, which is what gives the log its value as evidence.
"""

from django.conf import settings
from django.db import models


class AuditImmutableError(Exception):
    """An attempt to change or remove an audit entry."""


class Event(models.TextChoices):
    UNIT_STATUS = "unit_status", "Unit status change"
    LOGIN_SUCCESS = "login_success", "Sign-in"
    LOGIN_FAILURE = "login_failure", "Failed sign-in"
    LOGOUT = "logout", "Sign-out"
    LOCKOUT = "lockout", "Account locked"
    AUTHZ_FAILURE = "authz_failure", "Authorisation failure"
    CONFIG_CHANGE = "config_change", "Configuration change"
    REQUEST_STATUS = "request_status", "Blood request status change"
    ALLOCATION = "allocation", "Unit allocation or issue"


class AuditQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise AuditImmutableError("Audit entries cannot be updated.")

    def delete(self):
        raise AuditImmutableError("Audit entries cannot be deleted.")


class AuditEntry(models.Model):
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    event = models.CharField(max_length=20, choices=Event.choices, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    # The name as typed, so a failed sign-in for an unknown user is still recorded.
    actor_username = models.CharField(max_length=150, blank=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    entity_type = models.CharField(max_length=30, blank=True)
    entity_id = models.CharField(max_length=40, blank=True)
    previous_value = models.CharField(max_length=60, blank=True)
    new_value = models.CharField(max_length=60, blank=True)
    reason = models.CharField(max_length=200, blank=True)

    objects = AuditQuerySet.as_manager()

    class Meta:
        ordering = ["-occurred_at", "-pk"]
        verbose_name_plural = "audit entries"

    def __str__(self):
        when = f"{self.occurred_at:%Y-%m-%d %H:%M:%S}"
        return f"{when} {self.event} {self.entity_type} {self.entity_id}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AuditImmutableError("Audit entries cannot be edited.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AuditImmutableError("Audit entries cannot be deleted.")
