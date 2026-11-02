import re
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.permissions import _deny
from accounts.tests.helpers import make_user
from audit.models import AuditEntry, AuditImmutableError, Event
from audit.services import record_event
from donors.tests.helpers import PASSWORD
from inventory.models import InvalidTransitionError, Status
from inventory.tests.helpers import make_unit


class UnitStatusAuditTests(TestCase):
    """UT-24 and IT-13 (SRS REQ-23): every unit transition leaves a complete entry."""

    def setUp(self):
        self.staff = make_user("staff1", role=Role.STAFF)

    def test_a_transition_records_who_what_when_and_why(self):
        unit = make_unit()
        before = AuditEntry.objects.count()
        unit.transition_to(Status.DISCARDED, by=self.staff, reason="Breakage")
        entry = AuditEntry.objects.first()
        self.assertEqual(AuditEntry.objects.count(), before + 1)
        self.assertEqual(entry.event, Event.UNIT_STATUS)
        self.assertEqual(entry.entity_id, unit.unit_id)
        self.assertEqual((entry.previous_value, entry.new_value), ("Quarantined", "Discarded"))
        self.assertEqual(entry.actor, self.staff)
        self.assertEqual(entry.actor_username, "staff1")
        self.assertEqual(entry.reason, "Breakage")
        self.assertIsNotNone(entry.occurred_at)

    def test_three_transitions_give_three_entries_in_order(self):
        unit = make_unit()
        for step in (Status.AVAILABLE, Status.RESERVED, Status.ISSUED):
            unit.transition_to(step, by=self.staff)
        steps = [
            (e.previous_value, e.new_value)
            for e in AuditEntry.objects.filter(
                entity_id=unit.unit_id, event=Event.UNIT_STATUS
            ).order_by("pk")
        ]
        self.assertEqual(
            steps,
            [("Quarantined", "Available"), ("Available", "Reserved"), ("Reserved", "Issued")],
        )

    def test_a_refused_transition_leaves_no_entry(self):
        unit = make_unit()
        before = AuditEntry.objects.count()
        with self.assertRaises(InvalidTransitionError):
            unit.transition_to(Status.ISSUED)
        self.assertEqual(AuditEntry.objects.count(), before)

    def test_if_the_audit_write_fails_the_status_change_is_undone(self):
        unit = make_unit()
        with mock.patch("audit.receivers.record_event", side_effect=RuntimeError("log down")):
            with self.assertRaises(RuntimeError):
                unit.transition_to(Status.AVAILABLE, by=self.staff)
        unit.refresh_from_db()
        self.assertEqual(unit.status, Status.QUARANTINED)

    def test_the_source_address_comes_from_the_request(self):
        client = Client(REMOTE_ADDR="203.0.113.7")
        client.post(reverse("accounts:login"), {"username": "staff1", "password": PASSWORD})
        entry = AuditEntry.objects.get(event=Event.LOGIN_SUCCESS)
        self.assertEqual(entry.source_ip, "203.0.113.7")

    def test_a_status_change_made_during_a_request_carries_that_requests_address(self):
        unit = make_unit()
        client = Client(REMOTE_ADDR="198.51.100.9")
        client.login(username="staff1", password=PASSWORD)
        with mock.patch("audit.context.current_request") as current:
            current.return_value = type("R", (), {"META": {"REMOTE_ADDR": "198.51.100.9"}})()
            unit.transition_to(Status.AVAILABLE, by=self.staff)
        self.assertEqual(
            AuditEntry.objects.get(event=Event.UNIT_STATUS, entity_id=unit.unit_id).source_ip,
            "198.51.100.9",
        )


class ImmutabilityTests(TestCase):
    """SEC-OBJ-2: nobody can edit or remove an entry."""

    def setUp(self):
        self.entry = record_event(Event.CONFIG_CHANGE, entity_type="Setting", entity_id="x")

    def test_an_entry_cannot_be_edited(self):
        self.entry.reason = "changed"
        with self.assertRaises(AuditImmutableError):
            self.entry.save()

    def test_an_entry_cannot_be_deleted(self):
        with self.assertRaises(AuditImmutableError):
            self.entry.delete()

    def test_bulk_update_and_delete_are_refused(self):
        with self.assertRaises(AuditImmutableError):
            AuditEntry.objects.update(reason="x")
        with self.assertRaises(AuditImmutableError):
            AuditEntry.objects.all().delete()
        self.assertEqual(AuditEntry.objects.count(), 1)

    def test_the_admin_offers_no_way_to_change_or_delete(self):
        from django.contrib.admin.sites import site

        model_admin = site._registry[AuditEntry]
        request = type("R", (), {"user": make_user("a1", role=Role.ADMIN)})()
        for permission in (
            model_admin.has_add_permission,
            model_admin.has_change_permission,
            model_admin.has_delete_permission,
        ):
            self.assertFalse(permission(request))

    def test_no_application_code_updates_or_deletes_audit_entries(self):
        root = Path(__file__).resolve().parents[2]
        pattern = re.compile(r"AuditEntry\.objects[^\n]*\.(update|delete)\(")
        offenders = [
            str(p.relative_to(root))
            for p in root.rglob("*.py")
            if "tests" not in p.parts
            and "migrations" not in p.parts
            and pattern.search(p.read_text())
        ]
        self.assertEqual(offenders, [])


class AuthenticationAuditTests(TestCase):
    """NFR-SEC10: every authentication event, authorisation failure and lockout is recorded."""

    def setUp(self):
        self.user = make_user("alice", role=Role.DONOR)

    def _events(self, event):
        return AuditEntry.objects.filter(event=event)

    def test_sign_in_and_sign_out_are_recorded(self):
        self.client.post(reverse("accounts:login"), {"username": "alice", "password": PASSWORD})
        self.assertEqual(self._events(Event.LOGIN_SUCCESS).get().actor, self.user)
        self.client.post(reverse("accounts:logout"))
        self.assertEqual(self._events(Event.LOGOUT).get().actor, self.user)

    def test_a_failed_sign_in_is_recorded_with_the_name_tried_but_never_the_password(self):
        self.client.post(
            reverse("accounts:login"), {"username": "alice", "password": "Wrong#Pass99"}
        )
        entry = self._events(Event.LOGIN_FAILURE).get()
        self.assertEqual(entry.actor_username, "alice")
        for field in ("reason", "entity_id", "actor_username", "new_value"):
            self.assertNotIn("Wrong#Pass99", getattr(entry, field))

    def test_a_failed_sign_in_for_an_unknown_user_is_still_recorded(self):
        self.client.post(reverse("accounts:login"), {"username": "ghost", "password": "x"})
        self.assertEqual(self._events(Event.LOGIN_FAILURE).get().actor_username, "ghost")

    def test_a_lockout_is_recorded(self):
        for _ in range(5):
            self.client.post(reverse("accounts:login"), {"username": "alice", "password": "bad"})
        self.assertEqual(self._events(Event.LOCKOUT).count(), 1)

    def test_an_authorisation_failure_is_recorded_with_the_path(self):
        self.client.login(username="alice", password=PASSWORD)
        self.client.get(reverse("inventory:console"))
        entry = self._events(Event.AUTHZ_FAILURE).get()
        self.assertEqual(entry.actor, self.user)
        self.assertEqual(entry.entity_id, "/inventory/")

    def test_an_anonymous_authorisation_failure_has_no_user(self):
        request = RequestFactory().get("/x/")
        request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            _deny(request, ["admin"])
        self.assertIsNone(self._events(Event.AUTHZ_FAILURE).get().actor)


class AuditLogScreenTests(TestCase):
    def setUp(self):
        self.admin = make_user("admin1", role=Role.ADMIN)
        self.client.login(username="admin1", password=PASSWORD)
        self.url = reverse("audit:log")

    def test_administrators_see_the_log_newest_first(self):
        record_event(Event.CONFIG_CHANGE, entity_type="Setting", entity_id="first")
        record_event(Event.CONFIG_CHANGE, entity_type="Setting", entity_id="second")
        entries = list(self.client.get(self.url).context["page"])
        ids = [e.entity_id for e in entries if e.event == Event.CONFIG_CHANGE]
        self.assertEqual(ids, ["second", "first"])

    def test_the_log_can_be_filtered_by_event_and_text(self):
        record_event(
            Event.CONFIG_CHANGE, entity_type="Setting", entity_id="min_weight", reason="raised"
        )
        record_event(Event.LOGOUT, actor=self.admin)
        only = self.client.get(self.url, {"event": "config_change"}).context["page"]
        self.assertEqual({e.event for e in only}, {Event.CONFIG_CHANGE})
        found = self.client.get(self.url, {"q": "min_weight"}).context["page"]
        self.assertEqual([e.entity_id for e in found], ["min_weight"])

    def test_the_log_is_paged_at_25(self):
        for number in range(30):
            record_event(Event.CONFIG_CHANGE, entity_id=str(number))
        self.assertEqual(len(self.client.get(self.url).context["page"]), 25)

    def test_only_administrators_may_read_the_log(self):
        for role in (Role.STAFF, Role.DONOR, Role.HOSPITAL):
            make_user(role, role=role)
            self.client.login(username=role, password=PASSWORD)
            self.assertEqual(self.client.get(self.url).status_code, 403, role)

    def test_the_log_is_in_the_administrator_menu_only(self):
        self.assertContains(self.client.get(reverse("home")), "Audit log")
        make_user("staff9", role=Role.STAFF)
        self.client.login(username="staff9", password=PASSWORD)
        self.assertNotContains(self.client.get(reverse("home")), "Audit log")

    def test_the_time_column_is_indexed_because_the_log_only_grows(self):
        self.assertTrue(AuditEntry._meta.get_field("occurred_at").db_index)
