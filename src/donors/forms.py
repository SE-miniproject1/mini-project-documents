from django import forms
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from accounts.models import Role, User

from .models import DeferralCondition, Donor
from .notifications import send_welcome
from .services.eligibility import apply_result, evaluate_eligibility, record_declarations
from .services.id_generator import generate_donor_id
from .validators import ensure_email_unused, ensure_mobile_unused, validate_age

CONSENT_TEXT = (
    "I consent to my personal and medical details being stored and used by the blood bank "
    "for donor screening, donation and traceability."
)


class DonorRegistrationForm(forms.ModelForm):
    """Self-registration (SRS REQ-1, UC-1). Creates the donor and a sign-in account together."""

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirm password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    declared_conditions = forms.ModelMultipleChoiceField(
        label="Do any of these apply to you?",
        queryset=DeferralCondition.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Tick every one that applies. Leave blank if none do.",
    )
    consent = forms.BooleanField(
        label=CONSENT_TEXT,
        error_messages={"required": "You must give consent to register."},
    )

    class Meta:
        model = Donor
        fields = [
            "full_name",
            "date_of_birth",
            "gender",
            "blood_group",
            "mobile_number",
            "email",
            "address_line",
            "city",
            "pin_code",
            "weight_kg",
            "emergency_contact_name",
            "emergency_contact_number",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }
        labels = {
            "mobile_number": "Mobile number",
            "address_line": "Address",
            "pin_code": "PIN code",
            "weight_kg": "Weight (kg)",
            "emergency_contact_name": "Emergency contact name",
            "emergency_contact_number": "Emergency contact number",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["declared_conditions"].queryset = DeferralCondition.objects.filter(
            is_active=True
        )

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data["date_of_birth"]
        validate_age(date_of_birth)
        return date_of_birth

    def clean_mobile_number(self):
        mobile_number = self.cleaned_data["mobile_number"]
        ensure_mobile_unused(mobile_number)
        return mobile_number

    def clean_email(self):
        email = self.cleaned_data["email"]
        ensure_email_unused(email)
        return email

    def clean(self):
        cleaned = super().clean()
        first, second = cleaned.get("password1"), cleaned.get("password2")
        if first and second:
            if first != second:
                self.add_error("password2", "The two passwords do not match.")
            else:
                probe = User(
                    username="candidate",
                    email=cleaned.get("email", ""),
                    first_name=(cleaned.get("full_name") or "").split(" ")[0],
                )
                try:
                    validate_password(first, user=probe)
                except forms.ValidationError as error:
                    self.add_error("password1", error)
        return cleaned

    def save(self, commit=True):
        """Create the donor, its account and the identifier in one transaction (SRS REQ-3)."""
        if not commit:
            raise ValueError("Registration always saves.")
        with transaction.atomic():
            donor_id = generate_donor_id()
            name = self.cleaned_data["full_name"].strip()
            first, _, last = name.partition(" ")
            user = User.objects.create_user(
                username=donor_id,
                email=self.cleaned_data["email"],
                password=self.cleaned_data["password1"],
                role=Role.DONOR,
                first_name=first,
                last_name=last,
            )
            donor = super().save(commit=False)
            donor.donor_id = donor_id
            donor.user = user
            donor.consent_timestamp = timezone.now()
            # Check what can already be checked, such as weight (SRS REQ-6).
            declared = list(self.cleaned_data["declared_conditions"])
            apply_result(donor, evaluate_eligibility(donor, declared=declared))
            donor.save()
            record_declarations(donor, declared)
        transaction.on_commit(lambda: send_welcome(donor))
        return donor


class ScreeningForm(forms.Form):
    """Measurements taken by staff at screening (SRS REQ-6)."""

    weight_kg = forms.DecimalField(
        label="Weight (kg)", max_digits=5, decimal_places=1, min_value=1, max_value=300
    )
    haemoglobin = forms.DecimalField(
        label="Haemoglobin (g/dL)", max_digits=4, decimal_places=1, min_value=1, max_value=25
    )
    systolic_bp = forms.IntegerField(
        label="Systolic blood pressure (mmHg)", min_value=40, max_value=300
    )
    declared_conditions = forms.ModelMultipleChoiceField(
        label="Conditions the donor declares",
        queryset=DeferralCondition.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["declared_conditions"].queryset = DeferralCondition.objects.filter(
            is_active=True
        )
