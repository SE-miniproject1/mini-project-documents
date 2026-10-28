from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone

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
    collection_site = forms.CharField(
        label="Collection site",
        max_length=30,
        initial="Centre",
        help_text="Centre, or the camp ID when collected at a camp.",
    )
    collected_at = forms.DateTimeField(
        label="Collected at",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M"],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["collected_at"].initial = timezone.localtime().replace(second=0, microsecond=0)

    def clean_collected_at(self):
        collected_at = self.cleaned_data["collected_at"]
        if collected_at > timezone.now():
            raise forms.ValidationError("The collection time cannot be in the future.")
        return collected_at
