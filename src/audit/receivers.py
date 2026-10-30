"""Connects the system's events to the audit log."""

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from inventory.signals import unit_status_changed

from .models import Event
from .services import record_event


@receiver(unit_status_changed, dispatch_uid="audit_unit_status")
def record_unit_status(sender, unit, previous, new, by, reason, **kwargs):
    """Runs inside the transition's transaction. If this fails, the change is rolled back."""
    record_event(
        Event.UNIT_STATUS,
        actor=by,
        entity_type="BloodUnit",
        entity_id=unit.unit_id,
        previous=previous,
        new=new,
        reason=reason,
    )


@receiver(user_logged_in, dispatch_uid="audit_login")
def record_login(sender, request, user, **kwargs):
    record_event(Event.LOGIN_SUCCESS, actor=user, request=request)


@receiver(user_logged_out, dispatch_uid="audit_logout")
def record_logout(sender, request, user, **kwargs):
    if user is not None:
        record_event(Event.LOGOUT, actor=user, request=request)


@receiver(user_login_failed, dispatch_uid="audit_login_failed")
def record_login_failure(sender, credentials, request=None, **kwargs):
    # Only the user name is kept. The password in `credentials` is never read.
    record_event(
        Event.LOGIN_FAILURE, username=str(credentials.get("username", "")), request=request
    )
