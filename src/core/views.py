from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect, render

from accounts.models import Role
from accounts.permissions import role_required
from bloodrequests.services import hospital_for
from donors.models import BloodGroup
from inventory.models import BloodUnit, Component

from . import config
from .forms import ConfigForm
from .help_text import GENERAL, help_for


@login_not_required
def health(request):
    """Liveness probe for the reverse proxy and for monitoring (SAD section 4.4)."""
    return JsonResponse({"status": "ok"})


def home(request):
    return render(request, "core/home.html")


def help_page(request):
    """Help for the screen the user came from, passed as ?topic=<url name>."""
    topic = request.GET.get("topic", "")
    return render(
        request, "core/help.html", {"topic_text": help_for(topic), "general_text": GENERAL}
    )


@role_required(Role.ADMIN)
def settings_page(request):
    """Change eligibility limits, shelf lives, the near-expiry window and stock thresholds."""
    form = ConfigForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        changed = config.save(form.values(), by=request.user)
        messages.success(
            request,
            f"{len(changed)} setting{'s' if len(changed) != 1 else ''} changed."
            if changed
            else "No settings were changed.",
        )
        return redirect("config:settings")
    return render(request, "core/settings.html", {"form": form, "sections": form.sections()})


@role_required(Role.HOSPITAL)
def availability_search(request):
    """Return aggregate stock counts only; never expose units or donor records (REQ-38)."""
    if hospital_for(request.user) is None:
        return render(request, "requests/not_linked.html", status=403)

    group = request.GET.get("group", "").strip()
    component = request.GET.get("component", "").strip()
    valid_groups = {value for value, _ in BloodGroup.choices}
    valid_components = {value for value, _ in Component.choices}
    if group and group not in valid_groups:
        group = ""
    if component and component not in valid_components:
        component = ""

    units = BloodUnit.objects.issuable()
    if group:
        units = units.filter(blood_group=group)
    if component:
        units = units.filter(component_type=component)

    # Aggregate in the database. Only these three scalar fields reach the template.
    counts = list(
        units.values("blood_group", "component_type")
        .annotate(available_count=Count("pk"))
        .order_by("blood_group", "component_type")
    )
    return render(
        request,
        "core/availability.html",
        {
            "counts": counts,
            "selected_group": group,
            "selected_component": component,
            "groups": BloodGroup.choices,
            "components": Component.choices,
        },
    )
