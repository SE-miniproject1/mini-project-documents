"""URL configuration used only by the role enforcement tests."""

from django.http import HttpResponse
from django.urls import include, path
from django.views import View

from accounts.models import Role
from accounts.permissions import RoleRequiredMixin, role_required


@role_required(Role.STAFF, Role.ADMIN)
def staff_only(request):
    return HttpResponse("staff area")


@role_required(Role.ADMIN)
def admin_only(request):
    return HttpResponse("admin area")


class HospitalOnly(RoleRequiredMixin, View):
    allowed_roles = (Role.HOSPITAL,)

    def get(self, request):
        return HttpResponse("hospital area")


urlpatterns = [
    path("staff-only/", staff_only),
    path("admin-only/", admin_only),
    path("hospital-only/", HospitalOnly.as_view()),
    path("accounts/", include("accounts.urls")),
    path("donors/", include("donors.urls")),
    path("", include("core.urls")),
]
