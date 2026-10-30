from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from accounts.models import Role, User
from collection.models import ScreeningTest
from collection.services.screening import PANEL
from donors.models import Donor, Eligibility
from inventory.models import BloodUnit, Status


def seed(**options):
    out = StringIO()
    call_command("seed_demo", stdout=out, **options)
    return out.getvalue()


class SeedDemoTests(TestCase):
    """The deterministic fixture the Test Plan environment assumes (SRS NFR-Q6)."""

    def test_it_creates_one_account_per_role_and_the_same_donor_ids_every_time(self):
        seed(password="Demo#Pass2026x")
        self.assertEqual(
            set(User.objects.exclude(role=Role.DONOR).values_list("username", "role")),
            {("staff01", "staff"), ("admin01", "admin"), ("hosp01", "hospital")},
        )
        self.assertEqual(
            list(Donor.objects.values_list("donor_id", flat=True))[:2],
            ["DNR10000001", "DNR10000002"],
        )
        self.assertEqual(Donor.objects.count(), 10)

    def test_the_password_option_is_used_for_every_account(self):
        seed(password="Demo#Pass2026x")
        for user in User.objects.all():
            self.assertTrue(user.check_password("Demo#Pass2026x"), user.username)

    def test_without_the_option_a_strong_random_password_is_printed_and_works(self):
        from django.contrib.auth.password_validation import validate_password

        output = seed()
        password = output.split("Password: ")[1].splitlines()[0]
        validate_password(password)  # meets the same policy as real passwords
        self.assertTrue(User.objects.get(username="admin01").check_password(password))

    def test_running_it_twice_changes_nothing(self):
        seed(password="Demo#Pass2026x")
        before = (User.objects.count(), Donor.objects.count(), BloodUnit.objects.count())
        self.assertIn("already loaded", seed(password="Demo#Pass2026x"))
        self.assertEqual(
            before, (User.objects.count(), Donor.objects.count(), BloodUnit.objects.count())
        )

    @override_settings(ENVIRONMENT="production")
    def test_it_refuses_to_run_in_production(self):
        with self.assertRaises(CommandError):
            seed()
        self.assertEqual(User.objects.count(), 0)

    def test_the_data_covers_the_states_a_demo_needs(self):
        seed(password="Demo#Pass2026x")
        statuses = set(BloodUnit.objects.values_list("status", flat=True))
        self.assertEqual(statuses, {Status.AVAILABLE, Status.QUARANTINED, Status.DISCARDED})
        self.assertTrue(Donor.objects.filter(eligibility_status=Eligibility.ELIGIBLE).exists())
        self.assertTrue(Donor.objects.filter(eligibility_status=Eligibility.TEMPORARY).exists())

    def test_the_seeded_data_obeys_the_safety_rules(self):
        """Every unit that can be issued has a complete, entirely non-reactive panel."""
        seed(password="Demo#Pass2026x")
        for unit in BloodUnit.objects.filter(status=Status.AVAILABLE):
            results = dict(
                ScreeningTest.objects.filter(unit=unit).values_list("test_name", "result")
            )
            self.assertEqual(set(results), set(PANEL), unit.unit_id)
            self.assertEqual(set(results.values()), {"Non-Reactive"}, unit.unit_id)
        for unit in BloodUnit.objects.filter(status=Status.QUARANTINED):
            self.assertEqual(unit.tests.count(), 0)
