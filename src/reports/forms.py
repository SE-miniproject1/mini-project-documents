from datetime import date, timedelta

from django import forms


class RangeForm(forms.Form):
    """The date range for a report (SRS REQ-42)."""

    start = forms.DateField(label="From", widget=forms.DateInput(attrs={"type": "date"}))
    end = forms.DateField(label="To", widget=forms.DateInput(attrs={"type": "date"}))

    @classmethod
    def last_30_days(cls):
        today = date.today()
        return {"start": today - timedelta(days=29), "end": today}
