from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Role
from accounts.permissions import STAFF_ROLES, role_required
from core.listing import paginate
from donors.models import Donor

from .forms import CampForm
from .models import Camp, CampStatus
from .services import CampError, attainment, close_camp, create_camp, enrol_donor, upcoming_camps


@role_required(Role.DONOR)
def camp_list(request):
    """Upcoming camps for a donor, with an enrol button each (SRS REQ-34)."""
    donor = get_object_or_404(Donor, user=request.user, is_active=True)
    enrolled = set(donor.enrolments.values_list("camp_id", flat=True))
    return render(
        request,
        "camps/list.html",
        {"camps": upcoming_camps(), "enrolled": enrolled},
    )


@role_required(Role.DONOR)
def enrol(request, camp_id):
    camp = get_object_or_404(Camp, camp_id=camp_id)
    donor = get_object_or_404(Donor, user=request.user, is_active=True)
    if request.method == "POST":
        try:
            enrol_donor(camp, donor)
        except CampError as problem:
            messages.error(request, str(problem))
        else:
            messages.success(request, f"You are enrolled in {camp.name}.")
    return redirect("camps:list")


@role_required(*STAFF_ROLES)
def manage(request):
    show = request.GET.get("show", "open")
    camps = Camp.objects.all()
    if show == "open":
        camps = camps.filter(status=CampStatus.SCHEDULED)
    return render(request, "camps/manage.html", {"page": paginate(request, camps), "show": show})


@role_required(*STAFF_ROLES)
def new(request):
    form = CampForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            camp = create_camp(request.user, **form.cleaned_data)
        except CampError as problem:
            form.add_error(problem.field if problem.field in form.fields else None, str(problem))
        else:
            messages.success(request, f"{camp.name} was scheduled as {camp.camp_id}.")
            return redirect("camps:detail", camp_id=camp.camp_id)
    return render(request, "camps/new.html", {"form": form})


@role_required(*STAFF_ROLES)
def detail(request, camp_id):
    camp = get_object_or_404(Camp, camp_id=camp_id)
    return render(
        request,
        "camps/detail.html",
        {
            "camp": camp,
            "enrolments": camp.enrolments.select_related("donor"),
            "attainment": attainment(camp),
        },
    )


@role_required(*STAFF_ROLES)
def close(request, camp_id):
    camp = get_object_or_404(Camp, camp_id=camp_id)
    if request.method == "POST":
        try:
            camp = close_camp(camp, by=request.user)
        except CampError as problem:
            messages.error(request, str(problem))
        else:
            messages.success(
                request,
                f"{camp.name} is completed: {camp.units_collected} of "
                f"{camp.target_units} units collected.",
            )
    return redirect("camps:detail", camp_id=camp_id)
