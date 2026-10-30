from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from . import lockout
from .models import User


class LoginForm(AuthenticationForm):
    def get_invalid_login_error(self):
        username = self.cleaned_data.get("username")
        user = User._default_manager.filter(**{User.USERNAME_FIELD: username}).first()
        if user and lockout.is_locked(user):
            minutes = lockout.minutes_remaining(user)
            return ValidationError(
                "This account is locked after repeated failed sign-ins. "
                f"Try again in {minutes} minute{'s' if minutes != 1 else ''}.",
                code="locked",
            )
        return super().get_invalid_login_error()
