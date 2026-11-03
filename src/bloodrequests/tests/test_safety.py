"""Safety rules checked end to end: ST-26, ST-27 (SRS NFR-S1 to NFR-S4, US-27).

The unit tests in test_allocation.py exercise each guard on its own. These tests come at the
rules from the other side: they put a unit into a state the normal screens would never
produce, then confirm allocation and issue still refuse it.
"""

import threading
from datetime import date, timedelta

from django.db import connection
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

from accounts.models import Role
from accounts.tests.helpers import make_user
from bloodrequests.allocation import allocate_units, issue_reserved
from bloodrequests.models import Allocation, RequestStatus
from bloodrequests.workflow import WorkflowError
from collection.models import TestName, TestResult
from donors.tests.helpers import make_donor
from inventory.models import BloodUnit, Status
from inventory.services.safety import screening_problem
from inventory.tests.helpers import clear_screening, make_cleared_unit, make_unit

from .helpers import make_hospital_user, make_request


def force_status(unit, status):
    """Change a status behind the state machine's back, as a script or bad migration might."""
    BloodUnit.objects.filter(pk=unit.pk).update(status=status)
    unit.refresh_from_db()
    return unit


class ScreeningProblemTests(TestCase):
    def test_a_complete_non_reactive_panel_has_no_problem(self):
        self.assertIsNone(screening_problem(make_cleared_unit()))

    def test_a_missing_test_is_named(self):
        unit = clear_screening(make_unit(), skip=(TestName.values[0],))
        self.assertIn(TestName.values[0], screening_problem(unit))
        self.assertIn("incomplete", screening_problem(unit))

    def test_a_reactive_result_is_named(self):
        unit = clear_screening(make_unit(), result=TestResult.REACTIVE)
        self.assertIn("not clear", screening_problem(unit))

    def test_a_component_is_judged_by_its_parents_panel(self):
        parent = make_cleared_unit()
        child = make_unit(parent_unit=parent, donor=parent.donor)
        self.assertIsNone(screening_problem(child))
        orphan_parent = make_unit()
        child = make_unit(parent_unit=orphan_parent, donor=orphan_parent.donor)
        self.assertIn("incomplete", screening_problem(child))


class SafetyRuleTests(TestCase):
    """ST-26 (NFR-S1, NFR-S2) and ST-27 (NFR-S3)."""

    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)
        self.hospital_user = make_hospital_user()
        self.request = make_request(
            self.hospital_user, quantity_requested=1, status=RequestStatus.APPROVED
        )
        self.donor = make_donor(blood_group="A+")

    def assert_nothing_reserved(self, unit):
        unit.refresh_from_db()
        self.assertNotEqual(unit.status, Status.RESERVED)
        self.assertFalse(Allocation.objects.filter(unit=unit).exists())

    def test_an_untested_unit_forced_to_available_cannot_be_allocated(self):
        unit = force_status(make_unit(donor=self.donor), Status.AVAILABLE)
        with self.assertRaisesMessage(WorkflowError, "screening is incomplete"):
            allocate_units(self.request, [unit.unit_id], by=self.staff)
        self.assert_nothing_reserved(unit)

    def test_a_reactive_unit_forced_to_available_cannot_be_allocated(self):
        unit = clear_screening(make_unit(donor=self.donor), result=TestResult.REACTIVE)
        force_status(unit, Status.AVAILABLE)
        with self.assertRaisesMessage(WorkflowError, "screening is not clear"):
            allocate_units(self.request, [unit.unit_id], by=self.staff)
        self.assert_nothing_reserved(unit)

    def test_a_reserved_unit_whose_panel_turns_reactive_cannot_be_issued(self):
        unit = make_cleared_unit(donor=self.donor)
        allocate_units(self.request, [unit.unit_id], by=self.staff)
        unit.tests.filter(test_name=TestName.values[0]).update(result=TestResult.REACTIVE)
        with self.assertRaisesMessage(WorkflowError, "cannot be issued"):
            issue_reserved(self.request, by=self.staff)
        unit.refresh_from_db()
        self.assertEqual(unit.status, Status.RESERVED)

    def test_an_expired_unit_cannot_be_allocated_or_issued(self):
        stale = make_cleared_unit(donor=self.donor, expiry_date=date.today() - timedelta(days=1))
        with self.assertRaisesMessage(WorkflowError, "has expired"):
            allocate_units(self.request, [stale.unit_id], by=self.staff)
        unit = make_cleared_unit(donor=self.donor)
        allocate_units(self.request, [unit.unit_id], by=self.staff)
        with self.assertRaisesMessage(WorkflowError, "has expired and cannot be issued"):
            issue_reserved(self.request, by=self.staff, today=unit.expiry_date + timedelta(days=1))

    def test_a_wrong_group_unit_cannot_be_allocated(self):
        unit = make_cleared_unit(donor=make_donor(blood_group="O-"))
        with self.assertRaisesMessage(WorkflowError, "this request needs A+"):
            allocate_units(self.request, [unit.unit_id], by=self.staff)
        self.assert_nothing_reserved(unit)


@skipUnlessDBFeature("has_select_for_update")
class ConcurrentAllocationTests(TransactionTestCase):
    """ST-27 (NFR-S4): two staff allocate the same unit at the same moment."""

    def test_only_one_of_two_simultaneous_allocations_wins(self):
        staff = make_user("staff01", Role.STAFF)
        hospital_user = make_hospital_user()
        requests = [
            make_request(hospital_user, quantity_requested=1, status=RequestStatus.APPROVED)
            for _ in range(2)
        ]
        unit = make_cleared_unit(donor=make_donor(blood_group="A+"))
        barrier = threading.Barrier(2)
        outcomes = []

        def attempt(request):
            try:
                barrier.wait()
                allocate_units(request, [unit.unit_id], by=staff)
                outcomes.append("won")
            except Exception as exc:  # the loser may see a lock error or a workflow error
                outcomes.append(exc)
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt, args=(r,)) for r in requests]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(outcomes.count("won"), 1, outcomes)
        self.assertEqual(Allocation.objects.filter(unit=unit).count(), 1)


class SequentialAllocationRaceTests(TestCase):
    """ST-27 (NFR-S4) on databases without row locks, such as the SQLite test database.

    SQLite serialises writers, so the second allocation always sees the first one's
    reservation. The test pins that behaviour; the threaded test above covers PostgreSQL.
    """

    def test_the_second_allocation_of_a_reserved_unit_is_refused(self):
        staff = make_user("staff01", Role.STAFF)
        hospital_user = make_hospital_user()
        first, second = (
            make_request(hospital_user, quantity_requested=1, status=RequestStatus.APPROVED)
            for _ in range(2)
        )
        unit = make_cleared_unit(donor=make_donor(blood_group="A+"))
        allocate_units(first, [unit.unit_id], by=staff)
        with self.assertRaisesMessage(WorkflowError, "is Reserved"):
            allocate_units(second, [unit.unit_id], by=staff)
        self.assertEqual(Allocation.objects.filter(unit=unit).count(), 1)
