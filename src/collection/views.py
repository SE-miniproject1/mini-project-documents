import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.permissions import STAFF_ROLES, role_required
from donors.models import Donor
from inventory.models import BloodUnit

from .forms import CollectionForm, ScreeningResultsForm
from .models import TestName
from .services.collect import record_collection
from .services.guard import CollectionBlockedError, ensure_can_collect
from .services.screening import (
    PANEL,
    ScreeningError,
    missing_tests,
    record_results,
    release_unit,
)

logger = logging.getLogger(__name__)


@role_required(*STAFF_ROLES)
def new_collection(request, donor_id):
    """Record a donation (UC5). The guard runs first and its reason is shown if it refuses."""
    donor = get_object_or_404(Donor, donor_id=donor_id, is_active=True)
    try:
        ensure_can_collect(donor)
    except CollectionBlockedError as blocked:
        return render(request, "collection/blocked.html", {"donor": donor, "blocked": blocked})

    form = CollectionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            _, unit = record_collection(donor, recorded_by=request.user, **form.cleaned_data)
        except CollectionBlockedError as blocked:
            # Someone else recorded a donation for this donor a moment earlier.
            return render(request, "collection/blocked.html", {"donor": donor, "blocked": blocked})
        logger.info(
            "donation recorded unit_id=%s donor_id=%s user_id=%s",
            unit.unit_id,
            donor.donor_id,
            request.user.pk,
        )
        return redirect("collection:confirmation", unit_id=unit.unit_id)
    return render(
        request,
        "collection/new.html",
        {"donor": donor, "form": form, "cancel_url": reverse("donors:search")},
    )


@role_required(*STAFF_ROLES)
def confirmation(request, unit_id):
    unit = get_object_or_404(BloodUnit, unit_id=unit_id)
    return render(request, "collection/confirmation.html", {"unit": unit})


@role_required(*STAFF_ROLES)
def results(request, unit_id):
    """Enter screening results and release a unit to inventory (UC6)."""
    unit = get_object_or_404(BloodUnit.objects.select_related("donor"), unit_id=unit_id)
    recorded = {test.test_name: test for test in unit.tests.all()}
    pending = [name for name in PANEL if name not in recorded]
    editable = unit.status == "Quarantined"
    form = ScreeningResultsForm(request.POST or None, pending=pending if editable else [])

    if request.method == "POST" and editable and form.is_valid():
        action = request.POST.get("action", "save")
        try:
            entered = form.entered()
            if entered:
                record_results(
                    unit, entered, by=request.user, tested_on=form.cleaned_data["tested_on"]
                )
                unit.refresh_from_db()
            if unit.status == "Discarded":
                messages.error(
                    request,
                    "A result was Reactive. The unit is discarded and can never be issued.",
                )
            elif action == "release":
                outcome = release_unit(unit, by=request.user)
                (messages.success if outcome.released else messages.error)(
                    request, outcome.message
                )
            else:
                messages.success(request, "Results saved.")
        except ScreeningError as problem:
            messages.error(request, str(problem))
        logger.info(
            "screening results handled unit_id=%s user_id=%s", unit.unit_id, request.user.pk
        )
        return redirect("collection:results", unit_id=unit.unit_id)

    unit.refresh_from_db()
    rows = [
        {"name": name, "label": TestName(name).label, "test": recorded.get(name)} for name in PANEL
    ]
    return render(
        request,
        "collection/results.html",
        {
            "unit": unit,
            "form": form,
            "rows": rows,
            "editable": editable,
            "missing": missing_tests(unit),
        },
    )
