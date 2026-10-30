from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from accounts.permissions import STAFF_ROLES, role_required
from core.listing import apply_sort, paginate

from .models import BloodUnit, Status
from .services.barcode import code128_svg
from .services.expiry import near_expiry_units
from .services.stock import status_counts, stock_grid


@role_required(*STAFF_ROLES)
def unit_label(request, unit_id):
    """A printable unit label (SRS HI-2). It carries the unit, never the donor."""
    unit = get_object_or_404(BloodUnit, unit_id=unit_id)
    return render(request, "inventory/label.html", {"unit": unit})


@role_required(*STAFF_ROLES)
def unit_barcode(request, unit_id):
    unit = get_object_or_404(BloodUnit, unit_id=unit_id)
    return HttpResponse(code128_svg(unit.unit_id), content_type="image/svg+xml")


@role_required(*STAFF_ROLES)
def console(request):
    """Current stock and the units waiting for test results (UC8, SRS REQ-17).

    `?partial=1` returns only the live panel, which the page fetches every few seconds so
    one person's change reaches everyone else well inside the 5 seconds NFR-P5 allows.
    """
    near_expiry = near_expiry_units()
    context = {
        "grid": stock_grid(),
        "statuses": status_counts(),
        "as_of": timezone.localtime(),
        "near_expiry": near_expiry,
        "near_expiry_days": settings.BBMS_NEAR_EXPIRY_DAYS,
    }
    if request.GET.get("partial"):
        return render(request, "inventory/_live.html", context)
    awaiting, sort = apply_sort(
        request,
        BloodUnit.objects.filter(status=Status.QUARANTINED),
        {
            "unit": "unit_id",
            "group": "blood_group",
            "component": "component_type",
            "collected": "collection_date",
        },
        default="collected",
    )
    context.update({"page": paginate(request, awaiting), "sort": sort})
    return render(request, "inventory/console.html", context)
