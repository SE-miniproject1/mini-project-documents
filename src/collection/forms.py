from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone

from camps.models import Camp, CampStatus

from .models import TestName, TestResult

MIN_VOLUME_ML = 200
MAX_VOLUME_ML = 600


class CollectionForm(forms.Form):
    volume_ml = forms.IntegerField(
        label="Volume collected (ml)",
        min_value=MIN_VOLUME_ML,
        max_value=MAX_VOLUME_ML,
        error_messages={
            "min_value": f"Volume must be between {MIN_VOLUME_ML} and {MAX_VOLUME_ML} ml.",
            "max_value": f"Volume must be between {MIN_VOLUME_ML} and {MAX_VOLUME_ML} ml.",
        },
    )
    bag_lot_number = forms.CharField(
        label="Bag lot number",
        max_length=20,
        validators=[RegexValidator(r"^[A-Za-z0-9-]+$", "Use letters, digits and hyphens only.")],
    )
    collection_site = forms.ChoiceField(
        label="Collection site",
        initial="Centre",
        help_text="The centre, or the camp where the donation was taken.",
    )
    collected_at = forms.DateTimeField(
        label="Collected at",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M"],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        camps = Camp.objects.filter(status=CampStatus.SCHEDULED, camp_date__lte=today)
        self.fields["collection_site"].choices = [("Centre", "Centre")] + [
            (camp.camp_id, f"{camp.name} ({camp.camp_id})") for camp in camps
        ]
        self.fields["collected_at"].initial = timezone.localtime().replace(second=0, microsecond=0)

    def clean_collected_at(self):
        collected_at = self.cleaned_data["collected_at"]
        if collected_at > timezone.now():
            raise forms.ValidationError("The collection time cannot be in the future.")
        return collected_at


class ScreeningResultsForm(forms.Form):
    """One select per test that has no result yet. Blank means not tested yet."""

    tested_on = forms.DateField(
        label="Tested on", widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
    )

    def __init__(self, *args, pending, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tested_on"].initial = timezone.localdate()
        for name in pending:
            self.fields[name] = forms.ChoiceField(
                label=TestName(name).label,
                required=False,
                choices=[("", "Not tested yet"), *TestResult.choices],
            )

    def clean_tested_on(self):
        tested_on = self.cleaned_data["tested_on"]
        if tested_on > timezone.localdate():
            raise forms.ValidationError("The test date cannot be in the future.")
        return tested_on

    def entered(self):
        """The results filled in, as {test name: result}."""
        return {
            name: value
            for name, value in self.cleaned_data.items()
            if name != "tested_on" and value
        }
