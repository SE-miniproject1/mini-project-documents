from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from .forms import LoginForm


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class PasswordChangeView(auth_views.PasswordChangeView):
    """Changing the password keeps this session and ends every other one (NFR-SEC11)."""

    template_name = "accounts/password_change_form.html"
    success_url = reverse_lazy("accounts:password_change_done")
