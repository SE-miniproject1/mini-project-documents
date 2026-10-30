import itertools
import re
from datetime import date, timedelta
from pathlib import Path

from django.contrib.admin.sites import site
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Role
from accounts.tests.helpers import make_user
from inventory.models import (
    ALLOWED_TRANSITIONS,
    BloodUnit,
    InvalidTransitionError,
    Status,
)
from inventory.services.id_generator import UNIT_ID_PATTERN, generate_unit_id
from inventory.services.shelf_life import expiry_date_for
from inventory.signals import unit_status_changed

from .helpers import make_unit


class UnitIdTests(TestCase):
    """UT-11 (SRS REQ-10): unique, immutable BU + 10 digit identifiers."""

    def test_a_thousand_identifiers_are_distinct_and_well_formed(self):
        ids = [generate_unit_id() for _ in range(1000)]
        self.assertEqual(len(set(ids)), 1000)
        self.assertTrue(all(UNIT_ID_PATTERN.match(i) for i in ids))

    def test_numbering_starts_at_1000000001(self):
        self.assertEqual(generate_unit_id(), "BU1000000001")

    def test_an_identifier_cannot_be_changed(self):
        unit = BloodUnit.objects.get(pk=make_unit().pk)
        unit.unit_id = "BU9999999999"
        with self.assertRaises(ValueError):
            unit.save()


class UnitRecordTests(TestCase):
    """UT-17 (SRS REQ-16): every attribute is stored and a new unit is Quarantined."""

    def test_every_attribute_round_trips(self):
        unit = make_unit(
            component_type="PRBC",
            volume_ml=350,
            storage_location="FRIDGE-A2",
            bag_lot_number="BG-2026-0418",
            collection_site="CMP0000002",
        )
        stored = BloodUnit.objects.get(pk=unit.pk)
        self.assertEqual(stored.component_type, "PRBC")
        self.assertEqual(stored.volume_ml, 350)
        self.assertEqual(stored.storage_location, "FRIDGE-A2")
        self.assertEqual(stored.bag_lot_number, "BG-2026-0418")
        self.assertEqual(stored.collection_site, "CMP0000002")
        self.assertEqual(stored.blood_group, unit.donor.blood_group)
        self.assertIsNone(stored.parent_unit)

    def test_a_new_unit_is_quarantined_in_quarantine_storage(self):
        unit = make_unit()
        self.assertEqual(unit.status, Status.QUARANTINED)
        self.assertEqual(unit.storage_location, "QUARANTINE")

    def test_a_unit_cannot_be_created_in_any_other_status(self):
        unit = make_unit()
        with self.assertRaises(InvalidTransitionError):
            BloodUnit.objects.create(
                unit_id=generate_unit_id(),
                donor=unit.donor,
                blood_group="A+",
                component_type="Whole Blood",
                volume_ml=450,
                collection_date=date.today(),
                expiry_date=date.today() + timedelta(days=35),
                bag_lot_number="X",
                status=Status.AVAILABLE,
            )


class TransitionRuleTests(TestCase):
    """UT-12 and NFR-S7: only permitted moves change a status, every other is refused."""

    def test_the_permitted_moves_are_exactly_the_documented_ones(self):
        self.assertEqual(
            {k.value: {v.value for v in vs} for k, vs in ALLOWED_TRANSITIONS.items()},
            {
                "Quarantined": {"Available", "Discarded", "Expired"},
                "Available": {"Reserved", "Expired", "Discarded"},
                "Reserved": {"Issued", "Available", "Expired", "Discarded"},
                "Expired": {"Discarded"},
                "Issued": set(),
                "Discarded": set(),
            },
        )

    def test_every_permitted_move_works_and_every_other_is_refused(self):
        for start, end in itertools.product(Status, Status):
            unit = make_unit(status=start)
            if end in ALLOWED_TRANSITIONS[start]:
                unit.transition_to(end, reason="test reason")
                self.assertEqual(BloodUnit.objects.get(pk=unit.pk).status, end, (start, end))
            else:
                with self.assertRaises(InvalidTransitionError, msg=(start, end)):
                    unit.transition_to(end, reason="test reason")
                self.assertEqual(BloodUnit.objects.get(pk=unit.pk).status, start, (start, end))

    def test_a_quarantined_unit_cannot_be_issued_directly(self):
        unit = make_unit()
        with self.assertRaises(InvalidTransitionError):
            unit.transition_to(Status.ISSUED)

    def test_issued_and_discarded_units_are_final(self):
        for final in (Status.ISSUED, Status.DISCARDED):
            unit = make_unit(status=final)
            for target in Status:
                with self.assertRaises(InvalidTransitionError):
                    unit.transition_to(target, reason="x")

    def test_an_issued_unit_cannot_be_discarded(self):
        """SRS REQ-22."""
        with self.assertRaises(InvalidTransitionError):
            make_unit(status=Status.ISSUED).transition_to(Status.DISCARDED, reason="breakage")

    def test_discarding_needs_a_reason_and_records_it(self):
        unit = make_unit()
        with self.assertRaises(InvalidTransitionError):
            unit.transition_to(Status.DISCARDED)
        with self.assertRaises(InvalidTransitionError):
            unit.transition_to(Status.DISCARDED, reason="   ")
        unit.transition_to(Status.DISCARDED, reason="Breakage")
        self.assertEqual(BloodUnit.objects.get(pk=unit.pk).discard_reason, "Breakage")

    def test_writing_the_status_directly_is_refused(self):
        unit = BloodUnit.objects.get(pk=make_unit().pk)
        unit.status = Status.AVAILABLE
        with self.assertRaises(InvalidTransitionError):
            unit.save()
        self.assertEqual(BloodUnit.objects.get(pk=unit.pk).status, Status.QUARANTINED)

    def test_a_bulk_update_bypasses_the_instance_guard(self):
        """Known limit. The guard sits on the model, so a queryset update skips it.

        `test_no_application_code_updates_a_status_in_bulk` below keeps production code
        from ever using that route.
        """
        unit = make_unit()
        BloodUnit.objects.filter(pk=unit.pk).update(status=Status.AVAILABLE)
        self.assertEqual(BloodUnit.objects.get(pk=unit.pk).status, Status.AVAILABLE)

    def test_no_application_code_updates_a_status_in_bulk(self):
        root = Path(__file__).resolve().parents[2]
        pattern = re.compile(r"\.update\([^)]*\bstatus\b")
        offenders = []
        for path in root.rglob("*.py"):
            parts = path.relative_to(root).parts
            if "tests" in parts or "migrations" in parts:
                continue
            if pattern.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path.relative_to(root)))
        self.assertEqual(offenders, [])

    def test_a_stale_copy_cannot_act_on_a_unit_that_has_moved_on(self):
        """Two staff holding the same unit: the second is refused (SRS NFR-S4)."""
        first = make_unit(status=Status.AVAILABLE)
        second = BloodUnit.objects.get(pk=first.pk)
        first.transition_to(Status.RESERVED)
        with self.assertRaises(InvalidTransitionError):
            second.transition_to(Status.RESERVED)
        self.assertEqual(BloodUnit.objects.get(pk=first.pk).status, Status.RESERVED)

    def test_can_transition_to_reports_without_changing_anything(self):
        unit = make_unit()
        self.assertTrue(unit.can_transition_to(Status.AVAILABLE))
        self.assertFalse(unit.can_transition_to(Status.ISSUED))
        self.assertEqual(unit.status, Status.QUARANTINED)


class AnnouncementTests(TestCase):
    """SRS REQ-23: every change is announced inside the same transaction."""

    def test_a_receiver_gets_the_details_of_each_change(self):
        seen = []

        def receiver(sender, unit, previous, new, by, reason, **kwargs):
            seen.append((unit.unit_id, previous, new, by, reason))

        unit_status_changed.connect(receiver)
        self.addCleanup(unit_status_changed.disconnect, receiver)
        staff = make_user("s1", role=Role.STAFF)
        unit = make_unit()
        unit.transition_to(Status.AVAILABLE, by=staff)
        self.assertEqual(seen, [(unit.unit_id, "Quarantined", "Available", staff, "")])

    def test_a_failing_receiver_undoes_the_change(self):
        def broken(sender, **kwargs):
            raise RuntimeError("audit store unavailable")

        unit_status_changed.connect(broken)
        self.addCleanup(unit_status_changed.disconnect, broken)
        unit = make_unit()
        with self.assertRaises(RuntimeError):
            unit.transition_to(Status.AVAILABLE)
        self.assertEqual(BloodUnit.objects.get(pk=unit.pk).status, Status.QUARANTINED)

    def test_a_refused_move_announces_nothing(self):
        seen = []
        unit_status_changed.connect(lambda **kw: seen.append(kw), weak=False, dispatch_uid="t")
        self.addCleanup(unit_status_changed.disconnect, dispatch_uid="t")
        with self.assertRaises(InvalidTransitionError):
            make_unit().transition_to(Status.ISSUED)
        self.assertEqual(seen, [])


class IssuableTests(TestCase):
    """SRS REQ-11 and NFR-S2: only unexpired Available units may be offered or counted."""

    def test_only_available_unexpired_units_are_issuable(self):
        wanted = make_unit(status=Status.AVAILABLE)
        make_unit(status=Status.QUARANTINED)
        make_unit(status=Status.RESERVED)
        make_unit(status=Status.ISSUED)
        make_unit(status=Status.EXPIRED)
        make_unit(status=Status.DISCARDED)
        self.assertEqual(list(BloodUnit.objects.issuable()), [wanted])

    def test_a_unit_past_its_expiry_date_is_not_issuable_even_if_still_marked_available(self):
        stale = make_unit(status=Status.AVAILABLE)
        BloodUnit.objects.filter(pk=stale.pk).update(expiry_date=date.today() - timedelta(days=1))
        self.assertEqual(BloodUnit.objects.issuable().count(), 0)

    def test_a_unit_expiring_today_is_still_issuable_today(self):
        unit = make_unit(status=Status.AVAILABLE)
        BloodUnit.objects.filter(pk=unit.pk).update(expiry_date=date.today())
        self.assertEqual(BloodUnit.objects.issuable().count(), 1)


class DatabaseRuleTests(TestCase):
    def test_the_database_refuses_a_discarded_unit_with_no_reason(self):
        unit = make_unit()
        with self.assertRaises(IntegrityError), transaction.atomic():
            BloodUnit.objects.filter(pk=unit.pk).update(status="Discarded", discard_reason="")

    def test_the_database_refuses_an_unknown_status(self):
        unit = make_unit()
        with self.assertRaises(IntegrityError), transaction.atomic():
            BloodUnit.objects.filter(pk=unit.pk).update(status="Lost")

    def test_the_database_refuses_an_expiry_before_collection(self):
        unit = make_unit()
        with self.assertRaises(IntegrityError), transaction.atomic():
            BloodUnit.objects.filter(pk=unit.pk).update(
                expiry_date=unit.collection_date - timedelta(days=1)
            )


class ShelfLifeTests(TestCase):
    """SRS BR-4: shelf life by component, counted from collection."""

    def test_each_component_has_its_own_shelf_life(self):
        collected = date(2026, 9, 1)
        expected = {
            "Whole Blood": date(2026, 10, 6),
            "PRBC": date(2026, 10, 13),
            "FFP": date(2027, 9, 1),
            "Platelets": date(2026, 9, 6),
            "Cryoprecipitate": date(2027, 9, 1),
        }
        for component, expiry in expected.items():
            self.assertEqual(expiry_date_for(component, collected), expiry, component)


class AdminTests(TestCase):
    def test_the_admin_cannot_add_edit_or_delete_units(self):
        model_admin = site._registry[BloodUnit]
        request = type("R", (), {"user": make_user("a", role=Role.ADMIN)})()
        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))
        self.assertIn("status", model_admin.get_readonly_fields(request))
