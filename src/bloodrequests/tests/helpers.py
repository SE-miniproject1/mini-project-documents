from datetime import timedelta

from django.utils import timezone

from accounts.models import Role
from accounts.tests.helpers import make_hospital, make_user
from bloodrequests.models import BloodRequest, RequestStatus
from bloodrequests.services import generate_request_id


def make_hospital_user(username="hosp01", hospital=None, **extra):
    return make_user(username, Role.HOSPITAL, hospital=hospital or make_hospital(), **extra)


def make_request(user=None, **overrides):
    user = user or make_hospital_user()
    fields = {
        "request_id": generate_request_id(),
        "hospital": user.hospital,
        "requested_by": user,
        "blood_group": "A+",
        "component_type": "Whole Blood",
        "quantity_requested": 2,
        "urgency": "Routine",
        "required_by": timezone.now() + timedelta(days=1),
        "patient_reference": "BED-12",
        "status": RequestStatus.PENDING,
    }
    fields.update(overrides)
    return BloodRequest.objects.create(**fields)
