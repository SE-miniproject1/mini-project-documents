from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core import checks
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import make_user
from donors.models import DonorScreening, Eligibility
from donors.services.eligibility import (
    apply_result,
    apply_screening,
    evaluate_eligibility,
    next_eligible_date,
)

from .helpers import PASSWORD, make_donor, registration_data, years_ago

TODAY = date(2026, 10, 28)


def donor_for(**overrides):
    """A donor who meets every criterion unless a field is overridden."""
    fields = {
        "date_of_birth": date(1996, 10, 28),
        "weight_kg": Decimal("62"),
        "haemoglobin": Decimal("13.8"),
        "last_donation_date": TODAY - timedelta(days=120),
    }
    fields.update(overrides)
    return make_donor(**fields)


def codes(result):
    return sorted(failure.code for failure in result.failures)


class EngineTests(TestCase):
    """UT-06 and UT-07 (SRS REQ-6)."""

    def test_a_donor_who_meets_every_criterion_is_eligible(self):
        result = evaluate_eligibility(donor_for(), systolic_bp=118, on=TODAY)
        self.assertEqual(result.status, Eligibility.ELIGIBLE)
        self.assertEqual(result.failures, ())
        self.assertTrue(result.eligible)
        self.assertIsNone(result.review_date)

    def test_every_failing_criterion_is_reported_not_only_the_first(self):
        donor = donor_for(last_donation_date=TODAY - timedelta(days=30))
        result = evaluate_eligibility(
            donor, weight_kg=Decimal("45"), haemoglobin=Decimal("10.2"), systolic_bp=118, on=TODAY
        )
        self.assertEqual(result.status, Eligibility.TEMPORARY)
        self.assertEqual(codes(result), ["interval", "low_haemoglobin", "underweight"])
        self.assertEqual(len(result.reasons), 3)

    def test_all_five_criteria_can_fail_together(self):
        donor = donor_for(
            date_of_birth=years_ago(17, TODAY) + timedelta(days=1),
            last_donation_date=TODAY - timedelta(days=10),
        )
        result = evaluate_eligibility(
            donor, weight_kg=Decimal("40"), haemoglobin=Decimal("9"), systolic_bp=80, on=TODAY
        )
        self.assertEqual(
            codes(result),
            ["age_under", "blood_pressure", "interval", "low_haemoglobin", "underweight"],
        )

    def test_weight_boundary(self):
        for weight, passes in (
            (Decimal("50"), True),
            (Decimal("49.9"), False),
            (Decimal("49.99"), False),
        ):
            result = evaluate_eligibility(donor_for(), weight_kg=weight, systolic_bp=120, on=TODAY)
            self.assertEqual(result.eligible, passes, weight)

    def test_haemoglobin_boundary_is_exact(self):
        for value, passes in (
            (Decimal("12.5"), True),
            (Decimal("12.4"), False),
            (Decimal("12.499"), False),
        ):
            result = evaluate_eligibility(
                donor_for(), haemoglobin=value, systolic_bp=120, on=TODAY
            )
            self.assertEqual(result.eligible, passes, value)

    def test_blood_pressure_boundaries(self):
        for systolic, passes in ((100, True), (99, False), (140, True), (141, False)):
            result = evaluate_eligibility(donor_for(), systolic_bp=systolic, on=TODAY)
            self.assertEqual(result.eligible, passes, systolic)

    def test_the_donation_interval_boundary(self):
        for days, passes in ((90, True), (89, False), (91, True)):
            donor = donor_for(last_donation_date=TODAY - timedelta(days=days))
            self.assertEqual(
                evaluate_eligibility(donor, systolic_bp=120, on=TODAY).eligible, passes
            )

    def test_a_first_time_donor_has_no_interval_to_wait(self):
        donor = donor_for(last_donation_date=None)
        self.assertTrue(evaluate_eligibility(donor, systolic_bp=120, on=TODAY).eligible)

    def test_age_boundaries(self):
        for years, expected in ((18, Eligibility.ELIGIBLE), (65, Eligibility.ELIGIBLE)):
            donor = donor_for(date_of_birth=years_ago(years, TODAY))
            self.assertEqual(
                evaluate_eligibility(donor, systolic_bp=120, on=TODAY).status, expected
            )
        under = donor_for(date_of_birth=years_ago(18, TODAY) + timedelta(days=1))
        self.assertEqual(
            evaluate_eligibility(under, systolic_bp=120, on=TODAY).status, Eligibility.TEMPORARY
        )

    def test_a_donor_under_18_may_return_on_their_18th_birthday(self):
        birthday = years_ago(18, TODAY) + timedelta(days=40)
        result = evaluate_eligibility(donor_for(date_of_birth=birthday), systolic_bp=120, on=TODAY)
        self.assertEqual(
            result.review_date, date(birthday.year + 18, birthday.month, birthday.day)
        )

    def test_a_donor_over_65_is_permanently_ineligible(self):
        donor = donor_for(date_of_birth=years_ago(66, TODAY))
        result = evaluate_eligibility(donor, systolic_bp=120, on=TODAY)
        self.assertEqual(result.status, Eligibility.PERMANENT)
        self.assertIsNone(result.review_date)

    def test_unmeasured_values_are_skipped_not_assumed(self):
        donor = donor_for(haemoglobin=None)
        result = evaluate_eligibility(donor, on=TODAY)  # no Hb and no blood pressure
        self.assertTrue(result.eligible)

    def test_a_permanent_deferral_is_never_lifted_by_good_measurements(self):
        donor = donor_for(
            eligibility_status=Eligibility.PERMANENT, deferral_reason="Declared condition"
        )
        result = evaluate_eligibility(donor, systolic_bp=120, on=TODAY)
        self.assertEqual(result.status, Eligibility.PERMANENT)
        self.assertIn("Declared condition", result.reasons[0])

    def test_the_review_date_is_the_latest_of_the_failing_criteria(self):
        donor = donor_for(last_donation_date=TODAY - timedelta(days=80))
        result = evaluate_eligibility(donor, weight_kg=Decimal("45"), systolic_bp=120, on=TODAY)
        # Interval clears in 10 days, the weight deferral lasts 30 days.
        self.assertEqual(result.review_date, TODAY + timedelta(days=30))

    def test_the_interval_alone_clears_on_the_next_eligible_date(self):
        donor = donor_for(last_donation_date=TODAY - timedelta(days=30))
        result = evaluate_eligibility(donor, systolic_bp=120, on=TODAY)
        self.assertEqual(result.review_date, TODAY + timedelta(days=60))


class NextEligibleDateTests(TestCase):
    """UT-09 (SRS REQ-8): last donation plus the configured interval."""

    def test_ninety_days_after_the_last_donation(self):
        self.assertEqual(next_eligible_date(date(2026, 6, 1)), date(2026, 8, 30))

    def test_no_donation_gives_no_date(self):
        self.assertIsNone(next_eligible_date(None))

    def test_a_longer_configured_interval_is_used(self):
        longer = {**settings.BBMS_ELIGIBILITY, "donation_interval_days": 120}
        with override_settings(BBMS_ELIGIBILITY=longer):
            self.assertEqual(next_eligible_date(date(2026, 6, 1)), date(2026, 9, 29))

    def test_the_interval_can_never_be_set_below_ninety_days(self):
        too_short = {**settings.BBMS_ELIGIBILITY, "donation_interval_days": 60}
        with override_settings(BBMS_ELIGIBILITY=too_short):
            errors = checks.run_checks()
        self.assertIn("donors.E001", [error.id for error in errors])


class ApplyTests(TestCase):
    def test_apply_result_records_status_reason_and_review_date(self):
        donor = donor_for()
        result = evaluate_eligibility(donor, weight_kg=Decimal("45"), systolic_bp=120, on=TODAY)
        apply_result(donor, result)
        self.assertEqual(donor.eligibility_status, Eligibility.TEMPORARY)
        self.assertEqual(donor.deferral_reason, "Underweight")
        self.assertEqual(donor.deferral_review_date, TODAY + timedelta(days=30))

    def test_a_clean_result_clears_an_earlier_deferral(self):
        donor = donor_for(
            eligibility_status=Eligibility.TEMPORARY,
            deferral_reason="Low haemoglobin",
            deferral_review_date=TODAY,
        )
        apply_result(donor, evaluate_eligibility(donor, systolic_bp=120, on=TODAY))
        self.assertEqual(donor.eligibility_status, Eligibility.ELIGIBLE)
        self.assertEqual(donor.deferral_reason, "")
        self.assertIsNone(donor.deferral_review_date)

    def test_the_stored_reason_always_fits_its_column(self):
        donor = donor_for(
            date_of_birth=years_ago(17, TODAY) + timedelta(days=1),
            last_donation_date=TODAY - timedelta(days=5),
        )
        result = evaluate_eligibility(
            donor, weight_kg=Decimal("40"), haemoglobin=Decimal("9"), systolic_bp=70, on=TODAY
        )
        self.assertLessEqual(len(result.short_reason), 100)

    def test_apply_screening_updates_the_donor_and_keeps_a_record(self):
        donor = donor_for()
        staff = make_user("s1", role=Role.STAFF)
        screening, result = apply_screening(
            donor,
            weight_kg=Decimal("46"),
            haemoglobin=Decimal("10.5"),
            systolic_bp=120,
            screened_by=staff,
            on=TODAY,
        )
        donor.refresh_from_db()
        self.assertEqual(donor.eligibility_status, Eligibility.TEMPORARY)
        self.assertEqual(donor.weight_kg, Decimal("46.0"))
        self.assertEqual(screening.screened_by, staff)
        self.assertEqual(DonorScreening.objects.count(), 1)
        self.assertEqual(len(result.failures), 2)


class RegistrationEligibilityTests(TestCase):
    def test_an_underweight_registrant_starts_temporarily_deferred(self):
        self.client.post(reverse("donors:register"), registration_data(weight_kg="45"))
        from donors.models import Donor

        donor = Donor.objects.get()
        self.assertEqual(donor.eligibility_status, Eligibility.TEMPORARY)
        self.assertEqual(donor.deferral_reason, "Underweight")

    def test_a_registrant_who_meets_what_can_be_checked_is_eligible(self):
        self.client.post(reverse("donors:register"), registration_data())
        from donors.models import Donor

        self.assertEqual(Donor.objects.get().eligibility_status, Eligibility.ELIGIBLE)


class ScreeningScreenTests(TestCase):
    """IT-02 and ST-03: staff enter measurements and see the outcome."""

    def setUp(self):
        self.donor = make_donor(
            full_name="Meena Rao", last_donation_date=date.today() - timedelta(days=200)
        )
        make_user("staff1", role=Role.STAFF)
        self.client.login(username="staff1", password=PASSWORD)
        self.url = reverse("donors:screen", args=[self.donor.donor_id])

    def _post(self, **data):
        body = {"weight_kg": "62", "haemoglobin": "13.5", "systolic_bp": "120"}
        body.update(data)
        return self.client.post(self.url, body, follow=True)

    def test_the_form_shows_the_donor(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Meena Rao")
        self.assertContains(response, self.donor.donor_id)

    def test_a_low_haemoglobin_defers_the_donor_with_a_review_date(self):
        response = self._post(haemoglobin="11.0")
        self.donor.refresh_from_db()
        self.assertEqual(self.donor.eligibility_status, Eligibility.TEMPORARY)
        self.assertEqual(self.donor.deferral_reason, "Low haemoglobin")
        self.assertIsNotNone(self.donor.deferral_review_date)
        self.assertContains(response, "Temporarily Deferred")
        self.assertContains(response, "Haemoglobin 11.0 g/dL is below the minimum")

    def test_two_failures_list_both_reasons_and_a_review_date(self):
        response = self._post(weight_kg="46", haemoglobin="10.5")
        self.assertContains(response, "Weight 46 kg is below the minimum")
        self.assertContains(response, "Haemoglobin 10.5 g/dL is below the minimum")
        self.assertContains(response, "Review on")

    def test_a_passing_screening_says_every_criterion_is_met(self):
        self.assertContains(self._post(), "Every criterion is met.")

    def test_invalid_measurements_are_rejected_with_a_message(self):
        response = self._post(haemoglobin="abc", systolic_bp="5")
        self.assertContains(response, "Haemoglobin (g/dL): ")
        self.assertContains(response, "Systolic blood pressure (mmHg): ")
        self.assertEqual(DonorScreening.objects.count(), 0)

    def test_the_result_page_survives_a_refresh_without_repeating_the_screening(self):
        response = self.client.post(
            self.url, {"weight_kg": "62", "haemoglobin": "13.5", "systolic_bp": "120"}
        )
        self.client.get(response["Location"])
        self.client.get(response["Location"])
        self.assertEqual(DonorScreening.objects.count(), 1)

    def test_only_staff_and_administrators_may_screen(self):
        for role in (Role.DONOR, Role.HOSPITAL):
            make_user(role, role=role)
            self.client.login(username=role, password=PASSWORD)
            self.assertEqual(self.client.get(self.url).status_code, 403, role)
            self.assertEqual(self.client.post(self.url, {}).status_code, 403, role)

    def test_an_unknown_donor_gives_not_found(self):
        self.assertEqual(
            self.client.get(reverse("donors:screen", args=["DNR00000000"])).status_code, 404
        )


class SearchTests(TestCase):
    """UT-/ST- donor search (SRS UC4): by ID, mobile number or name."""

    def setUp(self):
        self.a = make_donor(full_name="Anita Desai", mobile_number="9111111111")
        self.b = make_donor(full_name="Bharat Shah", mobile_number="9222222222")
        make_user("staff1", role=Role.STAFF)
        self.client.login(username="staff1", password=PASSWORD)

    def _names(self, query=""):
        response = self.client.get(reverse("donors:search"), {"q": query})
        return [donor.full_name for donor in response.context["page"]]

    def test_no_query_lists_everyone(self):
        self.assertEqual(self._names(), ["Anita Desai", "Bharat Shah"])

    def test_search_by_name_id_and_mobile(self):
        self.assertEqual(self._names("desai"), ["Anita Desai"])
        self.assertEqual(self._names(self.b.donor_id), ["Bharat Shah"])
        self.assertEqual(self._names("9222"), ["Bharat Shah"])

    def test_no_match_says_so(self):
        response = self.client.get(reverse("donors:search"), {"q": "zzz"})
        self.assertContains(response, "No donors match.")

    def test_columns_sort_and_the_page_size_is_25(self):
        for _ in range(30):
            make_donor()
        response = self.client.get(reverse("donors:search"), {"sort": "name", "dir": "desc"})
        self.assertEqual(len(response.context["page"]), 25)
        names = [d.full_name for d in response.context["page"]]
        self.assertEqual(names, sorted(names, reverse=True))

    def test_inactive_donors_are_not_listed(self):
        self.a.is_active = False
        self.a.save()
        self.assertEqual(self._names(), ["Bharat Shah"])

    def test_only_staff_and_administrators_may_search(self):
        make_user("donor1", role=Role.DONOR)
        self.client.login(username="donor1", password=PASSWORD)
        self.assertEqual(self.client.get(reverse("donors:search")).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("donors:search")).status_code, 302)
