from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from accounts.tests.helpers import make_user
from collection.models import Donation
from collection.services.collect import record_collection
from collection.services.guard import CollectionBlockedError
from donors.models import Donor, Eligibility
from donors.tests.helpers import PASSWORD, make_donor
from inventory.models import BloodUnit, Status
from inventory.services.id_generator import UNIT_ID_PATTERN


def collect(donor, staff, **overrides):
    args = {
        "volume_ml": 450,
        "bag_lot_number": "BG-2026-0417",
        "collection_site": "Centre",
        "recorded_by": staff,
    }
    args.update(overrides)
    return record_collection(donor, **args)


class RecordCollectionTests(TestCase):
    """UT-10, UT-08 and IT-05 (SRS REQ-9, REQ-11)."""

    def setUp(self):
        self.staff = make_user("staff1", role=Role.STAFF)

    def test_a_collection_creates_a_donation_and_a_quarantined_unit(self):
        donor = make_donor()
        donation, unit = collect(donor, self.staff)
        self.assertEqual(unit.status, Status.QUARANTINED)
        self.assertRegex(unit.unit_id, UNIT_ID_PATTERN.pattern)
        self.assertEqual(donation.unit, unit)
        self.assertEqual(donation.recorded_by, self.staff)
        self.assertEqual(
            (unit.volume_ml, unit.bag_lot_number, unit.collection_site),
            (450, "BG-2026-0417", "Centre"),
        )
        self.assertEqual(unit.blood_group, donor.blood_group)
        self.assertEqual(unit.donor, donor)

    def test_the_expiry_date_comes_from_the_component_shelf_life(self):
        _, unit = collect(make_donor(), self.staff)
        self.assertEqual(unit.expiry_date, unit.collection_date + timedelta(days=35))

    def test_the_donor_s_last_and_next_dates_are_updated_and_they_wait_out_the_interval(self):
        donor = make_donor()
        _, unit = collect(donor, self.staff)
        donor.refresh_from_db()
        self.assertEqual(donor.last_donation_date, unit.collection_date)
        self.assertEqual(donor.next_eligible_date, unit.collection_date + timedelta(days=90))
        self.assertEqual(donor.eligibility_status, Eligibility.TEMPORARY)

    def test_a_deferred_donor_is_refused_and_no_unit_is_created(self):
        donor = make_donor(
            eligibility_status=Eligibility.TEMPORARY,
            deferral_reason="Low haemoglobin",
            deferral_review_date=timezone.localdate() + timedelta(days=10),
        )
        with self.assertRaises(CollectionBlockedError) as raised:
            collect(donor, self.staff)
        self.assertEqual(raised.exception.reason, "Low haemoglobin")
        self.assertEqual(BloodUnit.objects.count(), 0)
        self.assertEqual(Donation.objects.count(), 0)

    def test_a_second_collection_for_the_same_donor_is_refused(self):
        """The first collection defers the donor, so a second person cannot bleed them again."""
        donor = make_donor()
        collect(donor, self.staff)
        with self.assertRaises(CollectionBlockedError):
            collect(donor, self.staff)
        self.assertEqual(BloodUnit.objects.count(), 1)

    def test_a_past_collection_time_sets_the_dates_from_that_day(self):
        when = timezone.now() - timedelta(days=2)
        _, unit = collect(make_donor(), self.staff, collected_at=when)
        self.assertEqual(unit.collection_date, timezone.localtime(when).date())

    def test_a_failure_part_way_leaves_nothing_behind(self):
        from unittest import mock

        donor = make_donor()
        with mock.patch(
            "collection.services.collect.Donation.objects.create", side_effect=RuntimeError
        ):
            with self.assertRaises(RuntimeError):
                collect(donor, self.staff)
        self.assertEqual(BloodUnit.objects.count(), 0)
        donor.refresh_from_db()
        self.assertIsNone(donor.last_donation_date)


class CollectionScreenTests(TestCase):
    """ST-05, ST-07 and IT-03 (SRS REQ-9, REQ-10, REQ-7)."""

    def setUp(self):
        self.staff = make_user("staff1", role=Role.STAFF)
        self.client.login(username="staff1", password=PASSWORD)
        self.donor = make_donor(full_name="Meena Rao")
        self.url = reverse("collection:new", args=[self.donor.donor_id])

    def _post(self, **data):
        body = {
            "volume_ml": "450",
            "bag_lot_number": "BG-2026-0417",
            "collection_site": "Centre",
            "collected_at": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
        }
        body.update(data)
        return self.client.post(self.url, body, follow=True)

    def test_an_eligible_donor_gets_the_form(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Record a donation")
        self.assertContains(response, "Meena Rao")

    def test_saving_shows_the_unit_id_status_and_expiry(self):
        response = self._post()
        unit = BloodUnit.objects.get()
        self.assertContains(response, "Donation recorded")
        self.assertContains(response, unit.unit_id)
        self.assertContains(response, "Quarantined")
        self.assertContains(response, f"{unit.expiry_date:%d-%m-%Y}")

    def test_the_search_screen_offers_start_collection_to_an_eligible_donor(self):
        response = self.client.get(reverse("donors:search"))
        self.assertContains(response, f'href="{self.url}"')

    def test_the_search_screen_disables_it_with_the_reason_for_a_deferred_donor(self):
        Donor.objects.filter(pk=self.donor.pk).update(
            eligibility_status=Eligibility.TEMPORARY, deferral_reason="Low haemoglobin"
        )
        response = self.client.get(reverse("donors:search"))
        self.assertNotContains(response, f'href="{self.url}"')
        self.assertContains(response, 'aria-disabled="true">Start collection')
        self.assertContains(response, "Low haemoglobin.")

    def test_a_deferred_donor_sees_why_and_no_form(self):
        Donor.objects.filter(pk=self.donor.pk).update(
            eligibility_status=Eligibility.TEMPORARY,
            deferral_reason="Low haemoglobin",
            deferral_review_date=timezone.localdate() + timedelta(days=9),
        )
        response = self.client.get(self.url)
        self.assertContains(response, "Collection not allowed")
        self.assertContains(response, "Low haemoglobin. Review on")
        self.assertNotContains(response, "Save donation")

    def test_a_blocked_donor_cannot_be_collected_from_by_posting_directly(self):
        Donor.objects.filter(pk=self.donor.pk).update(eligibility_status=Eligibility.PERMANENT)
        response = self._post()
        self.assertContains(response, "Collection not allowed")
        self.assertEqual(BloodUnit.objects.count(), 0)

    def test_invalid_entries_show_messages_and_create_nothing(self):
        response = self._post(volume_ml="50", bag_lot_number="bad lot!")
        self.assertContains(
            response, "Volume collected (ml): Volume must be between 200 and 600 ml."
        )
        self.assertContains(response, "Bag lot number: Use letters, digits and hyphens only.")
        self.assertEqual(BloodUnit.objects.count(), 0)

    def test_the_collection_time_cannot_be_in_the_future(self):
        later = (timezone.localtime() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        self.assertContains(self._post(collected_at=later), "cannot be in the future")
        self.assertEqual(BloodUnit.objects.count(), 0)

    def test_an_unknown_donor_gives_not_found(self):
        self.assertEqual(
            self.client.get(reverse("collection:new", args=["DNR00000000"])).status_code, 404
        )

    def test_only_staff_and_administrators_may_record_a_donation(self):
        for role in (Role.DONOR, Role.HOSPITAL):
            make_user(role, role=role)
            self.client.login(username=role, password=PASSWORD)
            self.assertEqual(self.client.get(self.url).status_code, 403, role)
            self.assertEqual(self.client.post(self.url, {}).status_code, 403, role)
        self.assertEqual(BloodUnit.objects.count(), 0)

    def test_the_screening_result_offers_collection_to_an_eligible_donor(self):
        from donors.models import DonorScreening

        screening = DonorScreening.objects.create(
            donor=self.donor,
            screened_by=self.staff,
            weight_kg=62,
            haemoglobin=13.5,
            systolic_bp=120,
            outcome="Eligible",
        )
        response = self.client.get(reverse("donors:screening_result", args=[screening.pk]))
        self.assertContains(response, "Start collection")
