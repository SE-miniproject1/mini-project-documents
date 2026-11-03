from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied

from . import lockout
from .models import User


class LockoutBackend(ModelBackend):
    """Username and password authentication with lockout (SRS NFR-SEC1, NFR-SEC4)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = User._default_manager.get_by_natural_key(username)
        except User.DoesNotExist:
            # Hash anyway so the response time does not reveal whether the account exists.
            User().set_password(password)
            return None
        if lockout.is_locked(user):
            raise PermissionDenied("Account locked")
        if user.check_password(password) and self.user_can_authenticate(user):
            lockout.reset(user)
            return user
        lockout.register_failure(user)
        return None
