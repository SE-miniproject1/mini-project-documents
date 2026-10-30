from datetime import date, timedelta

from django.test import TestCase

from accounts.models import Role
from accounts.tests.helpers import make_user
from collection.services.guard import CollectionBlockedError, collection_status, ensure_can_collect
from donors.models import Eligibility
from donors.tests.helpers import PASSWORD, make_donor

TODAY = date(2026, 10, 28)


class GuardTests(TestCase):
    """UT-08 (SRS REQ-7): nothing is collected from a donor who is not eligible."""

    def test_an_eligible_donor_may_donate(self):
        ensure_can_collect(make_donor(), TODAY)  # does not raise

    def test_a_deferred_donor_is_refused_with_the_reason_and_review_date(self):
        donor = make_donor(
            eligibility_status=Eligibility.TEMPORARY,
            deferral_reason="Low haemoglobin",
            deferral_review_date=date(2026, 11, 20),
        )
        with self.assertRaises(CollectionBlockedError) as raised:
            ensure_can_collect(donor, TODAY)
        self.assertEqual(raised.exception.reason, "Low haemoglobin")
        self.assertEqual(raised.exception.review_date, date(2026, 11, 20))
        self.assertEqual(str(raised.exception), "Low haemoglobin. Review on 20-11-2026.")

    def test_a_permanently_deferred_donor_is_refused_with_no_review_date(self):
        donor = make_donor(
            eligibility_status=Eligibility.PERMANENT, deferral_reason="Declared condition"
        )
        with self.assertRaises(CollectionBlockedError) as raised:
            ensure_can_collect(donor, TODAY)
        self.assertIsNone(raised.exception.review_date)

    def test_a_deactivated_donor_is_refused(self):
        with self.assertRaises(CollectionBlockedError):
            ensure_can_collect(make_donor(is_active=False), TODAY)

    def test_the_interval_is_enforced_even_when_the_status_says_eligible(self):
        """NFR-S5: a stale status must not allow a donor to be bled too soon."""
        donor = make_donor(last_donation_date=TODAY - timedelta(days=30))
        self.assertEqual(donor.eligibility_status, Eligibility.ELIGIBLE)
        with self.assertRaises(CollectionBlockedError) as raised:
            ensure_can_collect(donor, TODAY)
        self.assertIn("30 days", raised.exception.reason)
        self.assertEqual(raised.exception.review_date, TODAY + timedelta(days=60))

    def test_exactly_ninety_days_after_the_last_donation_is_allowed(self):
        ensure_can_collect(make_donor(last_donation_date=TODAY - timedelta(days=90)), TODAY)
        with self.assertRaises(CollectionBlockedError):
            ensure_can_collect(make_donor(last_donation_date=TODAY - timedelta(days=89)), TODAY)

    def test_collection_status_gives_a_yes_or_a_reason_for_the_screen(self):
        self.assertEqual(collection_status(make_donor(), TODAY), (True, ""))
        deferred = make_donor(
            eligibility_status=Eligibility.TEMPORARY, deferral_reason="Underweight"
        )
        allowed, note = collection_status(deferred, TODAY)
        self.assertFalse(allowed)
        self.assertEqual(note, "Underweight.")


class SearchControlTests(TestCase):
    """IT-03: the Start Collection control is disabled for a deferred donor, with the reason."""

    def setUp(self):
        make_user("staff1", role=Role.STAFF)
        self.client.login(username="staff1", password=PASSWORD)

    def test_the_screen_works_for_eligible_and_deferred_donors(self):
        make_donor(full_name="Eligible Person")
        make_donor(
            full_name="Deferred Person",
            eligibility_status=Eligibility.TEMPORARY,
            deferral_reason="Low haemoglobin",
        )
        from django.urls import reverse

        response = self.client.get(reverse("donors:search"))
        by_name = {d.full_name: d for d in response.context["page"]}
        self.assertTrue(by_name["Eligible Person"].can_collect)
        self.assertFalse(by_name["Deferred Person"].can_collect)
        self.assertEqual(by_name["Deferred Person"].collect_note, "Low haemoglobin.")
