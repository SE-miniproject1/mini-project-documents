import re

from django import forms
from django.utils import timezone

from donors.models import BloodGroup
from inventory.models import Component

from .models import Urgency

PATIENT_REFERENCE = re.compile(r"^(?=.*\d)[A-Za-z0-9][A-Za-z0-9\-/]{2,19}$")


class RequestForm(forms.Form):
    blood_group = forms.ChoiceField(choices=[("", "Choose")] + BloodGroup.choices)
    component_type = forms.ChoiceField(
        label="Component", choices=[("", "Choose")] + Component.choices
    )
    quantity = forms.IntegerField(
        label="Units needed", min_value=1, max_value=50, widget=forms.NumberInput(attrs={"min": 1})
    )
    urgency = forms.ChoiceField(choices=Urgency.choices, initial=Urgency.ROUTINE)
    required_by = forms.DateTimeField(
        label="Required by",
        input_formats=["%Y-%m-%dT%H:%M", "%d-%m-%Y %H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        help_text="Date and time the units must reach the hospital.",
    )
    patient_reference = forms.CharField(
        label="Patient reference code",
        max_length=20,
        help_text=(
            "Your own case or bed number, with at least one digit. Never the patient's name."
        ),
    )

    def clean_required_by(self):
        value = self.cleaned_data["required_by"]
        if value <= timezone.now():
            raise forms.ValidationError("Required-by date and time must be in the future.")
        return value

    def clean_patient_reference(self):
        value = self.cleaned_data["patient_reference"].strip()
        if not PATIENT_REFERENCE.match(value):
            raise forms.ValidationError(
                "Use 3 to 20 letters, digits, hyphens or slashes, with at least one digit. "
                "Do not enter a patient's name."
            )
        return value.upper()


class RejectForm(forms.Form):
    reason = forms.ChoiceField(label="Reason for rejection")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.conf import settings

        self.fields["reason"].choices = [("", "Choose a reason")] + [
            (reason, reason) for reason in settings.BBMS_REJECTION_REASONS
        ]
