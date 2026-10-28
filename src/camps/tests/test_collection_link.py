from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_user
from audit.models import AuditEntry, Event
from camps.models import Camp, CampStatus
from camps.services import CampError, close_camp, create_camp
from collection.models import Donation
from collection.services.collect import record_collection
from collection.services.guard import CollectionBlockedError
from donors.tests.helpers import make_donor

from .test_camps import camp_fields

TODAY = date.today()


def started_camp(user, **overrides):
    """A camp that has already begun, so collections may be recorded against it."""
    camp = create_camp(user, **camp_fields(**overrides))
    Camp.objects.filter(pk=camp.pk).update(camp_date=TODAY)
    camp.refresh_from_db()
    return camp


def collect(donor, staff, site):
    return record_collection(
        donor, volume_ml=450, bag_lot_number="BG-1", collection_site=site, recorded_by=staff
    )


class CampCollectionTests(TestCase):
    """UT-38, UT-39 (SRS REQ-36, REQ-37)."""

    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)
        self.camp = started_camp(self.staff)

    def test_a_unit_collected_at_a_camp_carries_the_camp_as_its_site(self):
        donation, unit = collect(make_donor(), self.staff, self.camp.camp_id)
        self.assertEqual(unit.collection_site, self.camp.camp_id)
        self.assertEqual(donation.collection_site, self.camp.camp_id)

    def test_collection_at_the_centre_is_unchanged(self):
        _, unit = collect(make_donor(), self.staff, "Centre")
        self.assertEqual(unit.collection_site, "Centre")

    def test_an_unknown_site_is_refused(self):
        with self.assertRaisesMessage(CollectionBlockedError, "not the centre or a known camp"):
            collect(make_donor(), self.staff, "Somewhere")
        self.assertEqual(Donation.objects.count(), 0)

    def test_a_camp_that_has_not_started_takes_no_collections(self):
        future = create_camp(self.staff, **camp_fields())
        with self.assertRaisesMessage(CollectionBlockedError, "has not started"):
            collect(make_donor(), self.staff, future.camp_id)

    def test_closing_reports_actuals_against_target_and_blocks_more_collections(self):
        for _ in range(3):
            collect(make_donor(), self.staff, self.camp.camp_id)
        collect(make_donor(), self.staff, "Centre")
        closed = close_camp(self.camp, by=self.staff)
        self.assertEqual(
            (closed.status, closed.units_collected, closed.target_units),
            (CampStatus.COMPLETED, 3, 100),
        )
        donor = make_donor()
        with self.assertRaisesMessage(CollectionBlockedError, "is Completed"):
            collect(donor, self.staff, self.camp.camp_id)
        donor.refresh_from_db()
        self.assertIsNone(donor.last_donation_date)
        entry = AuditEntry.objects.get(event=Event.CONFIG_CHANGE, new_value="Completed")
        self.assertEqual(
            (entry.entity_id, entry.reason), (self.camp.camp_id, "3 of 100 units collected")
        )

    def test_a_camp_with_no_collections_closes_with_zero(self):
        self.assertEqual(close_camp(self.camp, by=self.staff).units_collected, 0)

    def test_a_camp_cannot_be_closed_twice(self):
        close_camp(self.camp, by=self.staff)
        with self.assertRaisesMessage(CampError, "is Completed"):
            close_camp(self.camp, by=self.staff)


class CampCollectionScreenTests(TestCase):
    """ST-19."""

    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)
        self.client.login(username="staff01", password=STRONG_PASSWORD)
        self.camp = started_camp(self.staff)
        self.donor = make_donor()

    def form_data(self, site):
        return {
            "volume_ml": "450",
            "bag_lot_number": "BG-77",
            "collection_site": site,
            "collected_at": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
        }

    def test_the_collection_form_offers_the_centre_and_open_started_camps_only(self):
        future = create_camp(self.staff, **camp_fields(name="Future Drive"))
        url = reverse("collection:new", args=[self.donor.donor_id])
        response = self.client.get(url)
        self.assertContains(response, self.camp.camp_id)
        self.assertNotContains(response, future.camp_id)
        close_camp(self.camp, by=self.staff)
        self.assertNotContains(self.client.get(url), self.camp.camp_id)

    def test_recording_a_camp_collection_through_the_form(self):
        url = reverse("collection:new", args=[self.donor.donor_id])
        response = self.client.post(url, self.form_data(self.camp.camp_id), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Donation.objects.get().collection_site, self.camp.camp_id)

    def test_a_site_outside_the_offered_choices_is_rejected_by_the_form(self):
        url = reverse("collection:new", args=[self.donor.donor_id])
        response = self.client.post(url, self.form_data("Mars"))
        self.assertContains(response, "error-summary")
        self.assertEqual(Donation.objects.count(), 0)

    def test_closing_a_camp_from_its_page_shows_the_result(self):
        collect(make_donor(), self.staff, self.camp.camp_id)
        detail = reverse("camps:detail", args=[self.camp.camp_id])
        self.assertContains(self.client.get(detail), "Close camp and report units collected")
        response = self.client.post(reverse("camps:close", args=[self.camp.camp_id]), follow=True)
        self.assertContains(response, "1 of 100 units collected")
        self.assertContains(response, "1 percent of target")
        self.assertNotContains(response, "Close camp and report")
        again = self.client.post(reverse("camps:close", args=[self.camp.camp_id]), follow=True)
        self.assertContains(again, "is Completed")

    def test_only_staff_can_close_a_camp(self):
        donor = make_donor()
        self.client.logout()
        self.client.login(username=donor.donor_id, password="Blood#Bank2026x")
        self.assertEqual(
            self.client.post(reverse("camps:close", args=[self.camp.camp_id])).status_code, 403
        )
        self.camp.refresh_from_db()
        self.assertEqual(self.camp.status, CampStatus.SCHEDULED)
