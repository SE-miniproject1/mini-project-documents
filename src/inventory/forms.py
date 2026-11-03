from django import forms

from donors.models import BloodGroup

from .models import Component, Status


class InventoryFilterForm(forms.Form):
    blood_group = forms.ChoiceField(required=False, choices=[("", "All blood groups"), *BloodGroup.choices])
    component_type = forms.ChoiceField(required=False, choices=[("", "All components"), *Component.choices])
    storage_location = forms.CharField(required=False, max_length=30)
    status = forms.ChoiceField(required=False, choices=[("", "All statuses"), *Status.choices])
    expiry_from = forms.DateField(required=False, input_formats=["%Y-%m-%d"], widget=forms.DateInput(attrs={"type": "date"}))
    expiry_to = forms.DateField(required=False, input_formats=["%Y-%m-%d"], widget=forms.DateInput(attrs={"type": "date"}))

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
    confirm = forms.BooleanField(required=True, label="I confirm this unit must be permanently discarded.")
