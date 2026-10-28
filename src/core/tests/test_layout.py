from django.test import TestCase, override_settings

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_user


@override_settings(ROOT_URLCONF="core.tests.urls_for_tests")
class LayoutTests(TestCase):
    """US-03 (SRS UI-1, UI-2, UI-3, UI-7)."""

    @classmethod
    def setUpTestData(cls):
        for role in Role.values:
            make_user(role, role=role, first_name=role.title(), last_name="Tester")

    def _page(self, role):
        self.client.login(username=role, password=STRONG_PASSWORD)
        return self.client.get("/")

    def test_header_shows_system_name_user_and_role(self):
        response = self._page(Role.STAFF)
        self.assertContains(response, "Blood Bank Management System")
        self.assertContains(response, "Staff Tester, Blood Bank Staff")

    def test_every_screen_has_help_sign_out_footer_and_a_skip_link(self):
        response = self._page(Role.DONOR)
        for text in ("Help", "Sign out", "Release 1.0", "Skip to main content", "Change password"):
            self.assertContains(response, text)

    def test_the_page_is_responsive_and_has_landmarks(self):
        html = self._page(Role.DONOR).content.decode()
        for marker in (
            'name="viewport"',
            "<header",
            '<nav id="site-nav"',
            "<main",
            "<footer",
            'lang="en"',
        ):
            self.assertIn(marker, html)

    def test_a_menu_toggle_exists_for_narrow_screens(self):
        self.assertContains(self._page(Role.DONOR), 'class="nav-toggle"')

    def test_anonymous_pages_have_no_menu_or_user_details(self):
        response = self.client.get("/accounts/login/")
        self.assertNotContains(response, 'id="site-nav"')
        self.assertNotContains(response, "Sign out")
        self.assertContains(response, "Help")

    def test_keyboard_shortcuts_are_on_for_staff_and_admin_only(self):
        for role in (Role.STAFF, Role.ADMIN):
            response = self._page(role)
            self.assertContains(response, 'data-shortcuts="on"')
            self.assertContains(response, "Alt+N new, Alt+S save, Alt+F search, Esc cancel")
        for role in (Role.DONOR, Role.HOSPITAL):
            self.assertNotContains(self._page(role), 'data-shortcuts="on"')

    def test_help_gives_text_for_the_screen_the_user_came_from(self):
        self.client.login(username=Role.DONOR, password=STRONG_PASSWORD)
        response = self.client.get("/help/?topic=accounts:password_change")
        self.assertContains(response, "at least 10 characters")

    def test_help_falls_back_to_general_guidance_for_an_unknown_screen(self):
        self.client.login(username=Role.DONOR, password=STRONG_PASSWORD)
        response = self.client.get("/help/?topic=nothing:here")
        self.assertContains(response, "Use the menu on the left")

    def test_the_home_page_lists_the_role_s_screens_as_cards(self):
        response = self._page(Role.STAFF)
        self.assertContains(response, 'class="card"')

    def test_static_assets_are_referenced(self):
        html = self._page(Role.DONOR).content.decode()
        self.assertIn("core/css/bbms.css", html)
        self.assertIn("core/js/bbms.js", html)
