from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from core.models import IdSequence
from donors.forms import DonorRegistrationForm
from donors.models import Donor, Eligibility
from donors.services.id_generator import DONOR_ID_PATTERN, generate_donor_id

from .helpers import PASSWORD, make_donor, registration_data

REGISTER = "donors:register"


class DonorIdTests(TestCase):
    """UT-02 (SRS REQ-2): unique, immutable DNR + 8 digit identifiers."""

    def test_a_thousand_identifiers_are_distinct_and_well_formed(self):
        ids = [generate_donor_id() for _ in range(1000)]
        self.assertEqual(len(set(ids)), 1000)
        self.assertTrue(all(DONOR_ID_PATTERN.match(i) for i in ids))

    def test_numbering_starts_at_10000001_and_counts_up(self):
        self.assertEqual(generate_donor_id(), "DNR10000001")
        self.assertEqual(generate_donor_id(), "DNR10000002")

    def test_a_donor_identifier_cannot_be_changed(self):
        donor = make_donor()
        donor = Donor.objects.get(pk=donor.pk)
        donor.donor_id = "DNR99999999"
        with self.assertRaises(ValueError):
            donor.save()

    def test_sequences_are_independent_per_name(self):
        self.assertEqual(IdSequence.next_value("a", 5), 5)
        self.assertEqual(IdSequence.next_value("a", 5), 6)
        self.assertEqual(IdSequence.next_value("b", 100), 100)


class RegistrationFormTests(TestCase):
    """UT-01 (SRS REQ-1)."""

    def test_a_complete_valid_form_creates_one_donor_with_the_submitted_values(self):
        form = DonorRegistrationForm(registration_data())
        self.assertTrue(form.is_valid(), form.errors)
        donor = form.save()
        self.assertEqual(Donor.objects.count(), 1)
        donor.refresh_from_db()
        self.assertEqual(donor.full_name, "Ravi Kumar")
        self.assertEqual(donor.blood_group, "O+")
        self.assertEqual(donor.mobile_number, "9880011223")
        self.assertEqual(donor.city, "Bengaluru")
        self.assertEqual(float(donor.weight_kg), 68.0)
        self.assertEqual(donor.eligibility_status, Eligibility.ELIGIBLE)
        self.assertTrue(DONOR_ID_PATTERN.match(donor.donor_id))

    def test_every_required_field_is_enforced(self):
        required = [k for k in registration_data() if k not in {"password2"}]
        for field in required:
            data = registration_data()
            data.pop(field)
            form = DonorRegistrationForm(data)
            self.assertFalse(form.is_valid(), field)
            self.assertIn(field, form.errors)

    def test_consent_is_required_and_recorded_with_a_timestamp(self):
        form = DonorRegistrationForm(registration_data(consent=""))
        self.assertFalse(form.is_valid())
        self.assertIn("You must give consent to register.", form.errors["consent"])
        donor = DonorRegistrationForm(registration_data())
        donor.is_valid()
        self.assertIsNotNone(donor.save().consent_timestamp)

    def test_formats_are_checked(self):
        for field, value in (
            ("mobile_number", "12345"),
            ("mobile_number", "98800abcde"),
            ("pin_code", "56008"),
            ("emergency_contact_number", "123"),
            ("weight_kg", "0"),
            ("weight_kg", "400"),
            ("gender", "Unknown"),
            ("blood_group", "C+"),
            ("email", "not-an-email"),
        ):
            form = DonorRegistrationForm(registration_data(**{field: value}))
            self.assertFalse(form.is_valid(), f"{field}={value}")

    def test_passwords_must_match_and_follow_the_policy(self):
        mismatch = DonorRegistrationForm(registration_data(password2="Different#Pass1"))
        self.assertFalse(mismatch.is_valid())
        self.assertIn("password2", mismatch.errors)
        weak = DonorRegistrationForm(registration_data(password1="weakpass", password2="weakpass"))
        self.assertFalse(weak.is_valid())
        self.assertIn("password1", weak.errors)

    def test_the_form_cannot_be_saved_without_committing(self):
        form = DonorRegistrationForm(registration_data())
        form.is_valid()
        with self.assertRaises(ValueError):
            form.save(commit=False)


class RegistrationFlowTests(TestCase):
    """IT-01 and ST-01 (SRS REQ-1, REQ-2, UC-1)."""

    def test_the_registration_page_is_public(self):
        self.assertEqual(self.client.get(reverse(REGISTER)).status_code, 200)

    def test_registration_creates_donor_account_and_consent_then_shows_the_id(self):
        response = self.client.post(reverse(REGISTER), registration_data(), follow=True)
        donor = Donor.objects.get()
        user = User.objects.get(username=donor.donor_id)
        self.assertEqual(user.role, Role.DONOR)
        self.assertEqual(donor.user, user)
        self.assertEqual(user.get_full_name(), "Ravi Kumar")
        self.assertContains(response, "Registration successful")
        self.assertContains(response, donor.donor_id)
        self.assertRegex(donor.donor_id, r"^DNR\d{8}$")

    def test_a_welcome_email_is_sent_to_the_donor(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse(REGISTER), registration_data())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ravi.k@example.com"])
        self.assertIn(Donor.objects.get().donor_id, mail.outbox[0].body)

    def test_a_failed_welcome_email_does_not_undo_the_registration(self):
        with (
            self.settings(EMAIL_BACKEND="django.core.mail.backends.dummy.NoSuchBackend"),
            self.assertLogs("donors.notifications", level="ERROR"),
        ):
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(reverse(REGISTER), registration_data())
        self.assertEqual(Donor.objects.count(), 1)

    def test_the_new_donor_can_sign_in_with_the_donor_id_as_username(self):
        self.client.post(reverse(REGISTER), registration_data())
        donor = Donor.objects.get()
        self.assertTrue(self.client.login(username=donor.donor_id, password=PASSWORD))

    def test_the_confirmation_page_needs_a_fresh_registration(self):
        self.assertRedirects(
            self.client.get(reverse("donors:registered")), reverse("accounts:login")
        )
        self.client.post(reverse(REGISTER), registration_data())
        self.client.get(reverse("donors:registered"))
        again = self.client.get(reverse("donors:registered"))
        self.assertEqual(again.status_code, 302)

    def test_the_identifier_is_not_put_in_the_address(self):
        response = self.client.post(reverse(REGISTER), registration_data())
        self.assertNotIn("DNR", response["Location"])

    def test_errors_show_beside_the_fields_and_nothing_is_saved(self):
        response = self.client.post(
            reverse(REGISTER), registration_data(mobile_number="12", consent="")
        )
        self.assertContains(response, "Mobile number: Enter a 10-digit number.")
        self.assertEqual(Donor.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)

    def test_a_signed_in_user_is_sent_home_instead(self):
        donor = make_donor()
        self.client.login(username=donor.donor_id, password=PASSWORD)
        self.assertRedirects(self.client.get(reverse(REGISTER)), reverse("home"))

    def test_the_numbers_are_not_reused_after_a_rejected_registration(self):
        self.client.post(reverse(REGISTER), registration_data(mobile_number="12"))
        self.client.post(reverse(REGISTER), registration_data())
        self.assertEqual(Donor.objects.get().donor_id, "DNR10000001")
