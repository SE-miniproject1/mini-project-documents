from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from . import lockout
from .models import Hospital, Role, User


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


ADMIN_CREATABLE_ROLES = [(r.value, r.label) for r in Role if r != Role.DONOR]


class UserAdminForm(forms.ModelForm):
    """Create or change an account: one role, and a hospital for hospital users (REQ-45)."""

    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Initial password. The user can change it after signing in.",
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "role", "hospital", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hospital"].queryset = Hospital.objects.filter(is_active=True)
        self.fields["hospital"].required = False
        if self.instance.pk:
            self.fields["password"].label = "New password (leave blank to keep)"
            if self.instance.role == Role.DONOR:
                self.fields["role"].choices = Role.choices
            else:
                self.fields["role"].choices = ADMIN_CREATABLE_ROLES
        else:
            self.fields["role"].choices = ADMIN_CREATABLE_ROLES
            self.fields["password"].required = True
            self.fields["password"].label = "Initial password"
            self.fields.pop("is_active")

    def clean(self):
        cleaned = super().clean()
        role, hospital = cleaned.get("role"), cleaned.get("hospital")
        if role == Role.HOSPITAL and not hospital:
            self.add_error("hospital", "A hospital user must belong to a hospital.")
        if role and role != Role.HOSPITAL and hospital:
            self.add_error("hospital", "Only hospital users belong to a hospital.")
        password = cleaned.get("password")
        if password:
            try:
                validate_password(password, self.instance)
            except ValidationError as problem:
                self.add_error("password", problem)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password"):
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class HospitalForm(forms.ModelForm):
    class Meta:
        model = Hospital
        fields = [
            "name",
            "address",
            "licence_number",
            "contact_name",
            "contact_phone",
            "contact_email",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields.pop("is_active")

    def clean_licence_number(self):
        return self.cleaned_data["licence_number"].strip().upper()
