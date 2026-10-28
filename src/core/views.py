from django.http import JsonResponse


def health(request):
    """Liveness probe for the reverse proxy and for monitoring (SAD section 4.4)."""
    return JsonResponse({"status": "ok"})
