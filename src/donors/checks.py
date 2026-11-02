from django.conf import settings
from django.core.checks import Error, register


@register()
def donation_interval_is_not_below_ninety_days(app_configs, **kwargs):
    """SRS BR-2: the interval is configurable but never below 90 days."""
    days = settings.BBMS_ELIGIBILITY["donation_interval_days"]
    if days < 90:
        return [
            Error(
                f"BBMS_ELIGIBILITY donation_interval_days is {days}; it must be at least 90.",
                id="donors.E001",
            )
        ]
    return []
