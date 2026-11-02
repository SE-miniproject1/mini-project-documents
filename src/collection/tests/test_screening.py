from datetime import date, timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import make_user
from collection.models import ScreeningTest, TestName
from collection.services.screening import (
    PANEL,
    ResultAlreadyRecordedError,
    ScreeningIncompleteError,
    UnitNotQuarantinedError,
    record_results,
    release_unit,
)
from donors.tests.helpers import PASSWORD
from inventory.models import BloodUnit, InvalidTransitionError, Status
from inventory.tests.helpers import make_unit

ALL_CLEAR = dict.fromkeys(PANEL, "Non-Reactive")


class RecordResultsTests(TestCase):
    """UT-13 to UT-15 (SRS REQ-12, REQ-13, REQ-14, NFR-S1)."""

    def setUp(self):
        self.staff = make_user("staff1", role=Role.STAFF)
        self.unit = make_unit()

    def test_the_mandatory_panel_is_the_five_tests_in_the_srs(self):
        self.assertEqual(PANEL, ("HIV", "HBV", "HCV", "Syphilis", "Malaria"))

    def test_an_incomplete_panel_cannot_be_released_and_the_missing_test_is_named(self):
        record_results(self.unit, {k: "Non-Reactive" for k in PANEL[:4]}, by=self.staff)
        with self.assertRaises(ScreeningIncompleteError) as raised:
            release_unit(self.unit, by=self.staff)
        self.assertEqual(raised.exception.missing, ("Malaria",))
        self.assertIn("Missing results: Malaria.", str(raised.exception))
        self.assertEqual(BloodUnit.objects.get(pk=self.unit.pk).status, Status.QUARANTINED)

    def test_no_results_at_all_names_every_test(self):
        with self.assertRaises(ScreeningIncompleteError) as raised:
            release_unit(self.unit, by=self.staff)
        self.assertEqual(raised.exception.missing, PANEL)

    def test_a_complete_non_reactive_panel_releases_the_unit_to_inventory(self):
        record_results(self.unit, ALL_CLEAR, by=self.staff)
        outcome = release_unit(self.unit, by=self.staff)
        self.assertTrue(outcome.released)
        stored = BloodUnit.objects.get(pk=self.unit.pk)
        self.assertEqual(stored.status, Status.AVAILABLE)
        self.assertEqual(stored.storage_location, "FRIDGE-A1")
        self.assertEqual(BloodUnit.objects.issuable().count(), 1)

    def test_results_can_be_entered_over_several_visits(self):
        record_results(self.unit, {"HIV": "Non-Reactive", "HBV": "Non-Reactive"}, by=self.staff)
        record_results(self.unit, {k: "Non-Reactive" for k in PANEL[2:]}, by=self.staff)
        self.assertTrue(release_unit(self.unit, by=self.staff).released)

    def test_one_reactive_result_discards_the_unit_at_once_with_the_reason(self):
        record_results(self.unit, {"HCV": "Reactive"}, by=self.staff)
        stored = BloodUnit.objects.get(pk=self.unit.pk)
        self.assertEqual(stored.status, Status.DISCARDED)
        self.assertEqual(stored.discard_reason, "Reactive Screening")

    def test_a_reactive_unit_can_never_be_restored(self):
        record_results(self.unit, {"HCV": "Reactive", "HIV": "Non-Reactive"}, by=self.staff)
        unit = BloodUnit.objects.get(pk=self.unit.pk)
        for target in (Status.AVAILABLE, Status.RESERVED, Status.ISSUED):
            with self.assertRaises(InvalidTransitionError):
                unit.transition_to(target)
        with self.assertRaises(UnitNotQuarantinedError):
            release_unit(unit, by=self.staff)
        self.assertEqual(BloodUnit.objects.issuable().count(), 0)

    def test_four_clear_and_one_reactive_still_discards(self):
        record_results(self.unit, {**ALL_CLEAR, "HCV": "Reactive"}, by=self.staff)
        self.assertEqual(BloodUnit.objects.get(pk=self.unit.pk).status, Status.DISCARDED)

    def test_a_recorded_result_is_final(self):
        record_results(self.unit, {"HIV": "Non-Reactive"}, by=self.staff)
        with self.assertRaises(ResultAlreadyRecordedError):
            record_results(self.unit, {"HIV": "Reactive"}, by=self.staff)
        self.assertEqual(ScreeningTest.objects.get().result, "Non-Reactive")
        test = ScreeningTest.objects.get()
        test.result = "Reactive"
        with self.assertRaises(ValueError):
            test.save()

    def test_unknown_tests_and_results_are_rejected(self):
        with self.assertRaises(ValueError):
            record_results(self.unit, {"Dengue": "Non-Reactive"}, by=self.staff)
        with self.assertRaises(ValueError):
            record_results(self.unit, {"HIV": "Maybe"}, by=self.staff)
        self.assertEqual(ScreeningTest.objects.count(), 0)

    def test_a_bad_entry_saves_none_of_the_batch(self):
        with self.assertRaises(ValueError):
            record_results(self.unit, {"HIV": "Non-Reactive", "HBV": "Maybe"}, by=self.staff)
        self.assertEqual(ScreeningTest.objects.count(), 0)

    def test_results_cannot_be_entered_for_a_unit_that_is_not_quarantined(self):
        released = make_unit(status=Status.AVAILABLE)
        with self.assertRaises(UnitNotQuarantinedError):
            record_results(released, {"HIV": "Reactive"}, by=self.staff)
        self.assertEqual(BloodUnit.objects.get(pk=released.pk).status, Status.AVAILABLE)

    def test_a_unit_that_expired_while_waiting_is_never_released(self):
        """NFR-S2."""
        record_results(self.unit, ALL_CLEAR, by=self.staff)
        BloodUnit.objects.filter(pk=self.unit.pk).update(
            expiry_date=date.today() - timedelta(days=1)
        )
        outcome = release_unit(self.unit, by=self.staff)
        self.assertFalse(outcome.released)
        self.assertEqual(BloodUnit.objects.get(pk=self.unit.pk).status, Status.EXPIRED)
        self.assertEqual(BloodUnit.objects.issuable().count(), 0)


class AdministratorAlertTests(TestCase):
    """IT-08 and ST-07 (SRS REQ-14): the donor's identity goes to administrators only."""

    def setUp(self):
        self.staff = make_user("staff1", role=Role.STAFF)
        self.admin = make_user("admin1", role=Role.ADMIN, email="admin1@example.com")
        make_user("hosp1", role=Role.HOSPITAL, email="hosp1@example.com")
        make_user("gone", role=Role.ADMIN, email="gone@example.com", is_active=False)
        self.unit = make_unit()

    def _reactive(self):
        with self.captureOnCommitCallbacks(execute=True):
            record_results(self.unit, {"HIV": "Reactive"}, by=self.staff)

    def test_only_active_administrators_are_alerted(self):
        self._reactive()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin1@example.com"])

    def test_the_alert_names_the_unit_the_test_and_the_donor(self):
        self._reactive()
        body = mail.outbox[0].body
        self.assertIn(self.unit.unit_id, body)
        self.assertIn("HIV", body)
        self.assertIn(self.unit.donor.full_name, body)
        self.assertIn("CONFIDENTIAL", body)

    def test_no_alert_goes_to_staff_or_hospital_users(self):
        self._reactive()
        for message in mail.outbox:
            self.assertNotIn("staff1@example.com", message.to)
            self.assertNotIn("hosp1@example.com", message.to)

    def test_a_clear_result_sends_no_alert(self):
        with self.captureOnCommitCallbacks(execute=True):
            record_results(self.unit, ALL_CLEAR, by=self.staff)
            release_unit(self.unit, by=self.staff)
        self.assertEqual(mail.outbox, [])

    def test_a_mail_failure_does_not_undo_the_discard(self):
        with (
            mock.patch("collection.services.screening.send_mail", side_effect=OSError),
            self.assertLogs("collection.services.screening", level="ERROR"),
        ):
            self._reactive()
        self.assertEqual(BloodUnit.objects.get(pk=self.unit.pk).status, Status.DISCARDED)

    def test_having_no_administrator_is_logged_not_ignored(self):
        self.admin.is_active = False
        self.admin.save()
        with self.assertLogs("collection.services.screening", level="ERROR") as logs:
            self._reactive()
        self.assertIn("no administrator", logs.output[0])
        self.assertEqual(BloodUnit.objects.get(pk=self.unit.pk).status, Status.DISCARDED)


class ResultsScreenTests(TestCase):
    """ST-06, ST-07 and IT-07: entering results through the screen."""

    def setUp(self):
        make_user("staff1", role=Role.STAFF)
        self.client.login(username="staff1", password=PASSWORD)
        self.unit = make_unit()
        self.url = reverse("collection:results", args=[self.unit.unit_id])

    def _post(self, action, **results):
        data = {"tested_on": date.today().isoformat(), "action": action}
        data.update(results)
        return self.client.post(self.url, data, follow=True)

    def test_the_screen_shows_all_five_tests_and_the_unit(self):
        response = self.client.get(self.url)
        self.assertContains(response, self.unit.unit_id)
        for label in ("HIV", "Hepatitis B", "Hepatitis C", "Syphilis", "Malaria"):
            self.assertContains(response, label)
        self.assertContains(response, "Release to inventory")

    def test_releasing_with_malaria_blank_is_refused_and_the_unit_stays_quarantined(self):
        response = self._post(
            "release",
            HIV="Non-Reactive",
            HBV="Non-Reactive",
            HCV="Non-Reactive",
            Syphilis="Non-Reactive",
        )
        self.assertContains(response, "Missing results: Malaria.")
        self.assertEqual(BloodUnit.objects.get(pk=self.unit.pk).status, Status.QUARANTINED)
        self.assertEqual(ScreeningTest.objects.count(), 4)

    def test_a_full_non_reactive_panel_released_from_the_screen_makes_the_unit_available(self):
        response = self._post("release", **ALL_CLEAR)
        self.assertContains(response, "The unit was released to inventory.")
        self.assertEqual(BloodUnit.objects.get(pk=self.unit.pk).status, Status.AVAILABLE)

    def test_saving_without_releasing_keeps_the_unit_quarantined(self):
        response = self._post("save", HIV="Non-Reactive")
        self.assertContains(response, "Results saved.")
        self.assertEqual(BloodUnit.objects.get(pk=self.unit.pk).status, Status.QUARANTINED)

    def test_a_reactive_result_discards_the_unit_and_says_so(self):
        response = self._post("save", HBV="Reactive")
        self.assertContains(response, "The unit is discarded and can never be issued.")
        self.assertContains(response, "Reactive Screening")
        self.assertEqual(BloodUnit.objects.get(pk=self.unit.pk).status, Status.DISCARDED)

    def test_a_decided_unit_shows_its_results_read_only(self):
        self._post("release", **ALL_CLEAR)
        response = self.client.get(self.url)
        self.assertNotContains(response, "Release to inventory")
        self.assertContains(response, "Non-Reactive")

    def test_a_future_test_date_is_refused(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        response = self.client.post(
            self.url, {"tested_on": tomorrow, "action": "save", "HIV": "Non-Reactive"}
        )
        self.assertContains(response, "The test date cannot be in the future.")
        self.assertEqual(ScreeningTest.objects.count(), 0)

    def test_a_result_for_an_already_recorded_test_is_not_offered_again(self):
        self._post("save", HIV="Non-Reactive")
        response = self.client.get(self.url)
        self.assertNotContains(response, 'name="HIV"')

    def test_only_staff_and_administrators_may_enter_results(self):
        for role in (Role.DONOR, Role.HOSPITAL):
            make_user(role, role=role)
            self.client.login(username=role, password=PASSWORD)
            self.assertEqual(self.client.get(self.url).status_code, 403, role)
            self.assertEqual(
                self.client.post(self.url, {"action": "release"}).status_code, 403, role
            )
        self.assertEqual(BloodUnit.objects.get(pk=self.unit.pk).status, Status.QUARANTINED)

    def test_the_confirmation_page_links_to_the_results_screen(self):
        response = self.client.get(reverse("collection:confirmation", args=[self.unit.unit_id]))
        self.assertContains(response, self.url)

    def test_test_names_in_the_panel_match_the_model_choices(self):
        self.assertEqual(set(PANEL), set(TestName.values))
