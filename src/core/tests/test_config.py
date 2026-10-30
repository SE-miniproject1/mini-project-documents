from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_user
from audit.models import AuditEntry, Event
from core import config
from core.forms import ConfigForm
from core.models import ConfigValue
from donors.services.eligibility import next_eligible_date, rules
from inventory.services.shelf_life import expiry_date_for


def full_post(**overrides):
    """A valid configuration form with every field at its current value, plus overrides."""
    data = {ConfigForm.field_name(k): v for k, v in config.current_values().items()}
    data.update({ConfigForm.field_name(k): v for k, v in overrides.items()})
    return data


class ConfigServiceTests(TestCase):
    """REQ-46, NFR-Q10: no code change or restart."""

    def test_defaults_come_from_settings_until_overridden(self):
        self.assertEqual(rules()["donation_interval_days"], 90)
        self.assertEqual(config.near_expiry_days(), 7)
        self.assertEqual(config.shelf_life_days("PRBC"), 42)
        self.assertEqual(config.min_stock("O-"), 0)

    def test_an_override_applies_to_the_next_call(self):
        admin = make_user("admin1", Role.ADMIN)
        config.save(
            {
                "eligibility.donation_interval_days": 120,
                "eligibility.min_haemoglobin": Decimal("13.0"),
                "shelf_life.PRBC": 35,
                "near_expiry_days": 3,
                "min_stock.O-": 10,
            },
            by=admin,
        )
        self.assertEqual(next_eligible_date(date(2026, 1, 1)), date(2026, 5, 1))
        self.assertEqual(rules()["min_haemoglobin"], Decimal("13.0"))
        self.assertEqual(expiry_date_for("PRBC", date(2026, 1, 1)), date(2026, 2, 5))
        self.assertEqual(config.near_expiry_days(), 3)
        self.assertEqual(config.min_stock("O-"), 10)

    def test_only_real_changes_are_stored_and_audited_with_before_and_after(self):
        admin = make_user("admin1", Role.ADMIN)
        changed = config.save({"near_expiry_days": 7, "shelf_life.FFP": 300}, by=admin)
        self.assertEqual(changed, ["shelf_life.FFP"])
        entry = AuditEntry.objects.get(event=Event.CONFIG_CHANGE)
        self.assertEqual(
            (entry.entity_id, entry.previous_value, entry.new_value, entry.actor),
            ("shelf_life.FFP", "365", "300", admin),
        )

    def test_a_garbled_stored_value_falls_back_to_the_default(self):
        ConfigValue.objects.create(key="near_expiry_days", value="abc")
        self.assertEqual(config.near_expiry_days(), 7)

    def test_validation_enforces_ranges_and_the_ninety_day_floor(self):
        problems = config.validate(
            {
                "eligibility.donation_interval_days": 60,
                "eligibility.min_systolic": 130,
                "eligibility.max_systolic": 125,
            }
        )
        self.assertEqual(
            set(problems),
            {
                "eligibility.donation_interval_days",
                "eligibility.max_systolic",
            },
        )
        self.assertEqual(config.validate({"near_expiry_days": 7}), {})


class ConfigScreenTests(TestCase):
    """UC18."""

    def setUp(self):
        self.admin = make_user("admin1", Role.ADMIN)
        self.client.login(username="admin1", password=STRONG_PASSWORD)
        self.url = reverse("config:settings")

    def test_only_administrators_can_open_it(self):
        for role in (Role.STAFF, Role.HOSPITAL, Role.DONOR):
            make_user(f"u_{role}", role)
            self.client.logout()
            self.client.login(username=f"u_{role}", password=STRONG_PASSWORD)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.client.post(self.url, full_post()).status_code, 403)
        self.assertFalse(ConfigValue.objects.exists())

    def test_the_form_shows_current_values_and_is_in_the_menu(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Near-expiry window (days)")
        self.assertContains(response, "Minimum stock, AB+ (units)")
        self.assertContains(response, 'href="/config/"')

    def test_saving_changes_applies_and_reports(self):
        response = self.client.post(self.url, full_post(near_expiry_days=14), follow=True)
        self.assertContains(response, "1 setting changed")
        self.assertEqual(config.near_expiry_days(), 14)

    def test_saving_with_no_changes_says_so(self):
        response = self.client.post(self.url, full_post(), follow=True)
        self.assertContains(response, "No settings were changed")

    def test_invalid_values_are_rejected_without_saving_anything(self):
        data = full_post(**{"near_expiry_days": 14, "eligibility.donation_interval_days": 60})
        response = self.client.post(self.url, data)
        self.assertContains(response, "Enter a value from 90 to 365")
        self.assertFalse(ConfigValue.objects.exists())

    def test_the_pressure_limits_must_not_cross(self):
        data = full_post(**{"eligibility.min_systolic": 125, "eligibility.max_systolic": 120})
        self.assertContains(self.client.post(self.url, data), "Must be above the minimum pressure")
