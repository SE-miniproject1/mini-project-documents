from datetime import date, timedelta
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import make_user
from donors.models import Eligibility
from donors.services.deferrals import clear_expired_deferrals
from donors.services.eligibility import evaluate_eligibility, record_donation

from .helpers import PASSWORD, make_donor

TODAY = date(2026, 10, 28)


def deferred(**overrides):
    fields = {
        "eligibility_status": Eligibility.TEMPORARY,
        "deferral_reason": "Low haemoglobin",
        "deferral_review_date": TODAY - timedelta(days=1),
    }
    fields.update(overrides)
    return make_donor(**fields)


class ClearDeferralTests(TestCase):
    """IT-04 (SRS REQ-8): a deferral ends by itself once its review date has passed."""

    def test_a_donor_past_the_review_date_returns_to_eligible_and_the_reason_is_cleared(self):
        donor = deferred()
        self.assertEqual(clear_expired_deferrals(TODAY), 1)
        donor.refresh_from_db()
        self.assertEqual(donor.eligibility_status, Eligibility.ELIGIBLE)
        self.assertEqual(donor.deferral_reason, "")
        self.assertIsNone(donor.deferral_review_date)

    def test_a_deferral_that_has_not_reached_its_review_date_is_left_alone(self):
        donor = deferred(deferral_review_date=TODAY + timedelta(days=1))
        self.assertEqual(clear_expired_deferrals(TODAY), 0)
        donor.refresh_from_db()
        self.assertEqual(donor.eligibility_status, Eligibility.TEMPORARY)

    def test_the_review_date_itself_counts_as_passed(self):
        donor = deferred(deferral_review_date=TODAY)
        clear_expired_deferrals(TODAY)
        donor.refresh_from_db()
        self.assertEqual(donor.eligibility_status, Eligibility.ELIGIBLE)

    def test_a_permanent_deferral_is_never_cleared(self):
        donor = make_donor(
            eligibility_status=Eligibility.PERMANENT,
            deferral_reason="Declared condition",
            deferral_review_date=TODAY - timedelta(days=100),
        )
        clear_expired_deferrals(TODAY)
        donor.refresh_from_db()
        self.assertEqual(donor.eligibility_status, Eligibility.PERMANENT)

    def test_a_donor_still_inside_the_interval_stays_deferred_with_a_new_review_date(self):
        donor = deferred(last_donation_date=TODAY - timedelta(days=60))
        clear_expired_deferrals(TODAY)
        donor.refresh_from_db()
        self.assertEqual(donor.eligibility_status, Eligibility.TEMPORARY)
        self.assertEqual(donor.deferral_review_date, TODAY + timedelta(days=30))

    def test_an_old_low_reading_does_not_keep_a_donor_deferred_for_ever(self):
        donor = deferred(haemoglobin=Decimal("10.0"), weight_kg=Decimal("45"))
        clear_expired_deferrals(TODAY)
        donor.refresh_from_db()
        self.assertEqual(donor.eligibility_status, Eligibility.ELIGIBLE)
        # ...but a fresh screening still catches it.
        self.assertFalse(evaluate_eligibility(donor, on=TODAY).eligible)

    def test_inactive_donors_are_ignored(self):
        donor = deferred(is_active=False)
        self.assertEqual(clear_expired_deferrals(TODAY), 0)
        donor.refresh_from_db()
        self.assertEqual(donor.eligibility_status, Eligibility.TEMPORARY)

    def test_the_nightly_command_reports_how_many_were_cleared(self):
        deferred()
        out = StringIO()
        call_command("clear_expired_deferrals", stdout=out)
        self.assertIn("1 donor(s) returned to Eligible", out.getvalue())


class RecordDonationTests(TestCase):
    def test_a_donation_sets_the_next_eligible_date_and_a_deferral_until_then(self):
        donor = make_donor()
        record_donation(donor, TODAY)
        self.assertEqual(donor.last_donation_date, TODAY)
        self.assertEqual(donor.next_eligible_date, TODAY + timedelta(days=90))
        self.assertEqual(donor.eligibility_status, Eligibility.TEMPORARY)
        self.assertEqual(donor.deferral_review_date, donor.next_eligible_date)

    def test_the_donor_is_eligible_again_on_the_next_eligible_date(self):
        donor = make_donor()
        record_donation(donor, TODAY)
        donor.save()
        clear_expired_deferrals(TODAY + timedelta(days=89))
        donor.refresh_from_db()
        self.assertEqual(donor.eligibility_status, Eligibility.TEMPORARY)
        clear_expired_deferrals(TODAY + timedelta(days=90))
        donor.refresh_from_db()
        self.assertEqual(donor.eligibility_status, Eligibility.ELIGIBLE)


class DashboardTests(TestCase):
    """ST-04 (SRS REQ-8, UC2): the donor sees status, next eligible date and days remaining."""

    def _sign_in(self, donor):
        self.client.login(username=donor.donor_id, password=PASSWORD)

    def test_a_donor_who_gave_blood_ten_days_ago_sees_not_eligible_and_the_date(self):
        donor = make_donor(full_name="Recent Donor")
        record_donation(donor, date.today() - timedelta(days=10))
        donor.save()
        self._sign_in(donor)
        response = self.client.get(reverse("donors:dashboard"))
        self.assertContains(response, "Not Eligible")
        self.assertContains(response, f"{donor.next_eligible_date:%d-%m-%Y}")
        self.assertContains(response, "Days remaining")
        self.assertEqual(response.context["days_remaining"], 80)

    def test_an_eligible_donor_sees_they_can_donate(self):
        donor = make_donor()
        self._sign_in(donor)
        response = self.client.get(reverse("donors:dashboard"))
        self.assertContains(response, "Eligible")
        self.assertContains(response, "You can donate now")
        self.assertNotContains(response, "Next eligible date")

    def test_a_deferred_donor_sees_the_reason(self):
        donor = make_donor(
            eligibility_status=Eligibility.TEMPORARY,
            deferral_reason="Underweight",
            deferral_review_date=date.today() + timedelta(days=12),
        )
        self._sign_in(donor)
        response = self.client.get(reverse("donors:dashboard"))
        self.assertContains(response, "Underweight")
        self.assertContains(response, "Review date")

    def test_a_donor_only_ever_sees_their_own_record(self):
        mine = make_donor(full_name="Mine Only")
        other = make_donor(full_name="Someone Else")
        self._sign_in(mine)
        response = self.client.get(reverse("donors:dashboard"))
        self.assertContains(response, mine.donor_id)
        self.assertNotContains(response, other.donor_id)

    def test_staff_and_hospital_users_cannot_use_the_donor_dashboard(self):
        for role in (Role.STAFF, Role.HOSPITAL, Role.ADMIN):
            make_user(role, role=role)
            self.client.login(username=role, password=PASSWORD)
            self.assertEqual(self.client.get(reverse("donors:dashboard")).status_code, 403, role)

    def test_the_dashboard_is_in_the_donor_menu(self):
        donor = make_donor()
        self._sign_in(donor)
        self.assertContains(self.client.get(reverse("home")), "My eligibility")
