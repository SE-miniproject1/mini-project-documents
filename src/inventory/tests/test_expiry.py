from datetime import date, timedelta
from io import StringIO
from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import make_user
from audit.models import AuditEntry, Event
from donors.tests.helpers import PASSWORD, make_donor
from inventory.models import BloodUnit, InvalidTransitionError, Status
from inventory.services.expiry import expire_due_units, near_expiry_units, send_expiry_digest

from .helpers import make_unit

TODAY = date(2026, 10, 28)


def unit_expiring(days_from_today, status=Status.AVAILABLE, **kwargs):
    unit = make_unit(status=status, **kwargs)
    BloodUnit.objects.filter(pk=unit.pk).update(
        expiry_date=TODAY + timedelta(days=days_from_today),
        collection_date=TODAY - timedelta(days=40),
    )
    unit.refresh_from_db()
    return unit


class ExpireDueUnitsTests(TestCase):
    """UT-20 and IT-11 (SRS REQ-19)."""

    def test_a_unit_past_its_expiry_date_becomes_expired_and_others_are_left_alone(self):
        yesterday = unit_expiring(-1)
        today = unit_expiring(0)
        tomorrow = unit_expiring(1)
        self.assertEqual(expire_due_units(TODAY), 1)
        for unit, expected in (
            (yesterday, Status.EXPIRED),
            (today, Status.AVAILABLE),
            (tomorrow, Status.AVAILABLE),
        ):
            unit.refresh_from_db()
            self.assertEqual(unit.status, expected)

    def test_quarantined_and_reserved_units_expire_too(self):
        quarantined = unit_expiring(-2, Status.QUARANTINED)
        reserved = unit_expiring(-2, Status.RESERVED)
        self.assertEqual(expire_due_units(TODAY), 2)
        for unit in (quarantined, reserved):
            unit.refresh_from_db()
            self.assertEqual(unit.status, Status.EXPIRED)

    def test_issued_discarded_and_already_expired_units_are_not_touched(self):
        for status in (Status.ISSUED, Status.DISCARDED, Status.EXPIRED):
            unit_expiring(-5, status)
        self.assertEqual(expire_due_units(TODAY), 0)

    def test_running_it_twice_changes_nothing_the_second_time(self):
        unit_expiring(-1)
        self.assertEqual(expire_due_units(TODAY), 1)
        self.assertEqual(expire_due_units(TODAY), 0)

    def test_expired_units_leave_the_stock_count(self):
        from inventory.services.stock import stock_grid

        unit_expiring(-1)
        unit_expiring(10)
        expire_due_units(TODAY)
        self.assertEqual(stock_grid(TODAY).total, 1)

    def test_each_expiry_is_audited_with_the_reason(self):
        unit = unit_expiring(-1)
        expire_due_units(TODAY)
        entry = AuditEntry.objects.get(
            event=Event.UNIT_STATUS, entity_id=unit.unit_id, new_value="Expired"
        )
        self.assertEqual(entry.reason, "Passed expiry date")
        self.assertIsNone(entry.actor)

    def test_a_unit_that_moved_on_meanwhile_is_skipped_and_the_rest_continue(self):
        first = unit_expiring(-1)
        second = unit_expiring(-1)
        real = BloodUnit.transition_to

        def flaky(self, *args, **kwargs):
            if self.pk == first.pk:
                raise InvalidTransitionError("moved on")
            return real(self, *args, **kwargs)

        with mock.patch.object(BloodUnit, "transition_to", flaky):
            self.assertEqual(expire_due_units(TODAY), 1)
        second.refresh_from_db()
        self.assertEqual(second.status, Status.EXPIRED)


class NearExpiryTests(TestCase):
    """UT-21 (SRS REQ-20): units inside the window are flagged, others are not."""

    def test_units_inside_the_window_are_listed_soonest_first(self):
        unit_expiring(7)
        unit_expiring(3)
        unit_expiring(8)
        unit_expiring(40)
        units = near_expiry_units(TODAY)
        self.assertEqual([u.days_left for u in units], [3, 7])

    def test_a_unit_expiring_today_is_still_flagged_and_an_expired_one_is_not(self):
        unit_expiring(0)
        unit_expiring(-1)
        self.assertEqual([u.days_left for u in near_expiry_units(TODAY)], [0])

    def test_only_available_units_are_flagged(self):
        for status in (Status.QUARANTINED, Status.RESERVED, Status.ISSUED, Status.DISCARDED):
            unit_expiring(2, status)
        self.assertEqual(near_expiry_units(TODAY), [])

    @override_settings(BBMS_NEAR_EXPIRY_DAYS=14)
    def test_the_window_is_configurable(self):
        unit_expiring(10)
        self.assertEqual(len(near_expiry_units(TODAY, window=14)), 1)
        self.assertEqual(len(near_expiry_units(TODAY, window=7)), 0)


class DigestTests(TestCase):
    """IT-11: one digest to staff listing the units about to expire."""

    def setUp(self):
        make_user("staff1", role=Role.STAFF, email="staff1@example.com")
        make_user("admin1", role=Role.ADMIN, email="admin1@example.com")
        make_user("gone", role=Role.STAFF, email="gone@example.com", is_active=False)
        make_user("hosp1", role=Role.HOSPITAL, email="hosp1@example.com")

    def test_one_email_goes_to_active_staff_and_administrators_only(self):
        unit_expiring(5)
        self.assertTrue(send_expiry_digest(TODAY))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(sorted(mail.outbox[0].to), ["admin1@example.com", "staff1@example.com"])

    def test_it_lists_each_unit_with_its_date_and_days_left(self):
        unit = unit_expiring(5)
        send_expiry_digest(TODAY)
        body = mail.outbox[0].body
        self.assertIn(unit.unit_id, body)
        self.assertIn("5 days left", body)
        self.assertIn("02-11-2026", body)

    def test_no_units_means_no_email(self):
        unit_expiring(30)
        self.assertFalse(send_expiry_digest(TODAY))
        self.assertEqual(mail.outbox, [])

    def test_a_mail_failure_is_logged_and_does_not_raise(self):
        unit_expiring(5)
        with (
            mock.patch("inventory.services.expiry.send_mail", side_effect=OSError),
            self.assertLogs("inventory.services.expiry", level="ERROR"),
        ):
            self.assertFalse(send_expiry_digest(TODAY))

    def test_having_no_recipients_is_logged_as_an_error(self):
        from accounts.models import User

        User.objects.filter(role__in=[Role.STAFF, Role.ADMIN]).update(is_active=False)
        unit_expiring(5)
        with self.assertLogs("inventory.services.expiry", level="ERROR"):
            self.assertFalse(send_expiry_digest(TODAY))

    def test_the_daily_command_expires_units_and_sends_the_digest(self):
        today = date.today()
        old = make_unit(status=Status.AVAILABLE)
        soon = make_unit(status=Status.AVAILABLE)
        BloodUnit.objects.filter(pk=old.pk).update(expiry_date=today - timedelta(days=1))
        BloodUnit.objects.filter(pk=soon.pk).update(expiry_date=today + timedelta(days=2))
        out = StringIO()
        call_command("expire_units", stdout=out)
        self.assertIn("1 unit(s) marked Expired.", out.getvalue())
        self.assertIn("digest sent", out.getvalue())
        old.refresh_from_db()
        self.assertEqual(old.status, Status.EXPIRED)
        self.assertEqual(len(mail.outbox), 1)

    def test_the_command_can_skip_the_digest(self):
        out = StringIO()
        call_command("expire_units", "--no-digest", stdout=out)
        self.assertNotIn("digest", out.getvalue().lower())


class ConsoleNearExpiryTests(TestCase):
    """ST-10 and ST-11: staff see what is about to expire, with text and not colour alone."""

    def setUp(self):
        make_user("staff1", role=Role.STAFF)
        self.client.login(username="staff1", password=PASSWORD)

    def test_the_console_lists_units_expiring_soon_with_days_left(self):
        donor = make_donor()
        unit = make_unit(status=Status.AVAILABLE, donor=donor)
        BloodUnit.objects.filter(pk=unit.pk).update(expiry_date=date.today() + timedelta(days=4))
        response = self.client.get(reverse("inventory:console"))
        self.assertContains(response, "Expiring soon")
        self.assertContains(response, unit.unit_id)
        self.assertContains(response, "4 days")
        self.assertContains(response, "1 unit expiring within 7 days")

    def test_with_nothing_expiring_it_says_so_and_shows_no_table(self):
        response = self.client.get(reverse("inventory:console"))
        self.assertContains(response, "None expiring within 7 days")
        self.assertNotContains(response, "Expiring soon")

    def test_the_live_panel_carries_the_near_expiry_count_too(self):
        unit = make_unit(status=Status.AVAILABLE)
        BloodUnit.objects.filter(pk=unit.pk).update(expiry_date=date.today() + timedelta(days=1))
        response = self.client.get(reverse("inventory:console"), {"partial": "1"})
        self.assertContains(response, "1 unit expiring within 7 days")
