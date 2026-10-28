from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from audit.models import Event
from audit.services import record_event
from core.listing import apply_sort, paginate

from .forms import HospitalForm, LoginForm, UserAdminForm
from .models import Hospital, Role, User
from .permissions import role_required


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class PasswordChangeView(auth_views.PasswordChangeView):
    """Changing the password keeps this session and ends every other one (NFR-SEC11)."""

    template_name = "accounts/password_change_form.html"
    success_url = reverse_lazy("accounts:password_change_done")


# ---------------------------------------------------------------------------
# Administration of users and hospitals (SRS REQ-45)
# ---------------------------------------------------------------------------
def _audit_user_change(request, user, previous, new, reason):
    record_event(
        Event.CONFIG_CHANGE,
        actor=request.user,
        entity_type="User",
        entity_id=user.username,
        previous=previous,
        new=new,
        reason=reason,
    )


@role_required(Role.ADMIN)
def user_admin(request):
    users = User.objects.select_related("hospital")
    query = request.GET.get("q", "").strip()
    if query:
        users = users.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(last_name__icontains=query)
        )
    role = request.GET.get("role", "")
    if role in Role.values:
        users = users.filter(role=role)
    users, sort = apply_sort(
        request,
        users,
        {"username": "username", "role": "role", "status": "is_active"},
        "username",
    )
    return render(
        request,
        "accounts/user_admin.html",
        {
            "page": paginate(request, users),
            "sort": sort,
            "q": query,
            "role": role,
            "roles": Role.choices,
        },
    )


@role_required(Role.ADMIN)
def user_create(request):
    form = UserAdminForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        _audit_user_change(request, user, "", user.role, "Account created")
        messages.success(request, f"Account {user.username} was created.")
        return redirect("accounts:user_admin")
    return render(
        request,
        "accounts/admin_form.html",
        {"form": form, "heading": "New user", "cancel_url": reverse_lazy("accounts:user_admin")},
    )


@role_required(Role.ADMIN)
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    before = (user.role, user.is_active)
    form = UserAdminForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        if user == request.user and (
            form.cleaned_data["role"] != Role.ADMIN or not form.cleaned_data["is_active"]
        ):
            form.add_error(None, "You cannot remove your own administrator access.")
        else:
            user = form.save()
            if (user.role, user.is_active) != before:
                _audit_user_change(
                    request,
                    user,
                    f"{before[0]}/{'active' if before[1] else 'inactive'}",
                    f"{user.role}/{'active' if user.is_active else 'inactive'}",
                    "Role or status changed",
                )
            messages.success(request, f"Account {user.username} was updated.")
            return redirect("accounts:user_admin")
    return render(
        request,
        "accounts/admin_form.html",
        {
            "form": form,
            "heading": f"Edit {user.username}",
            "cancel_url": reverse_lazy("accounts:user_admin"),
        },
    )


@role_required(Role.ADMIN)
def hospital_list(request):
    hospitals, sort = apply_sort(
        request,
        Hospital.objects.all(),
        {"name": "name", "licence": "licence_number", "status": "is_active"},
        "name",
    )
    return render(
        request,
        "accounts/hospital_list.html",
        {"page": paginate(request, hospitals), "sort": sort},
    )


@role_required(Role.ADMIN)
def hospital_create(request):
    form = HospitalForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        hospital = form.save()
        record_event(
            Event.CONFIG_CHANGE,
            actor=request.user,
            entity_type="Hospital",
            entity_id=hospital.licence_number,
            new="active",
            reason="Hospital registered",
        )
        messages.success(request, f"{hospital.name} was registered.")
        return redirect("accounts:hospital_list")
    return render(
        request,
        "accounts/admin_form.html",
        {
            "form": form,
            "heading": "Register a hospital",
            "cancel_url": reverse_lazy("accounts:hospital_list"),
        },
    )


@role_required(Role.ADMIN)
def hospital_edit(request, pk):
    hospital = get_object_or_404(Hospital, pk=pk)
    was_active = hospital.is_active
    form = HospitalForm(request.POST or None, instance=hospital)
    if request.method == "POST" and form.is_valid():
        hospital = form.save()
        if hospital.is_active != was_active:
            record_event(
                Event.CONFIG_CHANGE,
                actor=request.user,
                entity_type="Hospital",
                entity_id=hospital.licence_number,
                previous="active" if was_active else "inactive",
                new="active" if hospital.is_active else "inactive",
                reason="Hospital status changed",
            )
        messages.success(request, f"{hospital.name} was updated.")
        return redirect("accounts:hospital_list")
    return render(
        request,
        "accounts/admin_form.html",
        {
            "form": form,
            "heading": f"Edit {hospital.name}",
            "cancel_url": reverse_lazy("accounts:hospital_list"),
        },
    )
