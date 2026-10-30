from decimal import Decimal

from django import forms

from . import config


class ConfigForm(forms.Form):
    """One field per administrator-configurable parameter (SRS REQ-46)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current = config.current_values()
        for param in config.PARAMS:
            field_class = forms.DecimalField if param.kind is Decimal else forms.IntegerField
            extra = {"decimal_places": 1, "max_digits": 5} if param.kind is Decimal else {}
            self.fields[self.field_name(param.key)] = field_class(
                label=param.label,
                initial=current[param.key],
                help_text=param.help,
                **extra,
            )

    @staticmethod
    def field_name(key):
        return key.replace(".", "__").replace("+", "pos").replace("-", "neg")

    def clean(self):
        cleaned = super().clean()
        values = {
            p.key: cleaned[self.field_name(p.key)]
            for p in config.PARAMS
            if self.field_name(p.key) in cleaned
        }
        for key, message in config.validate(values).items():
            self.add_error(self.field_name(key), message)
        return cleaned

    def values(self):
        return {p.key: self.cleaned_data[self.field_name(p.key)] for p in config.PARAMS}

    def sections(self):
        sections = {}
        for param in config.PARAMS:
            sections.setdefault(param.section, []).append(self[self.field_name(param.key)])
        return sections.items()
