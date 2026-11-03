"""Ending temporary deferrals once their review date has passed (SRS REQ-8)."""

import logging
from datetime import date

from donors.models import Donor, Eligibility

from .eligibility import apply_result, evaluate_eligibility

logger = logging.getLogger(__name__)


def clear_expired_deferrals(today=None):
    """Return donors whose review date has passed to Eligible, if they still qualify.

    Only age and the donation interval are re-checked, because weight and haemoglobin
    must be measured again at screening. A donor who still fails one of those two stays
    deferred with a new review date. Permanent deferrals are never touched.
    """
    today = today or date.today()
    due = Donor.objects.filter(
        is_active=True,
        eligibility_status=Eligibility.TEMPORARY,
        deferral_review_date__lte=today,
    )
    cleared = 0
    for donor in due:
        result = evaluate_eligibility(donor, on=today, recorded=False)
        apply_result(donor, result)
        donor.save(
            update_fields=[
                "eligibility_status",
                "deferral_reason",
                "deferral_review_date",
                "next_eligible_date",
            ]
        )
        if result.eligible:
            cleared += 1
            logger.info("deferral cleared donor_id=%s", donor.donor_id)
    return cleared
