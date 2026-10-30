from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import make_user
from collection.services.guard import CollectionBlockedError, ensure_can_collect
from donors.models import (
    ConditionKind,
    DeferralCondition,
    Donor,
    DonorDeclaration,
    Eligibility,
)
from donors.services.eligibility import evaluate_eligibility

from .helpers import PASSWORD, make_donor, registration_data

TODAY = date(2026, 10, 28)


def condition(name):
    return DeferralCondition.objects.get(name=name)


class ConditionListTests(TestCase):
    """SRS REQ-5: a configured list of permanent and temporary deferral conditions."""

    def test_a_starting_list_of_both_kinds_is_loaded(self):
        kinds = set(DeferralCondition.objects.values_list("kind", flat=True))
        self.assertEqual(kinds, {ConditionKind.PERMANENT, ConditionKind.TEMPORARY})
        self.assertGreaterEqual(DeferralCondition.objects.count(), 10)

    def test_a_temporary_condition_must_say_how_long_and_a_permanent_one_must_not(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            DeferralCondition.objects.create(name="No days", kind="temporary")
        with self.assertRaises(IntegrityError), transaction.atomic():
            DeferralCondition.objects.create(
                name="Days on permanent", kind="permanent", deferral_days=5
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            DeferralCondition.objects.create(name="Zero days", kind="temporary", deferral_days=0)

    def test_a_donor_cannot_declare_the_same_condition_twice(self):
        donor = make_donor()
        DonorDeclaration.objects.create(donor=donor, condition=condition("Taking antibiotics"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            DonorDeclaration.objects.create(donor=donor, condition=condition("Taking antibiotics"))


class EngineWithDeclarationsTests(TestCase):
    """UT-05 (SRS REQ-5)."""

    def setUp(self):
        self.donor = make_donor(date_of_birth=date(1996, 10, 28), weight_kg=62, haemoglobin=13.8)

    def test_no_declaration_leaves_an_eligible_donor_eligible(self):
        self.assertTrue(evaluate_eligibility(self.donor, on=TODAY).eligible)

    def test_a_permanent_condition_defers_for_good_with_no_review_date(self):
        result = evaluate_eligibility(self.donor, on=TODAY, declared=[condition("HIV positive")])
        self.assertEqual(result.status, Eligibility.PERMANENT)
        self.assertIsNone(result.review_date)
        self.assertEqual(result.short_reason, "HIV positive")

    def test_a_temporary_condition_defers_for_its_number_of_days(self):
        result = evaluate_eligibility(
            self.donor, on=TODAY, declared=[condition("Vaccination in the last 4 weeks")]
        )
        self.assertEqual(result.status, Eligibility.TEMPORARY)
        self.assertEqual(result.review_date, TODAY + timedelta(days=28))

    def test_the_longest_temporary_condition_sets_the_review_date(self):
        result = evaluate_eligibility(
            self.donor,
            on=TODAY,
            declared=[condition("Taking antibiotics"), condition("Surgery in the last 6 months")],
        )
        self.assertEqual(result.review_date, TODAY + timedelta(days=180))
        self.assertEqual(len(result.failures), 2)

    def test_a_permanent_condition_wins_over_temporary_ones(self):
        result = evaluate_eligibility(
            self.donor,
            on=TODAY,
            declared=[condition("Taking antibiotics"), condition("Epilepsy")],
        )
        self.assertEqual(result.status, Eligibility.PERMANENT)
        self.assertEqual(len(result.failures), 2)

    def test_declarations_add_to_failed_measurements(self):
        result = evaluate_eligibility(
            self.donor, weight_kg=45, on=TODAY, declared=[condition("Taking antibiotics")]
        )
        self.assertEqual({f.code for f in result.failures}, {"underweight", "declared_temporary"})

    def test_many_conditions_still_fit_the_stored_reason(self):
        every = list(DeferralCondition.objects.all())
        result = evaluate_eligibility(self.donor, on=TODAY, declared=every)
        self.assertLessEqual(len(result.short_reason), 100)


class RegistrationDeclarationTests(TestCase):
    """SRS REQ-5 at registration."""

    def _register(self, *names, **extra):
        data = registration_data(**extra)
        data["declared_conditions"] = [condition(n).pk for n in names]
        return self.client.post(reverse("donors:register"), data)

    def test_the_conditions_are_offered_on_the_form(self):
        response = self.client.get(reverse("donors:register"))
        self.assertContains(response, "Do any of these apply to you?")
        self.assertContains(response, "HIV positive")

    def test_a_retired_condition_is_not_offered(self):
        DeferralCondition.objects.filter(name="Epilepsy").update(is_active=False)
        self.assertNotContains(self.client.get(reverse("donors:register")), "Epilepsy")

    def test_declaring_nothing_registers_an_eligible_donor(self):
        self._register()
        self.assertEqual(Donor.objects.get().eligibility_status, Eligibility.ELIGIBLE)
        self.assertEqual(DonorDeclaration.objects.count(), 0)

    def test_a_permanent_condition_registers_the_donor_as_permanently_deferred(self):
        self._register("Heart disease")
        donor = Donor.objects.get()
        self.assertEqual(donor.eligibility_status, Eligibility.PERMANENT)
        self.assertEqual(donor.deferral_reason, "Heart disease")
        self.assertIsNone(donor.deferral_review_date)
        self.assertEqual(DonorDeclaration.objects.get().condition.name, "Heart disease")

    def test_a_temporary_condition_registers_the_donor_as_temporarily_deferred(self):
        self._register("Tattoo or piercing in the last 6 months")
        donor = Donor.objects.get()
        self.assertEqual(donor.eligibility_status, Eligibility.TEMPORARY)
        self.assertEqual(donor.deferral_review_date, date.today() + timedelta(days=180))

    def test_a_deferred_donor_cannot_donate(self):
        self._register("Epilepsy")
        with self.assertRaises(CollectionBlockedError):
            ensure_can_collect(Donor.objects.get())

    def test_a_rejected_registration_records_no_declaration(self):
        self._register("Epilepsy", mobile_number="12")
        self.assertEqual(DonorDeclaration.objects.count(), 0)


class ScreeningDeclarationTests(TestCase):
    """Staff record a condition the donor mentions at screening."""

    def setUp(self):
        self.staff = make_user("staff1", role=Role.STAFF)
        self.client.login(username="staff1", password=PASSWORD)
        self.donor = make_donor()
        self.url = reverse("donors:screen", args=[self.donor.donor_id])

    def _post(self, *names):
        data = {"weight_kg": "62", "haemoglobin": "13.5", "systolic_bp": "120"}
        data["declared_conditions"] = [condition(n).pk for n in names]
        return self.client.post(self.url, data, follow=True)

    def test_a_declared_permanent_condition_defers_the_donor_even_with_good_measurements(self):
        response = self._post("Hepatitis B or C")
        self.donor.refresh_from_db()
        self.assertEqual(self.donor.eligibility_status, Eligibility.PERMANENT)
        self.assertContains(response, "Permanently Deferred")
        self.assertContains(response, "Declared condition: Hepatitis B or C")

    def test_the_declaration_is_kept_with_who_recorded_it(self):
        self._post("Taking antibiotics")
        declaration = DonorDeclaration.objects.get()
        self.assertEqual(declaration.recorded_by, self.staff)
        self.assertEqual(declaration.donor, self.donor)

    def test_a_later_clean_screening_does_not_lift_a_permanent_deferral(self):
        self._post("Cancer")
        self._post()
        self.donor.refresh_from_db()
        self.assertEqual(self.donor.eligibility_status, Eligibility.PERMANENT)

    def test_the_screening_form_offers_the_conditions(self):
        self.assertContains(self.client.get(self.url), "Conditions the donor declares")
