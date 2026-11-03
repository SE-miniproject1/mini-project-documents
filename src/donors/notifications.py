import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_welcome(donor):
    """Welcome message after registration. A delivery failure never undoes the registration."""
    try:
        send_mail(
            "Welcome to the Blood Bank",
            (
                f"Hello {donor.full_name},\n\n"
                "Thank you for registering as a blood donor.\n"
                f"Your donor ID is {donor.donor_id}. It is also your username for signing in.\n"
            ),
            settings.DEFAULT_FROM_EMAIL,
            [donor.email],
        )
    except Exception:  # noqa: BLE001 - see docstring
        logger.exception("welcome email failed donor_id=%s", donor.donor_id)
