from django import forms
from django.conf import settings

from donors.models import BloodGroup

from .models import Component, Status


class InventoryFilterForm(forms.Form):
    blood_group = forms.ChoiceField(
        required=False, choices=[("", "All blood groups"), *BloodGroup.choices]
    )
    component_type = forms.ChoiceField(
        required=False, choices=[("", "All components"), *Component.choices]
    )
    storage_location = forms.CharField(required=False, max_length=30)
    status = forms.ChoiceField(required=False, choices=[("", "All statuses"), *Status.choices])
    expiry_from = forms.DateField(
        required=False, input_formats=["%Y-%m-%d"], widget=forms.DateInput(attrs={"type": "date"})
    )
    expiry_to = forms.DateField(
        required=False, input_formats=["%Y-%m-%d"], widget=forms.DateInput(attrs={"type": "date"})
    )

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("expiry_from"), cleaned.get("expiry_to")
        if start and end and start > end:
            self.add_error("expiry_to", "Expiry end date must be on or after the start date.")
        return cleaned


class TransferForm(forms.Form):
    destination = forms.CharField(max_length=30)

    def clean_destination(self):
        value = self.cleaned_data["destination"].strip()
        if not value:
            raise forms.ValidationError("Enter a destination storage location.")
        return value


class DiscardForm(forms.Form):
    reason = forms.CharField(max_length=60)
    confirm = forms.BooleanField(
        required=True, label="I confirm this unit must be permanently discarded."
    )


class SeparationForm(forms.Form):
    """Tick the components to make and give each a volume (SRS REQ-15)."""

    def __init__(self, *args, unit, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit = unit
        for component, config in settings.BBMS_SEPARATION.items():
            self.fields[f"make_{component}"] = forms.BooleanField(
                label=f"Make {component}", required=False, initial=True
            )
            self.fields[f"volume_{component}"] = forms.IntegerField(
                label=f"{component} volume (ml)",
                min_value=1,
                max_value=unit.volume_ml,
                initial=config["suggested_ml"],
                required=False,
            )

    def clean(self):
        cleaned = super().clean()
        for component in settings.BBMS_SEPARATION:
            if cleaned.get(f"make_{component}") and not cleaned.get(f"volume_{component}"):
                self.add_error(f"volume_{component}", "Give a volume for each component you make.")
        return cleaned

    def volumes(self):
        return {
            component: self.cleaned_data[f"volume_{component}"]
            for component in settings.BBMS_SEPARATION
            if self.cleaned_data.get(f"make_{component}")
        }
