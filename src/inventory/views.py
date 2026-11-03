from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.permissions import STAFF_ROLES, role_required
from core import config
from core.listing import apply_sort, paginate

from .forms import DiscardForm, InventoryFilterForm, SeparationForm, TransferForm
from .models import BloodUnit, Component, Status
from .services.actions import ActionError, discard_unit, transfer_unit
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
    """Current stock, filters, and units waiting for test results."""
    near_expiry = near_expiry_units()
    context = {
        "grid": stock_grid(),
        "statuses": status_counts(),
        "as_of": timezone.localtime(),
        "near_expiry": near_expiry,
        "near_expiry_days": config.near_expiry_days(),
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
    filters = InventoryFilterForm(request.GET or None)
    filtered_units = BloodUnit.objects.select_related("donor")
    if filters.is_valid():
        data = filters.cleaned_data
        if data.get("blood_group"):
            filtered_units = filtered_units.filter(blood_group=data["blood_group"])
        if data.get("component_type"):
            filtered_units = filtered_units.filter(component_type=data["component_type"])
        if data.get("storage_location"):
            filtered_units = filtered_units.filter(
                storage_location__icontains=data["storage_location"]
            )
        if data.get("status"):
            filtered_units = filtered_units.filter(status=data["status"])
        if data.get("expiry_from"):
            filtered_units = filtered_units.filter(expiry_date__gte=data["expiry_from"])
        if data.get("expiry_to"):
            filtered_units = filtered_units.filter(expiry_date__lte=data["expiry_to"])
    filtered_units = filtered_units.order_by("expiry_date", "unit_id")
    context.update(
        {
            "page": paginate(request, awaiting),
            "sort": sort,
            "filters": filters,
            "filtered_units": paginate(request, filtered_units),
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


@role_required(*STAFF_ROLES)
def transfer(request, unit_id):
    unit = get_object_or_404(BloodUnit, unit_id=unit_id)
    form = TransferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            transfer_unit(unit, form.cleaned_data["destination"], by=request.user)
        except ActionError as problem:
            form.add_error("destination", str(problem))
        else:
            messages.success(
                request, f"{unit.unit_id} transferred to {form.cleaned_data['destination']}."
            )
            return redirect("inventory:unit_detail", unit_id=unit.unit_id)
    return render(
        request,
        "inventory/action_form.html",
        {"unit": unit, "form": form, "heading": "Transfer unit"},
    )


@role_required(*STAFF_ROLES)
def discard(request, unit_id):
    unit = get_object_or_404(BloodUnit, unit_id=unit_id)
    form = DiscardForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            discard_unit(unit, form.cleaned_data["reason"], by=request.user)
        except ActionError as problem:
            form.add_error(None, str(problem))
        else:
            messages.success(request, f"{unit.unit_id} was discarded.")
            return redirect("inventory:unit_detail", unit_id=unit.unit_id)
    return render(
        request,
        "inventory/action_form.html",
        {"unit": unit, "form": form, "heading": "Discard unit"},
    )
