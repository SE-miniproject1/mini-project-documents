from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.permissions import STAFF_ROLES, role_required
from core.listing import apply_sort, paginate

from .forms import SeparationForm
from .models import BloodUnit, Component, Status
from .services.barcode import code128_svg
from .services.expiry import near_expiry_units
from .services.separation import SeparationError, separate_unit
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
    context.update(
        {
            "page": paginate(request, awaiting),
            "sort": sort,
            "whole_blood": BloodUnit.objects.issuable()
            .filter(component_type=Component.WHOLE_BLOOD)
            .order_by("expiry_date", "unit_id")[:25],
        }
    )
    return render(request, "inventory/console.html", context)


@role_required(*STAFF_ROLES)
def unit_detail(request, unit_id):
    """One unit: its facts, screening results, parent or products, and what staff can do."""
    unit = get_object_or_404(
        BloodUnit.objects.select_related("donor", "parent_unit"), unit_id=unit_id
    )
    return render(
        request,
        "inventory/unit_detail.html",
        {
            "unit": unit,
            "tests": unit.tests.order_by("test_name"),
            "children": unit.children.order_by("component_type"),
            "can_separate": unit.status == Status.AVAILABLE
            and unit.component_type == Component.WHOLE_BLOOD,
        },
    )


@role_required(*STAFF_ROLES)
def separate(request, unit_id):
    """Split a whole blood unit into red cells, plasma and platelets (UC7)."""
    unit = get_object_or_404(BloodUnit.objects.select_related("donor"), unit_id=unit_id)
    form = SeparationForm(request.POST or None, unit=unit)
    if request.method == "POST" and form.is_valid():
        try:
            children = separate_unit(unit, form.volumes(), by=request.user)
        except SeparationError as problem:
            form.add_error(None, str(problem))
        else:
            messages.success(
                request, f"{unit.unit_id} was separated into {len(children)} components."
            )
            return redirect("inventory:unit_detail", unit_id=unit.unit_id)
    return render(
        request,
        "inventory/separate.html",
        {
            "unit": unit,
            "form": form,
            "cancel_url": reverse("inventory:unit_detail", args=[unit.unit_id]),
        },
    )
