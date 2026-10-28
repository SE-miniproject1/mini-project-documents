from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from accounts.permissions import STAFF_ROLES, role_required

from .models import BloodUnit
from .services.barcode import code128_svg


@role_required(*STAFF_ROLES)
def unit_label(request, unit_id):
    """A printable unit label (SRS HI-2). It carries the unit, never the donor."""
    unit = get_object_or_404(BloodUnit, unit_id=unit_id)
    return render(request, "inventory/label.html", {"unit": unit})


@role_required(*STAFF_ROLES)
def unit_barcode(request, unit_id):
    unit = get_object_or_404(BloodUnit, unit_id=unit_id)
    return HttpResponse(code128_svg(unit.unit_id), content_type="image/svg+xml")
