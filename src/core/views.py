from django.contrib.auth.decorators import login_not_required
from django.http import JsonResponse
from django.shortcuts import render


@login_not_required
def health(request):
    """Liveness probe for the reverse proxy and for monitoring (SAD section 4.4)."""
    return JsonResponse({"status": "ok"})


def home(request):
    return render(request, "core/home.html")
