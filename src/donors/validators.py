"""Registration rules: age and duplicates (SRS REQ-3, REQ-4)."""

from datetime import date

from django.core.exceptions import ValidationError

from accounts.models import User

from .models import Donor

MIN_AGE = 18
MAX_AGE = 65

AGE_MESSAGE = "Donors must be between 18 and 65 years of age."
DUPLICATE_MOBILE_MESSAGE = (
    "This mobile number is already registered. Please sign in or reset your password."
)
DUPLICATE_EMAIL_MESSAGE = (
    "This email address is already registered. Please sign in or reset your password."
)


def age_on(date_of_birth, on):
    """Completed years on a given day. A 29 February birthday counts from 1 March."""
    birthday_passed = (on.month, on.day) >= (date_of_birth.month, date_of_birth.day)
    return on.year - date_of_birth.year - (0 if birthday_passed else 1)


def validate_age(date_of_birth, today=None):
    today = today or date.today()
    if not MIN_AGE <= age_on(date_of_birth, today) <= MAX_AGE:
        raise ValidationError(AGE_MESSAGE, code="age_out_of_range")


def ensure_mobile_unused(mobile_number, exclude_pk=None):
    """Mobile numbers are unique across active donors."""
    taken = Donor.objects.filter(mobile_number=mobile_number, is_active=True)
    if exclude_pk:
        taken = taken.exclude(pk=exclude_pk)
    if taken.exists():
        raise ValidationError(DUPLICATE_MOBILE_MESSAGE, code="duplicate_mobile")


def ensure_email_unused(email, exclude_pk=None):
    """Email addresses are unique across active donors and across every sign-in account."""
    email = (email or "").strip().lower()
    donors = Donor.objects.filter(email__iexact=email, is_active=True)
    if exclude_pk:
        donors = donors.exclude(pk=exclude_pk)
    if donors.exists() or User.objects.filter(email__iexact=email).exists():
        raise ValidationError(DUPLICATE_EMAIL_MESSAGE, code="duplicate_email")
