"""No blood is taken from a donor who is not eligible (SRS REQ-7, NFR-S5).

This is the single check every collection goes through. It looks at the recorded
status and then at the dates again, so a stale status can never allow a donor to be
bled more often than the donation interval permits.
"""

from datetime import date

from donors.models import Eligibility
from donors.services.eligibility import next_eligible_date, rules


class CollectionBlockedError(Exception):
    """The donor cannot donate now. `reason` and `review_date` are safe to show staff."""

    def __init__(self, reason, review_date=None):
        self.reason = reason
        self.review_date = review_date
        super().__init__(self.describe())

    def describe(self):
        if self.review_date:
            return f"{self.reason}. Review on {self.review_date:%d-%m-%Y}."
        return f"{self.reason}."


def ensure_can_collect(donor, on=None):
    on = on or date.today()
    if not donor.is_active:
        raise CollectionBlockedError("The donor record is deactivated")
    if donor.eligibility_status != Eligibility.ELIGIBLE:
        raise CollectionBlockedError(
            donor.deferral_reason or donor.eligibility_status, donor.deferral_review_date
        )
    if donor.last_donation_date is not None:
        interval = rules()["donation_interval_days"]
        elapsed = (on - donor.last_donation_date).days
        if elapsed < interval:
            raise CollectionBlockedError(
                f"Only {elapsed} days since the last donation; {interval} are required",
                next_eligible_date(donor.last_donation_date),
            )


def collection_status(donor, on=None):
    """(allowed, message) for showing beside the Start Collection control."""
    try:
        ensure_can_collect(donor, on)
    except CollectionBlockedError as blocked:
        return False, blocked.describe()
    return True, ""
