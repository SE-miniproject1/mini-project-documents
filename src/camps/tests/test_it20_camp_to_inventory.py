from django.test import TestCase

from camps.tests import test_collection_link as t
from inventory.models import Status


class CampCollectionToInventoryTests(TestCase):
    """IT-20 (SRS REQ-36, REQ-37): camp collections reach inventory and closure locks the camp."""

    def test_three_camp_units_are_quarantined_and_closure_blocks_a_fourth(self):
        staff = t.make_user("staff01", t.Role.STAFF)
        camp = t.started_camp(staff)
        units = [t.collect(t.make_donor(), staff, camp.camp_id)[1] for _ in range(3)]
        for unit in units:
            unit.refresh_from_db()
            self.assertEqual(unit.status, Status.QUARANTINED)
            self.assertEqual(unit.collection_site, camp.camp_id)
        closed = t.close_camp(camp, by=staff)
        self.assertEqual(closed.units_collected, 3)
        with self.assertRaisesMessage(t.CollectionBlockedError, "is Completed"):
            t.collect(t.make_donor(), staff, camp.camp_id)
