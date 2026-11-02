"""Screening results, release to inventory and discard (SRS REQ-12, REQ-13, REQ-14, NFR-S1).

NFR-S1 is the most safety-critical rule in the system: no unit that has not completed the
mandatory panel with every result Non-Reactive may be issued. This module is the only way
a unit leaves quarantine.
"""

import logging
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from accounts.models import Role, User
from collection.models import ScreeningTest, TestName, TestResult
from inventory.models import BloodUnit, Status

logger = logging.getLogger(__name__)

PANEL = tuple(TestName.values)
REACTIVE_REASON = "Reactive Screening"


class ScreeningError(Exception):
    """Base for refusals that change nothing."""


class UnitNotQuarantinedError(ScreeningError):
    """Results can only be entered, and a unit released, while it is Quarantined."""


class ResultAlreadyRecordedError(ScreeningError):
    """A recorded result is final."""


class ScreeningIncompleteError(ScreeningError):
    """The mandatory panel is not complete."""

    def __init__(self, missing):
        self.missing = tuple(missing)
        names = ", ".join(TestName(name).label for name in self.missing)
        super().__init__(f"The screening panel is incomplete. Missing results: {names}.")


@dataclass(frozen=True)
class ReleaseResult:
    released: bool
    status: str
    message: str


def _lock(unit):
    locked = BloodUnit.objects.select_for_update().get(pk=unit.pk)
    unit.refresh_from_db()
    if locked.status != Status.QUARANTINED:
        raise UnitNotQuarantinedError(f"The unit is {locked.status}, not Quarantined.")
    return locked


def missing_tests(unit):
    recorded = set(unit.tests.values_list("test_name", flat=True))
    return [name for name in PANEL if name not in recorded]


@transaction.atomic
def record_results(unit, results, *, by, tested_on=None):
    """Record results (a mapping of test name to result). A Reactive result discards the unit.

    Returns the unit's status afterwards.
    """
    _lock(unit)
    tested_on = tested_on or date.today()
    existing = set(unit.tests.values_list("test_name", flat=True))
    for name, value in results.items():
        if name not in PANEL:
            raise ValueError(f"Unknown test {name!r}.")
        if value not in TestResult.values:
            raise ValueError(f"Unknown result {value!r}.")
        if name in existing:
            raise ResultAlreadyRecordedError(f"{TestName(name).label} was already recorded.")
        ScreeningTest.objects.create(
            unit=unit, test_name=name, result=value, tested_on=tested_on, tested_by=by
        )

    if unit.tests.filter(result=TestResult.REACTIVE).exists():
        # REQ-14: any Reactive result removes the unit from circulation for good.
        unit.transition_to(Status.DISCARDED, by=by, reason=REACTIVE_REASON)
        transaction.on_commit(lambda: notify_administrators(unit))
    return unit.status


@transaction.atomic
def release_unit(unit, *, by, today=None):
    """Move a unit from Quarantined to Available, only if the whole panel is Non-Reactive."""
    today = today or date.today()
    _lock(unit)
    missing = missing_tests(unit)
    if missing:
        raise ScreeningIncompleteError(missing)

    if unit.tests.filter(result=TestResult.REACTIVE).exists():
        unit.transition_to(Status.DISCARDED, by=by, reason=REACTIVE_REASON)
        transaction.on_commit(lambda: notify_administrators(unit))
        return ReleaseResult(
            False, unit.status, "A reactive result was found. The unit is discarded."
        )

    if unit.expiry_date < today:
        # Never release a unit that has already expired while waiting for results (NFR-S2).
        unit.transition_to(Status.EXPIRED, by=by)
        return ReleaseResult(
            False, unit.status, "The unit expired before release. It was not released."
        )

    unit.transition_to(Status.AVAILABLE, by=by)
    unit.storage_location = settings.BBMS_DEFAULT_STORAGE_LOCATION
    unit.save(update_fields=["storage_location"])
    return ReleaseResult(True, unit.status, "The unit was released to inventory.")


def notify_administrators(unit):
    """Confidential alert about a reactive unit (SRS REQ-14).

    The donor's identity appears only here, only for administrators. A mail failure is
    logged and never undoes the discard (SRS CI-6).
    """
    recipients = list(
        User.objects.filter(role=Role.ADMIN, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    if not recipients:
        logger.error("no administrator to alert about reactive unit_id=%s", unit.unit_id)
        return
    reactive = ", ".join(
        TestName(name).label
        for name in unit.tests.filter(result=TestResult.REACTIVE).values_list(
            "test_name", flat=True
        )
    )
    donor = unit.donor
    try:
        send_mail(
            f"Reactive screening result for unit {unit.unit_id}",
            (
                "CONFIDENTIAL. For administrators only.\n\n"
                f"Unit {unit.unit_id} was discarded after a reactive result: {reactive}.\n"
                f"Donor: {donor.full_name} ({donor.donor_id}), mobile {donor.mobile_number}.\n"
                "The unit can never be issued. Arrange donor follow-up under the blood bank's "
                "policy.\n"
            ),
            settings.DEFAULT_FROM_EMAIL,
            recipients,
        )
    except Exception:  # noqa: BLE001 - delivery problems must not undo the discard
        logger.exception("reactive alert failed unit_id=%s", unit.unit_id)
