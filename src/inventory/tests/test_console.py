from datetime import date, timedelta

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import make_user
from donors.tests.helpers import PASSWORD, make_donor
from inventory.models import BloodUnit, Status
from inventory.services.stock import COMPONENTS, GROUPS, status_counts, stock_grid

from .helpers import make_unit


def seed_o_positive_prbc():
    """UT-18: 5 Available, 2 Reserved, 3 Quarantined and 1 Expired unit of O+ PRBC."""
    donor = make_donor(blood_group="O+")
    for status, count in (
        (Status.AVAILABLE, 5),
        (Status.RESERVED, 2),
        (Status.QUARANTINED, 3),
        (Status.EXPIRED, 1),
    ):
        for _ in range(count):
            make_unit(status=status, donor=donor, component_type="PRBC")


class StockGridTests(TestCase):
    """UT-18 and ST-09 (SRS REQ-17)."""

    def test_only_available_units_are_counted(self):
        seed_o_positive_prbc()
        grid = stock_grid()
        self.assertEqual(grid.cells[("O+", "PRBC")], 5)
        self.assertEqual(grid.total, 5)

    def test_every_blood_group_and_component_appears_even_when_empty(self):
        grid = stock_grid()
        rows = list(grid.rows())
        self.assertEqual([group for group, _, _ in rows], list(GROUPS))
        self.assertTrue(all(len(counts) == len(COMPONENTS) for _, counts, _ in rows))
        self.assertEqual(grid.total, 0)

    def test_row_and_column_totals_add_up(self):
        for group, component, count in (("A+", "PRBC", 2), ("A+", "FFP", 1), ("B-", "PRBC", 4)):
            donor = make_donor(blood_group=group)
            for _ in range(count):
                make_unit(status=Status.AVAILABLE, donor=donor, component_type=component)
        grid = stock_grid()
        self.assertEqual(grid.row_totals["A+"], 3)
        self.assertEqual(grid.column_totals["PRBC"], 6)
        self.assertEqual(grid.total, 7)

    def test_a_unit_past_its_expiry_date_is_not_counted_even_if_still_marked_available(self):
        """NFR-S2."""
        unit = make_unit(status=Status.AVAILABLE)
        BloodUnit.objects.filter(pk=unit.pk).update(expiry_date=date.today() - timedelta(days=1))
        self.assertEqual(stock_grid().total, 0)

    def test_every_status_is_reported_including_empty_ones(self):
        seed_o_positive_prbc()
        self.assertEqual(
            status_counts(),
            {
                "Quarantined": 3,
                "Available": 5,
                "Reserved": 2,
                "Issued": 0,
                "Expired": 1,
                "Discarded": 0,
            },
        )

    def test_a_change_shows_on_the_very_next_read(self):
        """IT-10 (NFR-P5): nothing is cached."""
        unit = make_unit()
        self.assertEqual(stock_grid().total, 0)
        unit.transition_to(Status.AVAILABLE)
        self.assertEqual(stock_grid().total, 1)
        unit.transition_to(Status.RESERVED)
        self.assertEqual(stock_grid().total, 0)


class ConsoleTests(TestCase):
    def setUp(self):
        make_user("staff1", role=Role.STAFF)
        self.client.login(username="staff1", password=PASSWORD)
        self.url = reverse("inventory:console")

    def test_the_console_shows_the_grid_and_the_status_counts(self):
        seed_o_positive_prbc()
        response = self.client.get(self.url)
        self.assertContains(response, "Available units by blood group and component")
        self.assertContains(response, "5 available")
        self.assertContains(response, "All units by status")
        self.assertContains(response, "Quarantined")

    def test_the_grid_matches_the_database_cell_for_cell(self):
        """ST-09."""
        seed_o_positive_prbc()
        response = self.client.get(self.url)
        grid = response.context["grid"]
        self.assertEqual(
            grid.cells[("O+", "PRBC")],
            BloodUnit.objects.filter(
                blood_group="O+", component_type="PRBC", status="Available"
            ).count(),
        )

    def test_the_live_panel_is_returned_alone_for_the_five_second_refresh(self):
        seed_o_positive_prbc()
        response = self.client.get(self.url, {"partial": "1"})
        self.assertContains(response, "Available units by blood group")
        self.assertNotContains(response, "<html")
        self.assertNotContains(response, "Units waiting for test results")

    def test_the_page_asks_the_browser_to_refresh_the_panel_every_five_seconds(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-interval="5000"')
        self.assertContains(response, "partial=1")

    def test_quarantined_units_are_listed_with_a_link_to_enter_results(self):
        unit = make_unit()
        response = self.client.get(self.url)
        self.assertContains(response, unit.unit_id)
        self.assertContains(response, reverse("collection:results", args=[unit.unit_id]))

    def test_released_units_leave_the_waiting_list(self):
        unit = make_unit()
        unit.transition_to(Status.AVAILABLE)
        self.assertContains(self.client.get(self.url), "No units are waiting.")

    def test_the_waiting_list_is_paged_at_25_and_sortable(self):
        donor = make_donor()
        for _ in range(30):
            make_unit(donor=donor)
        response = self.client.get(self.url, {"sort": "unit", "dir": "desc"})
        self.assertEqual(len(response.context["page"]), 25)
        ids = [unit.unit_id for unit in response.context["page"]]
        self.assertEqual(ids, sorted(ids, reverse=True))

    def test_the_number_of_queries_does_not_grow_with_the_number_of_units(self):
        """NFR-P1: the console does a fixed amount of work however large the stock is."""
        donor = make_donor()
        for _ in range(5):
            make_unit(status=Status.AVAILABLE, donor=donor)
        with CaptureQueriesContext(connection) as small:
            self.client.get(self.url)
        for _ in range(40):
            make_unit(status=Status.AVAILABLE, donor=donor)
        with CaptureQueriesContext(connection) as large:
            self.client.get(self.url)
        self.assertEqual(len(small), len(large))

    def test_staff_and_administrators_see_inventory_in_the_menu(self):
        self.assertContains(self.client.get(reverse("home")), "Inventory")
        make_user("admin1", role=Role.ADMIN)
        self.client.login(username="admin1", password=PASSWORD)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertContains(self.client.get(reverse("home")), "Inventory")

    def test_donors_and_hospital_users_cannot_see_inventory(self):
        for role in (Role.DONOR, Role.HOSPITAL):
            make_user(role, role=role)
            self.client.login(username=role, password=PASSWORD)
            self.assertEqual(self.client.get(self.url).status_code, 403, role)
            self.assertEqual(self.client.get(self.url, {"partial": "1"}).status_code, 403, role)
            self.assertNotContains(self.client.get(reverse("home")), "Inventory")

    def test_anonymous_visitors_are_sent_to_sign_in(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)
