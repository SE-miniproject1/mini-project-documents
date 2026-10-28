from datetime import date, timedelta
from unittest import mock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from donors.models import Donor
from donors.validators import (
    AGE_MESSAGE,
    DUPLICATE_EMAIL_MESSAGE,
    DUPLICATE_MOBILE_MESSAGE,
    age_on,
    validate_age,
)

from .helpers import make_donor, registration_data, years_ago

REGISTER = "donors:register"


class AgeRuleTests(TestCase):
    """UT-04 (SRS REQ-4): at least 18 and at most 65 on the day of registration."""

    def test_the_boundaries_are_inclusive_at_18_and_65(self):
        today = date(2026, 10, 28)
        accepted = {
            "just 18": date(2008, 10, 28),
            "40": date(1986, 10, 28),
            "65 today": date(1961, 10, 28),
            "65 and 364 days": date(1960, 10, 29),
        }
        for label, dob in accepted.items():
            validate_age(dob, today)  # must not raise
            self.assertIn(age_on(dob, today), (18, 40, 65), label)

    def test_just_under_18_and_just_over_65_are_rejected(self):
        today = date(2026, 10, 28)
        for label, dob in {
            "17 and 364 days": date(2008, 10, 29),
            "newborn": today,
            "66": date(1960, 10, 28),
            "in the future": today + timedelta(days=1),
        }.items():
            with self.assertRaises(ValidationError, msg=label) as raised:
                validate_age(dob, today)
            self.assertEqual(raised.exception.messages, [AGE_MESSAGE])

    def test_the_message_is_the_one_in_the_srs(self):
        self.assertEqual(AGE_MESSAGE, "Donors must be between 18 and 65 years of age.")

    def test_a_leap_day_birthday_is_handled(self):
        self.assertEqual(age_on(date(2000, 2, 29), date(2026, 2, 28)), 25)
        self.assertEqual(age_on(date(2000, 2, 29), date(2026, 3, 1)), 26)

    def test_the_form_rejects_a_donor_who_is_too_young_or_too_old(self):
        for years in (16, 66, 90):
            response = self.client.post(
                reverse(REGISTER), registration_data(date_of_birth=years_ago(years))
            )
            self.assertContains(response, f"Date of birth: {AGE_MESSAGE}")
        self.assertEqual(Donor.objects.count(), 0)


class DuplicateTests(TestCase):
    """UT-03 (SRS REQ-3): a mobile number or email already on an active donor is refused."""

    def setUp(self):
        self.existing = make_donor(mobile_number="9880011223", email="ravi.k@example.com")

    def test_a_duplicate_mobile_number_is_refused_with_the_srs_message(self):
        before = (Donor.objects.count(), User.objects.count())
        response = self.client.post(
            reverse(REGISTER), registration_data(email="other@example.com")
        )
        self.assertContains(response, f"Mobile number: {DUPLICATE_MOBILE_MESSAGE}")
        self.assertEqual((Donor.objects.count(), User.objects.count()), before)

    def test_a_duplicate_email_is_refused_ignoring_case(self):
        response = self.client.post(
            reverse(REGISTER),
            registration_data(mobile_number="9000000001", email="RAVI.K@Example.com"),
        )
        self.assertContains(response, f"Email: {DUPLICATE_EMAIL_MESSAGE}")

    def test_an_email_used_by_any_sign_in_account_is_refused(self):
        User.objects.create_user("staff1", "staffer@example.com", "x", role="staff")
        response = self.client.post(
            reverse(REGISTER),
            registration_data(mobile_number="9000000002", email="staffer@example.com"),
        )
        self.assertContains(response, DUPLICATE_EMAIL_MESSAGE)

    def test_a_deactivated_donor_does_not_block_a_new_registration(self):
        Donor.objects.filter(pk=self.existing.pk).update(is_active=False)
        self.client.post(reverse(REGISTER), registration_data(email="fresh@example.com"))
        self.assertEqual(Donor.objects.filter(is_active=True).count(), 1)

    def test_unique_distinct_details_register_normally(self):
        response = self.client.post(
            reverse(REGISTER),
            registration_data(mobile_number="9000000003", email="new@example.com"),
        )
        self.assertRedirects(response, reverse("donors:registered"))

    def test_the_database_constraint_backs_the_check_up_when_two_requests_race(self):
        # Simulate the second of two simultaneous requests passing the form check.
        with (
            mock.patch("donors.forms.ensure_mobile_unused"),
            mock.patch("donors.forms.ensure_email_unused"),
        ):
            before = (Donor.objects.count(), User.objects.count())
            response = self.client.post(
                reverse(REGISTER), registration_data(email="race@example.com")
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "These details could not be saved")
        self.assertEqual((Donor.objects.count(), User.objects.count()), before)


class RejectedRegistrationTests(TestCase):
    """IT-01 second half and ST-02: invalid input leaves no trace and every error is shown."""

    def test_three_problems_give_three_field_errors_and_a_summary_with_no_account(self):
        make_donor(mobile_number="9880011223", email="taken@example.com")
        before = (Donor.objects.count(), User.objects.count())
        response = self.client.post(
            reverse(REGISTER),
            registration_data(date_of_birth=years_ago(16), pin_code="56008"),
        )
        html = response.content.decode()
        summary = html[
            html.index('class="error-summary"') : html.index('<form method="post" novalidate')
        ]
        for message in (
            f"Date of birth: {AGE_MESSAGE}",
            f"Mobile number: {DUPLICATE_MOBILE_MESSAGE}",
            "PIN code: Enter a 6-digit PIN code.",
        ):
            self.assertIn(message, summary)
            self.assertContains(response, 'class="field-error"')
        self.assertEqual((Donor.objects.count(), User.objects.count()), before)
