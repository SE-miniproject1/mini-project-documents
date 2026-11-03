from django.test import TestCase, override_settings

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_user
from core.navigation import NAV_ITEMS, nav_for


def labels(user):
    return [link["label"] for link in nav_for(user)]


@override_settings(ROOT_URLCONF="core.tests.urls_for_tests")
class NavigationTests(TestCase):
    """US-03 (SRS UI-1, UI-6): each role sees only its own screens."""

    @classmethod
    def setUpTestData(cls):
        cls.users = {role: make_user(role, role=role) for role in Role.values}

    def test_anonymous_visitors_get_no_navigation(self):
        from django.contrib.auth.models import AnonymousUser

        self.assertEqual(nav_for(AnonymousUser()), [])

    def test_a_donor_sees_donor_screens_only(self):
        self.assertEqual(labels(self.users[Role.DONOR]), ["Home", "My eligibility"])

    def test_staff_see_inventory_but_not_the_donor_dashboard(self):
        result = labels(self.users[Role.STAFF])
        self.assertIn("Inventory", result)
        self.assertNotIn("My eligibility", result)

    def test_a_hospital_user_sees_requests_but_not_inventory(self):
        result = labels(self.users[Role.HOSPITAL])
        self.assertIn("Raise a request", result)
        self.assertNotIn("Inventory", result)

    def test_links_to_screens_that_do_not_exist_yet_are_left_out(self):
        # camps:list is in the registry but has no URL in this test configuration.
        self.assertNotIn("Upcoming camps", labels(self.users[Role.DONOR]))

    def test_the_registry_gives_every_role_at_least_a_home_link(self):
        for role in Role.values:
            self.assertTrue(
                any(role in item.roles for item in NAV_ITEMS if item.url_name == "home"), role
            )

    def test_the_current_page_is_marked(self):
        self.client.login(username=Role.STAFF, password=STRONG_PASSWORD)
        response = self.client.get("/inventory/")
        self.assertContains(response, 'aria-current="page">Inventory')

    def test_the_menu_is_rendered_from_the_server_not_hidden_in_the_browser(self):
        self.client.login(username=Role.DONOR, password=STRONG_PASSWORD)
        response = self.client.get("/")
        self.assertNotContains(response, "Inventory")
        self.assertNotContains(response, "Raise a request")
