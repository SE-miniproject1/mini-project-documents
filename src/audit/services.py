from . import context
from .models import AuditEntry


def source_ip(request):
    if request is None:
        return None
    return request.META.get("REMOTE_ADDR") or None


def record_event(
    event,
    *,
    actor=None,
    username="",
    entity_type="",
    entity_id="",
    previous="",
    new="",
    reason="",
    request=None,
):
    """Add one entry. Never include a password, a token or medical detail in `reason`."""
    request = request or context.current_request()
    if actor is not None and not getattr(actor, "is_authenticated", True):
        actor = None
    return AuditEntry.objects.create(
        event=event,
        actor=actor,
        actor_username=(username or (actor.get_username() if actor else ""))[:150],
        source_ip=source_ip(request),
        entity_type=entity_type,
        entity_id=str(entity_id),
        previous_value=str(previous)[:60],
        new_value=str(new)[:60],
        reason=str(reason)[:200],
    )
