import re

from django import forms
from django.utils import timezone

PHONE = re.compile(r"^\d{10}$")


class CampForm(forms.Form):
    name = forms.CharField(label="Camp name", max_length=80)
    venue_address = forms.CharField(label="Venue address", max_length=150)
    camp_date = forms.DateField(
        label="Camp date",
        input_formats=["%Y-%m-%d", "%d-%m-%Y"],
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    start_time = forms.TimeField(
        label="Start time",
        input_formats=["%H:%M"],
        widget=forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
    )
    end_time = forms.TimeField(
        label="End time",
        input_formats=["%H:%M"],
        widget=forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
    )
    organiser_name = forms.CharField(label="Organiser name", max_length=60)
    organiser_contact = forms.CharField(
        label="Organiser contact number", max_length=10, help_text="10 digits."
    )
    target_units = forms.IntegerField(label="Target units", min_value=1, max_value=9999)

    def clean_camp_date(self):
        value = self.cleaned_data["camp_date"]
        if value < timezone.localdate():
            raise forms.ValidationError("Camp date cannot be in the past.")
        return value

    def clean_organiser_contact(self):
        value = self.cleaned_data["organiser_contact"].strip()
        if not PHONE.match(value):
            raise forms.ValidationError("Enter a 10-digit contact number.")
        return value

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_time"), cleaned.get("end_time")
        if start and end and end <= start:
            self.add_error("end_time", "End time must be later than the start time.")
        return cleaned
