from datetime import date, timedelta
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, User
from accounts.tests.helpers import make_user
from collection.models import ScreeningTest, TestName, TestResult
from donors.tests.helpers import PASSWORD
from inventory.models import BloodUnit, Status
from inventory.services.separation import SeparationError, separate_unit

from .helpers import make_unit

VOLUMES = {"PRBC": 200, "FFP": 150, "Platelets": 50}


def tested_unit(result=TestResult.NON_REACTIVE, **kwargs):
    staff = User.objects.filter(username="lab01").first() or make_user("lab01", Role.STAFF)
    unit = make_unit(status=Status.AVAILABLE, **kwargs)
    for name in TestName.values:
        ScreeningTest.objects.create(
            unit=unit, test_name=name, result=result, tested_on=date.today(), tested_by=staff
        )
    return unit


class SeparateUnitTests(TestCase):
    """UT-16, IT-09 (SRS REQ-15, BR-4)."""

    def test_each_component_is_a_new_available_unit_linked_to_the_parent(self):
        parent = tested_unit()
        children = separate_unit(parent, VOLUMES)
        self.assertEqual({c.component_type for c in children}, set(VOLUMES))
        for child in children:
            self.assertEqual(child.parent_unit, parent)
            self.assertEqual(child.donor, parent.donor)
            self.assertEqual(child.blood_group, parent.blood_group)
            self.assertEqual(child.collection_date, parent.collection_date)
            self.assertEqual(child.status, Status.AVAILABLE)
            self.assertEqual(child.volume_ml, VOLUMES[child.component_type])
            self.assertNotEqual(child.unit_id, parent.unit_id)

    def test_expiry_is_counted_from_the_collection_date_per_component(self):
        parent = tested_unit()
        children = {c.component_type: c for c in separate_unit(parent, VOLUMES)}
        self.assertEqual(children["PRBC"].expiry_date, parent.collection_date + timedelta(days=42))
        self.assertEqual(children["FFP"].expiry_date, parent.collection_date + timedelta(days=365))
        self.assertEqual(
            children["Platelets"].expiry_date, parent.collection_date + timedelta(days=5)
        )

    def test_the_whole_blood_unit_is_closed_with_a_reason(self):
        parent = tested_unit()
        separate_unit(parent, VOLUMES)
        parent.refresh_from_db()
        self.assertEqual(parent.status, Status.DISCARDED)
        self.assertEqual(parent.discard_reason, "Separated into components")
        self.assertNotIn(parent, BloodUnit.objects.issuable())

    def test_a_subset_of_components_is_allowed(self):
        parent = tested_unit()
        children = separate_unit(parent, {"PRBC": 300})
        self.assertEqual(len(children), 1)

    def test_volumes_over_the_parent_volume_are_refused_and_nothing_changes(self):
        parent = tested_unit()
        with self.assertRaisesMessage(SeparationError, "more than the unit's 450 ml"):
            separate_unit(parent, {"PRBC": 300, "FFP": 200})
        parent.refresh_from_db()
        self.assertEqual(parent.status, Status.AVAILABLE)
        self.assertEqual(BloodUnit.objects.count(), 1)

    def test_bad_requests_are_refused(self):
        parent = tested_unit()
        for volumes, message in (
            ({}, "at least one component"),
            ({"Cryoprecipitate": 50}, "not a component"),
            ({"PRBC": 0}, "more than zero"),
        ):
            with self.subTest(volumes=volumes), self.assertRaisesMessage(SeparationError, message):
                separate_unit(parent, volumes)

    def test_only_available_whole_blood_can_be_separated(self):
        quarantined = make_unit()
        with self.assertRaisesMessage(SeparationError, "Quarantined"):
            separate_unit(quarantined, VOLUMES)
        parent = tested_unit()
        child = separate_unit(parent, {"PRBC": 200})[0]
        with self.assertRaisesMessage(SeparationError, "Only a whole blood unit"):
            separate_unit(child, {"PRBC": 100})
        with self.assertRaisesMessage(SeparationError, "Discarded"):
            separate_unit(parent, {"PRBC": 100})

    def test_a_unit_without_a_clean_panel_is_refused(self):
        with self.assertRaisesMessage(SeparationError, "screening panel"):
            separate_unit(tested_unit(result=TestResult.REACTIVE), VOLUMES)
        with self.assertRaisesMessage(SeparationError, "screening panel"):
            separate_unit(make_unit(status=Status.AVAILABLE), VOLUMES)

    def test_a_unit_past_expiry_or_a_product_already_out_of_date_is_refused(self):
        expired = tested_unit(expiry_date=date.today() - timedelta(days=1))
        with self.assertRaisesMessage(SeparationError, "past its expiry"):
            separate_unit(expired, VOLUMES)
        old = tested_unit(collection_date=date.today() - timedelta(days=10))
        with self.assertRaisesMessage(SeparationError, "Platelets"):
            separate_unit(old, VOLUMES)
        old.refresh_from_db()
        self.assertEqual(old.status, Status.AVAILABLE)

    def test_a_failure_part_way_leaves_no_partial_products(self):
        parent = tested_unit()
        real = BloodUnit.transition_to
        calls = []

        def flaky(unit, *args, **kwargs):
            calls.append(unit.unit_id)
            if len(calls) == 3:
                raise RuntimeError("database went away")
            return real(unit, *args, **kwargs)

        with mock.patch.object(BloodUnit, "transition_to", flaky):
            with self.assertRaises(RuntimeError):
                separate_unit(parent, VOLUMES)
        self.assertEqual(BloodUnit.objects.count(), 1)
        parent.refresh_from_db()
        self.assertEqual(parent.status, Status.AVAILABLE)


class SeparationViewTests(TestCase):
    """ST-08."""

    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)
        self.client.login(username="staff01", password=PASSWORD)
        self.unit = tested_unit()

    def test_the_detail_page_offers_separation_for_available_whole_blood(self):
        response = self.client.get(reverse("inventory:unit_detail", args=[self.unit.unit_id]))
        self.assertContains(response, "Separate into components")
        self.assertContains(response, "Non-Reactive")

    def test_the_console_lists_whole_blood_with_a_separate_link(self):
        response = self.client.get(reverse("inventory:console"))
        self.assertContains(response, reverse("inventory:separate", args=[self.unit.unit_id]))

    def test_submitting_the_form_creates_the_products_and_shows_them(self):
        url = reverse("inventory:separate", args=[self.unit.unit_id])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(
            url,
            {
                "make_PRBC": "on",
                "volume_PRBC": "200",
                "make_FFP": "on",
                "volume_FFP": "150",
            },
            follow=True,
        )
        self.assertContains(response, "separated into 2 components")
        self.assertContains(response, "Components made from this unit")
        self.assertEqual(self.unit.children.count(), 2)

    def test_a_missing_volume_and_an_oversize_total_show_errors(self):
        url = reverse("inventory:separate", args=[self.unit.unit_id])
        response = self.client.post(url, {"make_PRBC": "on"})
        self.assertContains(response, "Give a volume")
        response = self.client.post(
            url, {"make_PRBC": "on", "volume_PRBC": "300", "make_FFP": "on", "volume_FFP": "300"}
        )
        self.assertContains(response, "more than the unit")
        self.assertEqual(self.unit.children.count(), 0)

    def test_a_child_page_links_back_to_its_parent_and_cannot_be_separated(self):
        child = separate_unit(self.unit, {"PRBC": 200})[0]
        response = self.client.get(reverse("inventory:unit_detail", args=[child.unit_id]))
        self.assertContains(response, self.unit.unit_id)
        self.assertNotContains(response, "Separate into components")

    def test_donors_cannot_reach_the_screens(self):
        make_user("donor01", Role.DONOR)
        self.client.logout()
        self.client.login(username="donor01", password=PASSWORD)
        for name in ("unit_detail", "separate"):
            response = self.client.get(reverse(f"inventory:{name}", args=[self.unit.unit_id]))
            self.assertEqual(response.status_code, 403)
