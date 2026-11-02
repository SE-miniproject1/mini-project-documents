from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import Role
from accounts.permissions import STAFF_ROLES, role_required
from core.listing import apply_sort, paginate

from .allocation import (
    ALLOCATABLE,
    CANCELLABLE,
    allocate_units,
    cancel_request,
    candidate_units,
    issue_reserved,
    release_allocation,
)
from .forms import RejectForm, RequestForm
from .models import Allocation, BloodRequest, RequestStatus
from .services import RequestError, available_count, create_request, hospital_for
from .workflow import OPEN_STATUSES, WorkflowError, approve_request, queue, reject_request


@role_required(Role.HOSPITAL)
def new_request(request):
    if hospital_for(request.user) is None:
        return render(request, "requests/not_linked.html", status=403)
    form = RequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            blood_request = create_request(
                request.user,
                blood_group=data["blood_group"],
                component_type=data["component_type"],
                quantity=data["quantity"],
                urgency=data["urgency"],
                required_by=data["required_by"],
                patient_reference=data["patient_reference"],
            )
        except RequestError as problem:
            form.add_error(problem.field if problem.field in form.fields else None, str(problem))
        else:
            available = available_count(blood_request.blood_group, blood_request.component_type)
            if available < blood_request.quantity_requested:
                messages.warning(
                    request,
                    f"Request {blood_request.request_id} was raised, but only {available} "
                    f"unit(s) of {blood_request.blood_group} {blood_request.component_type} "
                    "are available now. Staff may fulfil it in part.",
                )
            else:
                messages.success(request, f"Request {blood_request.request_id} was raised.")
            return redirect("requests:detail", request_id=blood_request.request_id)
    return render(request, "requests/new.html", {"form": form})


@role_required(Role.HOSPITAL)
def tracker(request):
    hospital = hospital_for(request.user)
    if hospital is None:
        return render(request, "requests/not_linked.html", status=403)
    requests_, sort = apply_sort(
        request,
        BloodRequest.objects.filter(hospital=hospital),
        {
            "id": "request_id",
            "raised": "raised_on",
            "required": "required_by",
            "status": "status",
            "urgency": "urgency",
        },
        "raised",
    )
    if "sort" not in request.GET:
        requests_ = requests_.reverse()
    return render(
        request, "requests/tracker.html", {"page": paginate(request, requests_), "sort": sort}
    )


@role_required(Role.HOSPITAL, *STAFF_ROLES)
def detail(request, request_id):
    blood_request = get_object_or_404(
        BloodRequest.objects.select_related("hospital"), request_id=request_id
    )
    if request.user.role == Role.HOSPITAL:
        hospital = hospital_for(request.user)
        # Another hospital's request is reported as missing, never as forbidden (NFR-SEC6).
        if hospital is None or blood_request.hospital_id != hospital.pk:
            raise Http404
    return render(
        request,
        "requests/detail.html",
        {
            "req": blood_request,
            "available": available_count(blood_request.blood_group, blood_request.component_type),
            "is_staff": request.user.role == Role.STAFF,
            "reject_form": RejectForm(),
            "allocations": blood_request.allocations.select_related("unit").order_by("pk"),
            "can_allocate": request.user.role == Role.STAFF
            and blood_request.status in ALLOCATABLE,
            "candidates": candidate_units(blood_request)[:50]
            if blood_request.status in ALLOCATABLE
            else [],
            "has_reserved": blood_request.allocations.filter(
                released_at__isnull=True, issued_at__isnull=True
            ).exists(),
            "can_cancel": request.user.role == Role.HOSPITAL
            and blood_request.status in CANCELLABLE
            and not blood_request.quantity_issued,
        },
    )


@role_required(Role.STAFF)
def staff_queue(request):
    """Open requests, Emergency first (REQ-26)."""
    show = request.GET.get("show", "open")
    statuses = OPEN_STATUSES if show == "open" else tuple(RequestStatus.values)
    return render(
        request,
        "requests/queue.html",
        {"page": paginate(request, queue(statuses)), "show": show},
    )


@role_required(Role.STAFF)
def approve(request, request_id):
    blood_request = get_object_or_404(BloodRequest, request_id=request_id)
    if request.method == "POST":
        try:
            approve_request(blood_request, by=request.user)
        except WorkflowError as problem:
            messages.error(request, str(problem))
        else:
            messages.success(request, f"Request {request_id} was approved.")
    return redirect("requests:detail", request_id=request_id)


@role_required(Role.STAFF)
def reject(request, request_id):
    blood_request = get_object_or_404(BloodRequest, request_id=request_id)
    form = RejectForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            try:
                reject_request(blood_request, by=request.user, reason=form.cleaned_data["reason"])
            except WorkflowError as problem:
                messages.error(request, str(problem))
            else:
                messages.success(request, f"Request {request_id} was rejected.")
        else:
            messages.error(request, "Choose a reason before rejecting a request.")
    return redirect("requests:detail", request_id=request_id)


def _staff_action(request, request_id, action, success):
    blood_request = get_object_or_404(BloodRequest, request_id=request_id)
    if request.method == "POST":
        try:
            action(blood_request)
        except WorkflowError as problem:
            messages.error(request, str(problem))
        else:
            messages.success(request, success)
    return redirect("requests:detail", request_id=request_id)


@role_required(Role.STAFF)
def allocate(request, request_id):
    return _staff_action(
        request,
        request_id,
        lambda r: allocate_units(r, request.POST.getlist("unit_ids"), by=request.user),
        "The chosen units are reserved.",
    )


@role_required(Role.STAFF)
def issue(request, request_id):
    return _staff_action(
        request,
        request_id,
        lambda r: issue_reserved(r, by=request.user),
        "The reserved units were issued.",
    )


@role_required(Role.STAFF)
def release(request, request_id, allocation_id):
    get_object_or_404(Allocation, pk=allocation_id, request__request_id=request_id)
    return _staff_action(
        request,
        request_id,
        lambda r: release_allocation(allocation_id, by=request.user),
        "The unit was released back to stock.",
    )


@role_required(Role.HOSPITAL)
def cancel(request, request_id):
    hospital = hospital_for(request.user)
    blood_request = get_object_or_404(BloodRequest, request_id=request_id)
    if hospital is None or blood_request.hospital_id != hospital.pk:
        raise Http404
    if request.method == "POST":
        try:
            cancel_request(blood_request, by=request.user)
        except WorkflowError as problem:
            messages.error(request, str(problem))
        else:
            messages.success(request, f"Request {request_id} was cancelled.")
    return redirect("requests:detail", request_id=request_id)
