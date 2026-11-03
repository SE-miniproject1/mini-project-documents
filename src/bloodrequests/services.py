"""Raising a request (SRS REQ-24, REQ-25, BR-7)."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from accounts.models import Role, User
from audit.models import Event
from audit.services import record_event
from core.models import IdSequence
from donors.models import BloodGroup
from inventory.models import BloodUnit, Component

from .models import BloodRequest, RequestStatus, Urgency

logger = logging.getLogger(__name__)

SEQUENCE = "request"
FIRST_NUMBER = 10000001
MAX_QUANTITY = 50


class RequestError(Exception):
    """A request cannot be raised. `field` names the field in error where there is one."""

    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field


def generate_request_id():
    return f"REQ{IdSequence.next_value(SEQUENCE, FIRST_NUMBER)}"


def hospital_for(user):
    """The active hospital a user may raise requests for, or None (SRS BR-7)."""
    hospital = getattr(user, "hospital", None)
    if user.role == Role.HOSPITAL and hospital is not None and hospital.is_active:
        return hospital
    return None


def available_count(blood_group, component_type, today=None):
    """How many units could be allocated now, shown so a hospital sees the stock position."""
    return (
        BloodUnit.objects.issuable(today)
        .filter(blood_group=blood_group, component_type=component_type)
        .count()
    )


def validate_request(
    *, blood_group, component_type, quantity, urgency, required_by, patient_reference, now=None
):
    now = now or timezone.now()
    if blood_group not in BloodGroup.values:
        raise RequestError("Choose a blood group.", "blood_group")
    if component_type not in Component.values:
        raise RequestError("Choose a component.", "component_type")
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
        raise RequestError("Quantity must be a whole number of at least 1.", "quantity")
    if quantity > MAX_QUANTITY:
        raise RequestError(f"Quantity cannot be more than {MAX_QUANTITY} units.", "quantity")
    if urgency not in Urgency.values:
        raise RequestError("Choose Routine, Urgent or Emergency.", "urgency")
    if required_by is None or required_by <= now:
        raise RequestError("Required-by date and time must be in the future.", "required_by")
    if not patient_reference:
        raise RequestError("Enter the patient reference code.", "patient_reference")


def create_request(
    user,
    *,
    blood_group,
    component_type,
    quantity,
    urgency,
    required_by,
    patient_reference,
    now=None,
):
    hospital = hospital_for(user)
    if hospital is None:
        raise RequestError("Your account is not linked to an active registered hospital.")
    validate_request(
        blood_group=blood_group,
        component_type=component_type,
        quantity=quantity,
        urgency=urgency,
        required_by=required_by,
        patient_reference=patient_reference,
        now=now,
    )
    request = BloodRequest.objects.create(
        request_id=generate_request_id(),
        hospital=hospital,
        requested_by=user,
        blood_group=blood_group,
        component_type=component_type,
        quantity_requested=quantity,
        urgency=urgency,
        required_by=required_by,
        patient_reference=patient_reference,
    )
    record_event(
        Event.REQUEST_STATUS,
        actor=user,
        entity_type="Request",
        entity_id=request.request_id,
        new=RequestStatus.PENDING,
        reason=f"{quantity} x {blood_group} {component_type}, {urgency}",
    )
    notify_staff_of_new_request(request)
    return request


def notify_staff_of_new_request(request):
    """Tell staff a request is waiting. A mail failure never loses the request."""
    recipients = list(
        User.objects.filter(role=Role.STAFF, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    if not recipients:
        return False
    try:
        send_mail(
            f"[{request.urgency}] New blood request {request.request_id}",
            f"{request.hospital.name} requests {request.quantity_requested} unit(s) of "
            f"{request.blood_group} {request.component_type}, needed by "
            f"{timezone.localtime(request.required_by):%d-%m-%Y %H:%M}.\n"
            "Open the request queue to review it.\n",
            settings.DEFAULT_FROM_EMAIL,
            recipients,
        )
    except Exception:  # noqa: BLE001
        logger.exception("new-request notification failed for %s", request.request_id)
        return False
    return True
