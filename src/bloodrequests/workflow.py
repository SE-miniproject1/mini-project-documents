"""Staff review of requests (SRS REQ-26, REQ-27)."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When

from audit.models import Event
from audit.services import record_event

from .models import URGENCY_RANK, BloodRequest, RequestStatus

logger = logging.getLogger(__name__)

OPEN_STATUSES = (RequestStatus.PENDING, RequestStatus.APPROVED, RequestStatus.PARTIAL)


class WorkflowError(Exception):
    """The action is not allowed in the request's current state. Nothing was changed."""


def queue(statuses=OPEN_STATUSES):
    """Emergency first, then Urgent, then Routine; within each, earliest required-by first."""
    rank = Case(
        *[When(urgency=urgency, then=Value(r)) for urgency, r in URGENCY_RANK.items()],
        default=Value(9),
        output_field=IntegerField(),
    )
    return (
        BloodRequest.objects.filter(status__in=statuses)
        .select_related("hospital")
        .annotate(urgency_rank=rank)
        .order_by("urgency_rank", "required_by", "request_id")
    )


def _lock(request, expected):
    current = BloodRequest.objects.select_for_update().get(pk=request.pk)
    if current.status not in expected:
        raise WorkflowError(
            f"Request {current.request_id} is {current.status}; this action needs "
            + " or ".join(expected)
            + "."
        )
    return current


def _audit(request, previous, new, by, reason=""):
    record_event(
        Event.REQUEST_STATUS,
        actor=by,
        entity_type="Request",
        entity_id=request.request_id,
        previous=previous,
        new=new,
        reason=reason,
    )


@transaction.atomic
def approve_request(request, *, by):
    current = _lock(request, (RequestStatus.PENDING,))
    previous = current.status
    current.status = RequestStatus.APPROVED
    current.save(update_fields=["status", "updated_on"])
    _audit(current, previous, current.status, by)
    transaction.on_commit(
        lambda: notify_hospital(current, f"Request {current.request_id} was approved.")
    )
    return current


@transaction.atomic
def reject_request(request, *, by, reason):
    if reason not in settings.BBMS_REJECTION_REASONS:
        raise WorkflowError("Choose a rejection reason from the list.")
    current = _lock(request, (RequestStatus.PENDING,))
    previous = current.status
    current.status = RequestStatus.REJECTED
    current.rejection_reason = reason
    current.save(update_fields=["status", "rejection_reason", "updated_on"])
    _audit(current, previous, current.status, by, reason)
    transaction.on_commit(
        lambda: notify_hospital(
            current, f"Request {current.request_id} was rejected.\nReason: {reason}"
        )
    )
    return current


def notify_hospital(request, text):
    """Email the person who raised the request. A mail failure never undoes the decision."""
    address = request.requested_by.email
    if not address:
        return False
    try:
        send_mail(
            f"Blood request {request.request_id}: {request.status}",
            text + "\n",
            settings.DEFAULT_FROM_EMAIL,
            [address],
        )
    except Exception:  # noqa: BLE001
        logger.exception("hospital notification failed for %s", request.request_id)
        return False
    return True
