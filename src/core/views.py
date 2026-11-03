from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from accounts.models import Role
from accounts.permissions import role_required

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
