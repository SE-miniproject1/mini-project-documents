from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_user
from audit.models import AuditEntry, Event
from donors.tests.helpers import make_donor
from inventory.models import Status
from inventory.tests.helpers import make_unit


class InventoryActionTests(TestCase):
    def setUp(self):
        self.staff = make_user("inventory_staff", role=Role.STAFF)

    def test_transfer_updates_location_and_writes_audit_record(self):
        from inventory.services.actions import transfer_unit

        unit = make_unit(status=Status.AVAILABLE, storage_location="FRIDGE-A1")
        transfer_unit(unit, "FRIDGE-B2", by=self.staff)
        unit.refresh_from_db()
        self.assertEqual((unit.storage_location, unit.status), ("FRIDGE-B2", Status.AVAILABLE))
        entry = AuditEntry.objects.get(event=Event.LOCATION_TRANSFER, entity_id=unit.unit_id)
        self.assertEqual((entry.previous_value, entry.new_value, entry.actor), ("FRIDGE-A1", "FRIDGE-B2", self.staff))

    def test_transfer_rejects_same_location_and_issued_units(self):
        from inventory.services.actions import ActionError, transfer_unit

        unit = make_unit(status=Status.AVAILABLE, storage_location="FRIDGE-A1")
        with self.assertRaises(ActionError):
            transfer_unit(unit, "FRIDGE-A1", by=self.staff)
        issued = make_unit(status=Status.ISSUED)
        with self.assertRaises(ActionError):
            transfer_unit(issued, "FRIDGE-C1", by=self.staff)

    def test_discard_requires_reason_and_respects_status_transition_rules(self):
        from inventory.services.actions import ActionError, discard_unit

        unit = make_unit(status=Status.AVAILABLE)
        with self.assertRaises(ActionError):
            discard_unit(unit, "", by=self.staff)
        issued = make_unit(status=Status.ISSUED)
        with self.assertRaises(ActionError):
            discard_unit(issued, "Breakage", by=self.staff)
        discard_unit(unit, "Breakage", by=self.staff)
        unit.refresh_from_db()
        self.assertEqual((unit.status, unit.discard_reason), (Status.DISCARDED, "Breakage"))


class InventoryActionScreenTests(TestCase):
    def setUp(self):
        self.staff = make_user("staff_actions", role=Role.STAFF)
        self.client.login(username=self.staff.username, password=STRONG_PASSWORD)
        self.unit = make_unit(status=Status.AVAILABLE, storage_location="FRIDGE-A1")

    def test_transfer_screen_updates_location(self):
        response = self.client.post(reverse("inventory:transfer", args=[self.unit.unit_id]), {"destination": "FRIDGE-B2"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.storage_location, "FRIDGE-B2")
        self.assertTrue(AuditEntry.objects.filter(event=Event.LOCATION_TRANSFER, actor=self.staff).exists())

    def test_discard_requires_confirmation_and_reason(self):
        url = reverse("inventory:discard", args=[self.unit.unit_id])
        self.client.post(url, {"reason": "Breakage"}, follow=True)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, Status.AVAILABLE)
        self.client.post(url, {"reason": "Breakage", "confirm": "on"}, follow=True)
        self.unit.refresh_from_db()
        self.assertEqual((self.unit.status, self.unit.discard_reason), (Status.DISCARDED, "Breakage"))

    def test_issued_unit_cannot_be_discarded(self):
        issued = make_unit(status=Status.ISSUED)
        response = self.client.post(reverse("inventory:discard", args=[issued.unit_id]), {"reason": "Breakage", "confirm": "on"}, follow=True)
        issued.refresh_from_db()
        self.assertEqual(issued.status, Status.ISSUED)
        self.assertContains(response, "cannot be discarded")

    def test_inventory_filters_work_together(self):
        donor = make_donor(blood_group="A+")
        matching = make_unit(status=Status.AVAILABLE, donor=donor, component_type="PRBC", storage_location="FRIDGE-A1", expiry_date=date.today() + timedelta(days=3))
        other = make_unit(status=Status.AVAILABLE, component_type="FFP", storage_location="FRIDGE-B2")
        response = self.client.get(reverse("inventory:console"), {"blood_group": "A+", "component_type": "PRBC", "storage_location": "FRIDGE-A1", "status": "Available", "expiry_from": date.today().isoformat(), "expiry_to": (date.today() + timedelta(days=7)).isoformat()})
        self.assertContains(response, matching.unit_id)
        self.assertNotContains(response, other.unit_id)
