from accounts.models import Role

from .navigation import nav_for

SHORTCUT_ROLES = (Role.STAFF, Role.ADMIN)


def navigation(request):
    match = getattr(request, "resolver_match", None)
    current = None
    if match:
        current = f"{match.namespace}:{match.url_name}" if match.namespace else match.url_name
    user = request.user
    return {
        "nav_links": nav_for(user),
        "current_url_name": current,
        # SRS UI-3: keyboard shortcuts are offered to the staff console only.
        "shortcuts_enabled": user.is_authenticated and user.role in SHORTCUT_ROLES,
    }
