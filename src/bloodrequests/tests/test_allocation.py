from datetime import date, timedelta
from unittest import mock

from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_hospital, make_user
from audit.models import AuditEntry, Event
from bloodrequests.allocation import (
    allocate_units,
    cancel_request,
    candidate_units,
    issue_reserved,
    release_allocation,
)
from bloodrequests.models import Allocation, RequestStatus
from bloodrequests.workflow import WorkflowError
from donors.tests.helpers import make_donor
from inventory.models import BloodUnit, Status
from inventory.services.expiry import expire_due_units
from inventory.tests.helpers import make_unit

from .helpers import make_hospital_user, make_request


def a_pos_unit(status=Status.AVAILABLE, **kwargs):
    kwargs.setdefault("donor", make_donor(blood_group="A+"))
    return make_unit(status=status, **kwargs)


class AllocationTestCase(TestCase):
    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)
        self.hospital_user = make_hospital_user()
        self.request = make_request(
            self.hospital_user, quantity_requested=2, status=RequestStatus.APPROVED
        )


class AllocateTests(AllocationTestCase):
    """UT-29, UT-30 (SRS REQ-28)."""

    def test_matching_available_units_are_reserved_and_linked(self):
        units = [a_pos_unit(), a_pos_unit()]
        allocate_units(self.request, [u.unit_id for u in units], by=self.staff)
        for unit in units:
            unit.refresh_from_db()
            self.assertEqual(unit.status, Status.RESERVED)
        self.assertEqual(self.request.allocations.count(), 2)
        self.assertEqual(
            AuditEntry.objects.filter(
                event=Event.ALLOCATION, entity_id=self.request.request_id
            ).count(),
            2,
        )

    def test_a_blood_group_mismatch_is_refused_and_nothing_is_reserved(self):
        good, wrong = (
            a_pos_unit(),
            make_unit(status=Status.AVAILABLE, donor=make_donor(blood_group="O+")),
        )
        with self.assertRaisesMessage(WorkflowError, "needs A+"):
            allocate_units(self.request, [good.unit_id, wrong.unit_id], by=self.staff)
        good.refresh_from_db()
        self.assertEqual(good.status, Status.AVAILABLE)
        self.assertEqual(Allocation.objects.count(), 0)

    def test_a_component_mismatch_is_refused(self):
        unit = a_pos_unit(component_type="PRBC")
        with self.assertRaisesMessage(WorkflowError, "needs Whole Blood"):
            allocate_units(self.request, [unit.unit_id], by=self.staff)

    def test_quarantined_expired_reserved_issued_and_discarded_units_are_refused(self):
        for status in (
            Status.QUARANTINED,
            Status.RESERVED,
            Status.ISSUED,
            Status.DISCARDED,
            Status.EXPIRED,
        ):
            unit = a_pos_unit(status)
            with (
                self.subTest(status=status),
                self.assertRaisesMessage(WorkflowError, f"is {status}"),
            ):
                allocate_units(self.request, [unit.unit_id], by=self.staff)

    def test_a_unit_past_its_expiry_date_is_refused_even_if_still_marked_available(self):
        unit = a_pos_unit()
        BloodUnit.objects.filter(pk=unit.pk).update(
            expiry_date=date.today() - timedelta(days=1),
            collection_date=date.today() - timedelta(days=40),
        )
        with self.assertRaisesMessage(WorkflowError, "has expired"):
            allocate_units(self.request, [unit.unit_id], by=self.staff)
        self.assertNotIn(unit, candidate_units(self.request))

    def test_more_units_than_are_needed_or_none_are_refused(self):
        units = [a_pos_unit() for _ in range(3)]
        with self.assertRaisesMessage(WorkflowError, "Only 2 more"):
            allocate_units(self.request, [u.unit_id for u in units], by=self.staff)
        with self.assertRaisesMessage(WorkflowError, "at least one"):
            allocate_units(self.request, [], by=self.staff)
        with self.assertRaisesMessage(WorkflowError, "does not exist"):
            allocate_units(self.request, ["BU0000000000"], by=self.staff)

    def test_requests_that_are_not_approved_cannot_receive_units(self):
        unit = a_pos_unit()
        for status in (
            RequestStatus.PENDING,
            RequestStatus.REJECTED,
            RequestStatus.CANCELLED,
            RequestStatus.FULFILLED,
        ):
            request = make_request(
                self.hospital_user,
                status=status,
                rejection_reason="x" if status == "Rejected" else "",
            )
            with (
                self.subTest(status=status),
                self.assertRaisesMessage(WorkflowError, f"is {status}"),
            ):
                allocate_units(request, [unit.unit_id], by=self.staff)

    def test_two_requests_cannot_hold_the_same_unit(self):
        unit = a_pos_unit()
        other = make_request(self.hospital_user, status=RequestStatus.APPROVED)
        allocate_units(self.request, [unit.unit_id], by=self.staff)
        with self.assertRaisesMessage(WorkflowError, "is Reserved"):
            allocate_units(other, [unit.unit_id], by=self.staff)

    def test_the_database_itself_refuses_a_second_live_claim_on_a_unit(self):
        unit = a_pos_unit()
        Allocation.objects.create(request=self.request, unit=unit, allocated_by=self.staff)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Allocation.objects.create(request=self.request, unit=unit, allocated_by=self.staff)

    def test_candidates_are_exact_match_only_and_earliest_expiry_first(self):
        later = a_pos_unit(expiry_date=date.today() + timedelta(days=30))
        sooner = a_pos_unit(expiry_date=date.today() + timedelta(days=5))
        a_pos_unit(component_type="FFP")
        make_unit(status=Status.AVAILABLE, donor=make_donor(blood_group="O-"))
        self.assertEqual(list(candidate_units(self.request)), [sooner, later])


class IssueTests(AllocationTestCase):
    """UT-31, UT-32, IT-16, IT-17 (SRS REQ-29, REQ-30)."""

    def test_issuing_all_requested_units_fulfils_the_request(self):
        units = [a_pos_unit(), a_pos_unit()]
        allocate_units(self.request, [u.unit_id for u in units], by=self.staff)
        with self.captureOnCommitCallbacks(execute=True):
            issue_reserved(self.request, by=self.staff)
        self.request.refresh_from_db()
        self.assertEqual((self.request.status, self.request.quantity_issued), ("Fulfilled", 2))
        for unit in units:
            unit.refresh_from_db()
            self.assertEqual(unit.status, Status.ISSUED)
        allocation = self.request.allocations.first()
        self.assertEqual((allocation.issued_by, allocation.state), (self.staff, "Issued"))
        self.assertIsNotNone(allocation.issued_at)
        self.assertIn("fulfilled", mail.outbox[-1].body)

    def test_issuing_fewer_than_requested_is_partial_and_records_the_shortfall(self):
        allocate_units(self.request, [a_pos_unit().unit_id], by=self.staff)
        with self.captureOnCommitCallbacks(execute=True):
            issue_reserved(self.request, by=self.staff)
        self.request.refresh_from_db()
        self.assertEqual((self.request.status, self.request.shortfall), ("Partially Fulfilled", 1))
        self.assertIn("1 still outstanding", mail.outbox[-1].body)

    def test_a_partially_fulfilled_request_stays_open_for_more_units(self):
        allocate_units(self.request, [a_pos_unit().unit_id], by=self.staff)
        issue_reserved(self.request, by=self.staff)
        self.request.refresh_from_db()
        allocate_units(self.request, [a_pos_unit().unit_id], by=self.staff)
        issue_reserved(self.request, by=self.staff)
        self.request.refresh_from_db()
        self.assertEqual((self.request.status, self.request.quantity_issued), ("Fulfilled", 2))
        with self.assertRaisesMessage(WorkflowError, "is Fulfilled"):
            allocate_units(self.request, [a_pos_unit().unit_id], by=self.staff)

    def test_issue_needs_reserved_units_and_an_unexpired_one(self):
        with self.assertRaisesMessage(WorkflowError, "No units are reserved"):
            issue_reserved(self.request, by=self.staff)
        unit = a_pos_unit()
        allocate_units(self.request, [unit.unit_id], by=self.staff)
        BloodUnit.objects.filter(pk=unit.pk).update(
            expiry_date=date.today() - timedelta(days=1),
            collection_date=date.today() - timedelta(days=40),
        )
        with self.assertRaisesMessage(WorkflowError, "has expired"):
            issue_reserved(self.request, by=self.staff)
        unit.refresh_from_db()
        self.assertEqual(unit.status, Status.RESERVED)

    def test_a_failure_part_way_issues_nothing(self):
        units = [a_pos_unit(), a_pos_unit()]
        allocate_units(self.request, [u.unit_id for u in units], by=self.staff)
        real = BloodUnit.transition_to
        calls = []

        def flaky(unit, new_status, **kwargs):
            calls.append(unit.unit_id)
            if len(calls) == 2:
                raise RuntimeError("database went away")
            return real(unit, new_status, **kwargs)

        with mock.patch.object(BloodUnit, "transition_to", flaky), self.assertRaises(RuntimeError):
            issue_reserved(self.request, by=self.staff)
        self.request.refresh_from_db()
        self.assertEqual((self.request.status, self.request.quantity_issued), ("Approved", 0))
        for unit in units:
            unit.refresh_from_db()
            self.assertEqual(unit.status, Status.RESERVED)

    def test_the_request_status_change_is_audited(self):
        allocate_units(self.request, [a_pos_unit().unit_id], by=self.staff)
        issue_reserved(self.request, by=self.staff)
        entry = AuditEntry.objects.filter(
            event=Event.REQUEST_STATUS, previous_value="Approved"
        ).get()
        self.assertEqual(entry.new_value, "Partially Fulfilled")


class ReleaseAndCancelTests(AllocationTestCase):
    """UT-33, IT-17 (SRS REQ-31)."""

    def test_releasing_returns_the_unit_to_stock_and_frees_the_claim(self):
        unit = a_pos_unit()
        allocate_units(self.request, [unit.unit_id], by=self.staff)
        release_allocation(self.request.allocations.get().pk, by=self.staff)
        unit.refresh_from_db()
        self.assertEqual(unit.status, Status.AVAILABLE)
        self.assertEqual(self.request.allocations.get().state, "Released")
        allocate_units(self.request, [unit.unit_id], by=self.staff)

    def test_an_issued_or_released_unit_cannot_be_released(self):
        allocate_units(self.request, [a_pos_unit().unit_id], by=self.staff)
        allocation = self.request.allocations.get()
        release_allocation(allocation.pk, by=self.staff)
        with self.assertRaisesMessage(WorkflowError, "Only a reserved unit"):
            release_allocation(allocation.pk, by=self.staff)

    def test_cancelling_releases_every_reserved_unit(self):
        units = [a_pos_unit(), a_pos_unit()]
        allocate_units(self.request, [u.unit_id for u in units], by=self.staff)
        cancel_request(self.request, by=self.hospital_user)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, RequestStatus.CANCELLED)
        for unit in units:
            unit.refresh_from_db()
            self.assertEqual(unit.status, Status.AVAILABLE)
        self.assertEqual(self.request.allocations.filter(released_at__isnull=True).count(), 0)

    def test_a_pending_request_can_be_cancelled(self):
        pending = make_request(self.hospital_user)
        cancel_request(pending, by=self.hospital_user)
        pending.refresh_from_db()
        self.assertEqual(pending.status, RequestStatus.CANCELLED)

    def test_cancellation_is_barred_once_any_unit_is_issued(self):
        allocate_units(self.request, [a_pos_unit().unit_id], by=self.staff)
        issue_reserved(self.request, by=self.staff)
        self.request.refresh_from_db()
        with self.assertRaisesMessage(WorkflowError, "is Partially Fulfilled"):
            cancel_request(self.request, by=self.hospital_user)
        closed = make_request(self.hospital_user, status=RequestStatus.APPROVED, quantity_issued=1)
        with self.assertRaisesMessage(WorkflowError, "issued units"):
            cancel_request(closed, by=self.hospital_user)

    def test_a_reserved_unit_that_expires_frees_its_claim(self):
        """SRS REQ-19, D-42."""
        unit = a_pos_unit()
        allocate_units(self.request, [unit.unit_id], by=self.staff)
        BloodUnit.objects.filter(pk=unit.pk).update(
            expiry_date=date.today() - timedelta(days=1),
            collection_date=date.today() - timedelta(days=40),
        )
        expire_due_units()
        unit.refresh_from_db()
        self.assertEqual(unit.status, Status.EXPIRED)
        allocation = self.request.allocations.get()
        self.assertEqual(
            (allocation.state, allocation.release_reason), ("Released", "Unit became Expired")
        )
        replacement = a_pos_unit()
        allocate_units(self.request, [replacement.unit_id], by=self.staff)

    def test_a_reserved_unit_that_is_discarded_frees_its_claim(self):
        unit = a_pos_unit()
        allocate_units(self.request, [unit.unit_id], by=self.staff)
        unit.refresh_from_db()
        unit.transition_to(Status.DISCARDED, by=self.staff, reason="Bag damaged")
        self.assertEqual(self.request.allocations.get().state, "Released")


class AllocationScreenTests(AllocationTestCase):
    """ST-15, ST-16."""

    def login(self, username):
        self.client.logout()
        self.client.login(username=username, password=STRONG_PASSWORD)

    def test_staff_reserve_issue_and_the_hospital_sees_the_result(self):
        units = [a_pos_unit(), a_pos_unit()]
        self.login("staff01")
        detail = reverse("requests:detail", args=[self.request.request_id])
        self.assertContains(self.client.get(detail), units[0].unit_id)
        response = self.client.post(
            reverse("requests:allocate", args=[self.request.request_id]),
            {"unit_ids": [u.unit_id for u in units]},
            follow=True,
        )
        self.assertContains(response, "units are reserved")
        self.assertContains(response, "Confirm issue of reserved units")
        response = self.client.post(
            reverse("requests:issue", args=[self.request.request_id]), follow=True
        )
        self.assertContains(response, "were issued")
        self.login("hosp01")
        response = self.client.get(detail)
        self.assertContains(response, "Fulfilled")
        self.assertContains(response, units[0].unit_id)
        self.assertNotContains(response, "Reserve selected units")

    def test_a_mismatched_unit_posted_by_hand_is_refused_with_the_reason(self):
        wrong = make_unit(status=Status.AVAILABLE, donor=make_donor(blood_group="O+"))
        self.login("staff01")
        response = self.client.post(
            reverse("requests:allocate", args=[self.request.request_id]),
            {"unit_ids": [wrong.unit_id]},
            follow=True,
        )
        self.assertContains(response, "needs A+")
        wrong.refresh_from_db()
        self.assertEqual(wrong.status, Status.AVAILABLE)

    def test_release_from_the_screen(self):
        unit = a_pos_unit()
        allocate_units(self.request, [unit.unit_id], by=self.staff)
        self.login("staff01")
        pk = self.request.allocations.get().pk
        response = self.client.post(
            reverse("requests:release", args=[self.request.request_id, pk]), follow=True
        )
        self.assertContains(response, "released back to stock")
        other = make_request(self.hospital_user, status=RequestStatus.APPROVED)
        wrong_request = self.client.post(reverse("requests:release", args=[other.request_id, pk]))
        self.assertEqual(wrong_request.status_code, 404)

    def test_the_hospital_cancels_its_own_request_only(self):
        self.login("hosp01")
        response = self.client.post(
            reverse("requests:cancel", args=[self.request.request_id]), follow=True
        )
        self.assertContains(response, "was cancelled")
        make_hospital_user("hosp02", make_hospital(licence_number="L2"))
        self.login("hosp02")
        theirs = make_request(self.hospital_user)
        self.assertEqual(
            self.client.post(reverse("requests:cancel", args=[theirs.request_id])).status_code, 404
        )
        theirs.refresh_from_db()
        self.assertEqual(theirs.status, RequestStatus.PENDING)

    def test_the_hospital_has_no_cancel_button_after_an_issue(self):
        allocate_units(self.request, [a_pos_unit().unit_id], by=self.staff)
        issue_reserved(self.request, by=self.staff)
        self.login("hosp01")
        response = self.client.get(reverse("requests:detail", args=[self.request.request_id]))
        self.assertContains(response, "1 outstanding")
        self.assertNotContains(response, "Cancel this request")

    def test_hospital_users_and_donors_cannot_allocate_issue_or_release(self):
        unit = a_pos_unit()
        make_user("donor01", Role.DONOR)
        for username in ("hosp01", "donor01"):
            self.login(username)
            for name in ("allocate", "issue"):
                response = self.client.post(
                    reverse(f"requests:{name}", args=[self.request.request_id]),
                    {"unit_ids": [unit.unit_id]},
                )
                self.assertEqual(response.status_code, 403)
        unit.refresh_from_db()
        self.assertEqual(unit.status, Status.AVAILABLE)

    def test_staff_cannot_cancel_a_hospitals_request(self):
        self.login("staff01")
        self.assertEqual(
            self.client.post(
                reverse("requests:cancel", args=[self.request.request_id])
            ).status_code,
            403,
        )
