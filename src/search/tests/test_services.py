from datetime import date, timedelta

from django.test import TestCase

from inventory.models import Status
from inventory.tests.helpers import make_cleared_unit, make_unit
from search.services import availability_search


class AvailabilitySearchTests(TestCase):
    def test_counts_only_available_unexpired_units(self):
        make_cleared_unit(
            blood_group="B+",
            component_type="PRBC",
        )
        make_unit(
            status=Status.QUARANTINED,
            blood_group="B+",
            component_type="PRBC",
        )
        make_cleared_unit(
            blood_group="B+",
            component_type="PRBC",
            expiry_date=date.today() - timedelta(days=1),
        )

        results = availability_search("B+", "PRBC")

        self.assertEqual(
            results,
            [{"blood_group": "B+", "component_type": "PRBC", "quantity": 1}],
        )

    def test_returns_only_aggregate_fields(self):
        make_cleared_unit(
            blood_group="O+",
            component_type="Whole Blood",
        )

        results = availability_search()

        self.assertTrue(results)
        self.assertEqual(
            set(results[0]),
            {"blood_group", "component_type", "quantity"},
        )

    def test_filters_by_blood_group_and_component(self):
        make_cleared_unit(
            blood_group="A+",
            component_type="PRBC",
        )
        make_cleared_unit(
            blood_group="B+",
            component_type="FFP",
        )

        results = availability_search("A+", "PRBC")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["blood_group"], "A+")
        self.assertEqual(results[0]["component_type"], "PRBC")
