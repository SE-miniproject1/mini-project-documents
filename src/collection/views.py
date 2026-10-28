import logging

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.permissions import STAFF_ROLES, role_required
from donors.models import Donor
from inventory.models import BloodUnit

from .forms import CollectionForm
from .services.collect import record_collection
from .services.guard import CollectionBlockedError, ensure_can_collect

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
