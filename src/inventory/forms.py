from django import forms
from django.conf import settings


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
