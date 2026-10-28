"""Safety rule tests and concurrency hardening (SRS NFR-S1 to NFR-S4, ST-26, ST-27, US-27).

Validates:
- NFR-S1: Untested / quarantined units can never be allocated or issued.
- NFR-S2: Expired units can never be allocated or issued through any route.
- NFR-S3: Group mismatch allocation is strictly refused and preserves unit state.
- NFR-S4: Concurrent double allocation / race condition on the same unit is prevented;
  database unique constraints enforce only one live unreleased allocation per blood unit.
"""

from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import make_hospital, make_user
from bloodrequests.allocation import allocate_units
from bloodrequests.models import Allocation, RequestStatus
from bloodrequests.tests.helpers import make_hospital_user, make_request
from bloodrequests.workflow import WorkflowError
from donors.tests.helpers import make_donor
from inventory.models import Status
from inventory.tests.helpers import make_unit


class SafetyRulesAndConcurrencyTests(TestCase):
    """Exercises ST-26 and ST-27 system tests covering NFR-S1, NFR-S2, NFR-S3, and NFR-S4."""

    def setUp(self):
        self.staff1 = make_user("staff_safety_1", Role.STAFF)
        self.staff2 = make_user("staff_safety_2", Role.STAFF)
        hospital = make_hospital(name="Safety General", licence_number="LIC-SAFE-01")
        self.hospital_user = make_hospital_user("hosp_safety_1", hospital)
        self.req_a_pos = make_request(
            self.hospital_user,
            blood_group="A+",
            component_type="Whole Blood",
            quantity_requested=1,
            status=RequestStatus.APPROVED,
        )

    def test_nfr_s1_untested_quarantined_unit_cannot_be_allocated_or_issued(self):
        """NFR-S1 / ST-26: Quarantined units cannot be allocated or issued."""
        donor = make_donor(blood_group="A+")
        quarantined_unit = make_unit(donor=donor, status=Status.QUARANTINED)

        # 1. Direct service attempt
        with self.assertRaises(WorkflowError) as cm:
            allocate_units(self.req_a_pos, [quarantined_unit.unit_id], by=self.staff1)
        self.assertIn("Quarantined", str(cm.exception))

        quarantined_unit.refresh_from_db()
        self.assertEqual(quarantined_unit.status, Status.QUARANTINED)
        self.assertEqual(Allocation.objects.filter(unit=quarantined_unit).count(), 0)

        # 2. HTTP POST attempt as staff
        self.client.force_login(self.staff1)
        response = self.client.post(
            reverse("requests:allocate", args=[self.req_a_pos.request_id]),
            {"unit_ids": [quarantined_unit.unit_id]},
            follow=True,
        )
        self.assertContains(response, "is Quarantined, not Available")
        quarantined_unit.refresh_from_db()
        self.assertEqual(quarantined_unit.status, Status.QUARANTINED)

    def test_nfr_s2_expired_unit_cannot_be_allocated_or_issued(self):
        """NFR-S2 / ST-26: Expired unit can never be allocated or issued through any route."""
        donor = make_donor(blood_group="A+")
        yesterday = date.today() - timedelta(days=1)
        # Marked Available in DB but past expiry date
        expired_unit = make_unit(
            donor=donor,
            status=Status.AVAILABLE,
            expiry_date=yesterday,
        )

        # 1. Service-level check
        with self.assertRaises(WorkflowError) as cm:
            allocate_units(self.req_a_pos, [expired_unit.unit_id], by=self.staff1)
        self.assertIn("expired", str(cm.exception).lower())

        expired_unit.refresh_from_db()
        self.assertEqual(expired_unit.status, Status.AVAILABLE)

        # 2. HTTP endpoint check
        self.client.force_login(self.staff1)
        response = self.client.post(
            reverse("requests:allocate", args=[self.req_a_pos.request_id]),
            {"unit_ids": [expired_unit.unit_id]},
            follow=True,
        )
        self.assertContains(response, "has expired")
        expired_unit.refresh_from_db()
        self.assertEqual(expired_unit.status, Status.AVAILABLE)

        # 3. Unit explicitly marked EXPIRED
        expired_status_unit = make_unit(donor=donor, status=Status.EXPIRED)
        with self.assertRaises(WorkflowError):
            allocate_units(self.req_a_pos, [expired_status_unit.unit_id], by=self.staff1)

    def test_nfr_s3_group_mismatch_allocation_prevented_and_state_preserved(self):
        """NFR-S3 / ST-27: Group mismatch is rejected; unit remains Available."""
        o_pos_donor = make_donor(blood_group="O+")
        o_pos_unit = make_unit(donor=o_pos_donor, status=Status.AVAILABLE)

        # Request is A+
        with self.assertRaises(WorkflowError) as cm:
            allocate_units(self.req_a_pos, [o_pos_unit.unit_id], by=self.staff1)
        self.assertIn("needs A+", str(cm.exception))

        o_pos_unit.refresh_from_db()
        self.assertEqual(o_pos_unit.status, Status.AVAILABLE)
        self.assertEqual(Allocation.objects.filter(unit=o_pos_unit).count(), 0)

        # HTTP check
        self.client.force_login(self.staff1)
        response = self.client.post(
            reverse("requests:allocate", args=[self.req_a_pos.request_id]),
            {"unit_ids": [o_pos_unit.unit_id]},
            follow=True,
        )
        self.assertContains(response, "needs A+")
        o_pos_unit.refresh_from_db()
        self.assertEqual(o_pos_unit.status, Status.AVAILABLE)

    def test_nfr_s4_concurrent_double_allocation_prevented(self):
        """NFR-S4 / ST-27: Prevention of double allocation on the same blood unit.

        Verifies:
        1. When first request allocates the unit, status becomes RESERVED.
        2. A concurrent/subsequent allocation attempt for the same unit fails because
           the unit is no longer Available.
        3. Under race conditions bypassing application logic, database unique constraint
           'one_live_allocation_per_unit' rejects any simultaneous unreleased allocation.
        """
        donor = make_donor(blood_group="A+")
        shared_unit = make_unit(donor=donor, status=Status.AVAILABLE)

        req_b = make_request(
            self.hospital_user,
            blood_group="A+",
            component_type="Whole Blood",
            quantity_requested=1,
            status=RequestStatus.APPROVED,
        )

        # First allocation succeeds
        allocate_units(self.req_a_pos, [shared_unit.unit_id], by=self.staff1)
        shared_unit.refresh_from_db()
        self.assertEqual(shared_unit.status, Status.RESERVED)

        # Second allocation attempt via workflow is rejected with WorkflowError
        with self.assertRaises(WorkflowError) as cm:
            allocate_units(req_b, [shared_unit.unit_id], by=self.staff2)
        self.assertIn("Reserved", str(cm.exception))

        # Enforce database-level constraint hardening (one_live_allocation_per_unit)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Allocation.objects.create(
                    request=req_b,
                    unit=shared_unit,
                    allocated_by=self.staff2,
                )

        # Exactly 1 active allocation remains for the winning request
        allocations = Allocation.objects.filter(unit=shared_unit, released_at__isnull=True)
        self.assertEqual(allocations.count(), 1)
        self.assertEqual(allocations.first().request, self.req_a_pos)
