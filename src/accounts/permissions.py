"""Server-side role enforcement (SRS NFR-SEC5, NFR-SEC6).

Authorisation is checked here on every request and never trusts what the
client chose to show. Anonymous visitors are handled earlier by the login
middleware, so these helpers only decide between roles.
"""

import logging
from functools import wraps

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied

from .models import Role

logger = logging.getLogger(__name__)

STAFF_ROLES = (Role.STAFF, Role.ADMIN)


def _deny(request, roles):
    logger.warning(
        "authorisation failure user_id=%s role=%s path=%s needs=%s",
        getattr(request.user, "pk", None),
        getattr(request.user, "role", None),
        request.path,
        ",".join(roles),
    )
    raise PermissionDenied


def role_required(*roles):
    """Decorator for function views: allow only the listed roles."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated or request.user.role not in roles:
                _deny(request, roles)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


class RoleRequiredMixin(AccessMixin):
    """Mixin for class-based views. Set `allowed_roles` on the view."""

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in self.allowed_roles:
            _deny(request, self.allowed_roles)
        return super().dispatch(request, *args, **kwargs)
