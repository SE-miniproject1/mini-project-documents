"""Hospital-facing blood availability search."""

from django.shortcuts import render

from accounts.models import Role
from accounts.permissions import role_required
from bloodrequests.services import hospital_for
from donors.models import BloodGroup
from inventory.models import Component
from search.services import availability_search


@role_required(Role.HOSPITAL)
def availability(request):
    hospital = hospital_for(request.user)

    if hospital is None:
        return render(request, "requests/not_linked.html", status=403)

    blood_group = request.GET.get("blood_group", "").strip()
    component_type = request.GET.get("component_type", "").strip()

    valid_groups = BloodGroup.values
    valid_components = Component.values

    if blood_group not in valid_groups:
        blood_group = ""

    if component_type not in valid_components:
        component_type = ""

    results = availability_search(
        blood_group=blood_group or None,
        component_type=component_type or None,
    )

    return render(
        request,
        "search/availability.html",
        {
            "results": results,
            "blood_groups": BloodGroup.choices,
            "components": Component.choices,
            "selected_group": blood_group,
            "selected_component": component_type,
        },
    )
