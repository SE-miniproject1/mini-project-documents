from django.db.models import Q
from django.shortcuts import render

from accounts.models import Role
from accounts.permissions import role_required
from core.listing import apply_sort, paginate

from .models import AuditEntry, Event


@role_required(Role.ADMIN)
def log(request):
    """The audit log, for administrators only (SRS REQ-23, NFR-SEC10)."""
    entries = AuditEntry.objects.select_related("actor")
    event = request.GET.get("event", "")
    if event in Event.values:
        entries = entries.filter(event=event)
    query = request.GET.get("q", "").strip()
    if query:
        entries = entries.filter(
            Q(actor_username__icontains=query)
            | Q(entity_id__icontains=query)
            | Q(reason__icontains=query)
        )
    entries, sort = apply_sort(
        request,
        entries,
        {
            "time": "occurred_at",
            "event": "event",
            "actor": "actor_username",
            "entity": "entity_id",
        },
        default="time",
    )
    if "sort" not in request.GET:
        entries = entries.reverse()  # newest first by default
    return render(
        request,
        "audit/log.html",
        {
            "page": paginate(request, entries),
            "sort": sort,
            "events": Event.choices,
            "event": event,
            "query": query,
        },
    )
