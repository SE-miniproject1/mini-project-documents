from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.shortcuts import render

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
