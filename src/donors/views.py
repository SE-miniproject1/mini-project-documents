import logging
from datetime import date

from django.contrib.auth.decorators import login_not_required
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.models import Role
from accounts.permissions import STAFF_ROLES, role_required
from collection.services.guard import collection_status
from core.listing import apply_sort, paginate

from .forms import DonorRegistrationForm, ScreeningForm
from .models import Donor, DonorScreening, Eligibility
from .services.eligibility import apply_screening

logger = logging.getLogger(__name__)

SESSION_KEY = "registered_donor_id"


@login_not_required
def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = DonorRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            donor = form.save()
        except IntegrityError:
            # Another request registered the same mobile number or email a moment earlier.
            form.add_error(None, "These details could not be saved. Check them and try again.")
        else:
            request.session[SESSION_KEY] = donor.donor_id
            return redirect("donors:registered")
    return render(request, "donors/register.html", {"form": form})


@login_not_required
def registered(request):
    """Confirmation page. The identifier travels in the session, not in the URL."""
    donor_id = request.session.pop(SESSION_KEY, None)
    if not donor_id:
        return redirect("accounts:login")
    return render(request, "donors/registered.html", {"donor_id": donor_id})


@role_required(*STAFF_ROLES)
def search(request):
    """Find a donor by ID, mobile number or name (UC4)."""
    query = request.GET.get("q", "").strip()
    donors = Donor.objects.filter(is_active=True)
    if query:
        donors = donors.filter(
            Q(donor_id__icontains=query)
            | Q(mobile_number__contains=query)
            | Q(full_name__icontains=query)
        )
    donors, sort = apply_sort(
        request,
        donors,
        {
            "id": "donor_id",
            "name": "full_name",
            "group": "blood_group",
            "status": "eligibility_status",
        },
        default="id",
    )
    page = paginate(request, donors)
    # Staff see, beside each donor, whether collection can start and why not (IT-03).
    for donor in page:
        donor.can_collect, donor.collect_note = collection_status(donor)
    return render(request, "donors/search.html", {"page": page, "query": query, "sort": sort})


@role_required(*STAFF_ROLES)
def screen(request, donor_id):
    donor = get_object_or_404(Donor, donor_id=donor_id, is_active=True)
    form = ScreeningForm(request.POST or None, initial={"weight_kg": donor.weight_kg})
    if request.method == "POST" and form.is_valid():
        screening, result = apply_screening(donor, screened_by=request.user, **form.cleaned_data)
        logger.info(
            "screening recorded donor_id=%s outcome=%s user_id=%s",
            donor.donor_id,
            result.status,
            request.user.pk,
        )
        return redirect("donors:screening_result", pk=screening.pk)
    return render(
        request,
        "donors/screen.html",
        {"donor": donor, "form": form, "cancel_url": reverse("donors:search")},
    )


@role_required(*STAFF_ROLES)
def screening_result(request, pk):
    screening = get_object_or_404(DonorScreening.objects.select_related("donor"), pk=pk)
    return render(
        request,
        "donors/screening_result.html",
        {
            "screening": screening,
            "donor": screening.donor,
            "reasons": [r for r in screening.reasons.split("\n") if r],
        },
    )


@role_required(Role.DONOR)
def dashboard(request):
    """A donor's own eligibility, next eligible date and days remaining (UC2, REQ-8)."""
    donor = get_object_or_404(Donor, user=request.user, is_active=True)
    today = date.today()
    days_remaining = None
    if donor.next_eligible_date and donor.next_eligible_date > today:
        days_remaining = (donor.next_eligible_date - today).days
    return render(
        request,
        "donors/dashboard.html",
        {
            "donor": donor,
            "eligible": donor.eligibility_status == Eligibility.ELIGIBLE,
            "days_remaining": days_remaining,
        },
    )
