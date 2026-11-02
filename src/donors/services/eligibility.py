"""Donor eligibility (SRS REQ-6, REQ-8, NFR-Q4, BR-2, BR-3).

`evaluate_eligibility` is a pure decision: it reads a donor and some measurements and
returns every criterion that fails, not just the first. All comparisons use exact
decimals, because this rule protects donors and recipients and must not round.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from django.db import transaction

from core import config
from donors.models import ConditionKind, DonorDeclaration, DonorScreening, Eligibility
from donors.validators import add_years, age_on


@dataclass(frozen=True)
class Failure:
    code: str
    short: str  # kept short: it is stored in the donor's 100-character deferral reason
    message: str
    permanent: bool = False
    review_date: date | None = None


@dataclass(frozen=True)
class EligibilityResult:
    status: str
    failures: tuple
    review_date: date | None = None

    @property
    def eligible(self):
        return self.status == Eligibility.ELIGIBLE

    @property
    def reasons(self):
        return [failure.message for failure in self.failures]

    @property
    def short_reason(self):
        return "; ".join(failure.short for failure in self.failures)[:100]


def rules():
    return config.eligibility_rules()


def next_eligible_date(last_donation_date):
    """Last whole blood donation plus the donation interval (SRS REQ-8)."""
    if last_donation_date is None:
        return None
    return last_donation_date + timedelta(days=rules()["donation_interval_days"])


def evaluate_eligibility(
    donor,
    *,
    weight_kg=None,
    haemoglobin=None,
    systolic_bp=None,
    on=None,
    recorded=True,
    declared=(),
):
    """Check a donor against every criterion.

    Measurements that are not supplied fall back to the donor's recorded weight and
    haemoglobin. Blood pressure is only checked when measured. A criterion that cannot
    be checked yet is skipped, not assumed to pass or fail.

    `declared` is a list of `DeferralCondition` the donor has just declared. A permanent
    one defers the donor for good, a temporary one for its number of days (SRS REQ-5).

    With `recorded=False` the stored weight and haemoglobin are ignored, so only age
    and the donation interval are checked. The nightly job uses this: an old reading is
    not evidence about today, and re-using it would defer the donor again for ever.
    """
    on = on or date.today()
    cfg = rules()
    weight = weight_kg if weight_kg is not None else (donor.weight_kg if recorded else None)
    haemo = haemoglobin if haemoglobin is not None else (donor.haemoglobin if recorded else None)
    failures = []

    age = age_on(donor.date_of_birth, on)
    if age < cfg["min_age"]:
        failures.append(
            Failure(
                "age_under",
                "Under minimum age",
                f"Age {age} is below the minimum of {cfg['min_age']}.",
                review_date=add_years(donor.date_of_birth, cfg["min_age"]),
            )
        )
    elif age > cfg["max_age"]:
        failures.append(
            Failure(
                "age_over",
                "Over maximum age",
                f"Age {age} is above the maximum of {cfg['max_age']}.",
                permanent=True,
            )
        )

    review = on + timedelta(days=cfg["deferral_review_days"])
    if weight is not None and weight < cfg["min_weight_kg"]:
        failures.append(
            Failure(
                "underweight",
                "Underweight",
                f"Weight {weight} kg is below the minimum of {cfg['min_weight_kg']} kg.",
                review_date=review,
            )
        )
    if haemo is not None and haemo < cfg["min_haemoglobin"]:
        failures.append(
            Failure(
                "low_haemoglobin",
                "Low haemoglobin",
                f"Haemoglobin {haemo} g/dL is below the minimum of {cfg['min_haemoglobin']} g/dL.",
                review_date=review,
            )
        )
    if systolic_bp is not None and not cfg["min_systolic"] <= systolic_bp <= cfg["max_systolic"]:
        failures.append(
            Failure(
                "blood_pressure",
                "Blood pressure out of range",
                f"Systolic blood pressure {systolic_bp} mmHg is outside "
                f"{cfg['min_systolic']} to {cfg['max_systolic']} mmHg.",
                review_date=review,
            )
        )

    if donor.last_donation_date is not None:
        elapsed = (on - donor.last_donation_date).days
        if elapsed < cfg["donation_interval_days"]:
            failures.append(
                Failure(
                    "interval",
                    "Donation interval not elapsed",
                    f"Only {elapsed} days since the last donation; at least "
                    f"{cfg['donation_interval_days']} are required.",
                    review_date=next_eligible_date(donor.last_donation_date),
                )
            )

    for condition in declared:
        if condition.kind == ConditionKind.PERMANENT:
            failures.append(
                Failure(
                    "declared_permanent",
                    condition.name,
                    f"Declared condition: {condition.name}. Permanent deferral.",
                    permanent=True,
                )
            )
        else:
            failures.append(
                Failure(
                    "declared_temporary",
                    condition.name,
                    f"Declared condition: {condition.name}. Deferred for "
                    f"{condition.deferral_days} days.",
                    review_date=on + timedelta(days=condition.deferral_days),
                )
            )

    if donor.eligibility_status == Eligibility.PERMANENT:
        # A permanent deferral is never lifted by a measurement (SRS REQ-5).
        kept = Failure(
            "permanent",
            donor.deferral_reason or "Permanently deferred",
            donor.deferral_reason or "The donor is permanently deferred.",
            permanent=True,
        )
        return EligibilityResult(Eligibility.PERMANENT, (kept, *failures))
    if any(failure.permanent for failure in failures):
        return EligibilityResult(Eligibility.PERMANENT, tuple(failures))
    if failures:
        dates = [f.review_date for f in failures if f.review_date]
        return EligibilityResult(Eligibility.TEMPORARY, tuple(failures), max(dates))
    return EligibilityResult(Eligibility.ELIGIBLE, ())


def apply_result(donor, result):
    """Record an outcome on the donor. Does not save."""
    donor.eligibility_status = result.status
    donor.deferral_reason = "" if result.eligible else result.short_reason
    donor.deferral_review_date = None if result.eligible else result.review_date
    if donor.last_donation_date:
        donor.next_eligible_date = next_eligible_date(donor.last_donation_date)


def record_declarations(donor, conditions, *, by=None):
    """Keep the declared conditions against the donor. Already-declared ones are skipped."""
    for condition in conditions:
        DonorDeclaration.objects.get_or_create(
            donor=donor, condition=condition, defaults={"recorded_by": by}
        )


@transaction.atomic
def apply_screening(
    donor, *, weight_kg, haemoglobin, systolic_bp, screened_by, on=None, declared=()
):
    """Staff screening (UC4): evaluate, update the donor and keep a record of the visit."""
    result = evaluate_eligibility(
        donor,
        weight_kg=weight_kg,
        haemoglobin=haemoglobin,
        systolic_bp=systolic_bp,
        on=on,
        declared=declared,
    )
    record_declarations(donor, declared, by=screened_by)
    donor.weight_kg = weight_kg
    donor.haemoglobin = haemoglobin
    apply_result(donor, result)
    donor.save()
    screening = DonorScreening.objects.create(
        donor=donor,
        screened_by=screened_by,
        weight_kg=weight_kg,
        haemoglobin=haemoglobin,
        systolic_bp=systolic_bp,
        outcome=result.status,
        reasons="\n".join(result.reasons),
        review_date=result.review_date,
    )
    return screening, result


def record_donation(donor, on):
    """After a donation the donor waits out the interval (SRS REQ-8, NFR-S5). Does not save."""
    donor.last_donation_date = on
    donor.next_eligible_date = next_eligible_date(on)
    donor.eligibility_status = Eligibility.TEMPORARY
    donor.deferral_reason = "Donation interval not elapsed"
    donor.deferral_review_date = donor.next_eligible_date
