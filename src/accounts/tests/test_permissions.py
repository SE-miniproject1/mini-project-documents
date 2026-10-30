from django.test import TestCase, override_settings

from accounts.models import Role

from .helpers import STRONG_PASSWORD, make_user


@override_settings(ROOT_URLCONF="accounts.tests.urls_for_tests")
class RoleEnforcementTests(TestCase):
    """IT-25 and ST-28 (NFR-SEC5): authorisation is checked on the server for every request."""

    @classmethod
    def setUpTestData(cls):
        for role in Role.values:
            make_user(role, role=role)

    def _get(self, role, url):
        self.client.login(username=role, password=STRONG_PASSWORD)
        return self.client.get(url)

    def test_anonymous_visitors_are_redirected_to_login(self):
        for url in ("/staff-only/", "/admin-only/", "/hospital-only/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertIn("/accounts/login/", response["Location"])

    def test_a_donor_cannot_reach_staff_or_admin_urls(self):
        self.assertEqual(self._get(Role.DONOR, "/staff-only/").status_code, 403)
        self.assertEqual(self._get(Role.DONOR, "/admin-only/").status_code, 403)

    def test_a_hospital_user_cannot_reach_staff_or_admin_urls(self):
        self.assertEqual(self._get(Role.HOSPITAL, "/staff-only/").status_code, 403)
        self.assertEqual(self._get(Role.HOSPITAL, "/admin-only/").status_code, 403)

    def test_staff_cannot_reach_admin_urls(self):
        self.assertEqual(self._get(Role.STAFF, "/admin-only/").status_code, 403)

    def test_each_role_reaches_its_own_area(self):
        self.assertEqual(self._get(Role.STAFF, "/staff-only/").status_code, 200)
        self.assertEqual(self._get(Role.ADMIN, "/staff-only/").status_code, 200)
        self.assertEqual(self._get(Role.ADMIN, "/admin-only/").status_code, 200)
        self.assertEqual(self._get(Role.HOSPITAL, "/hospital-only/").status_code, 200)

    def test_class_based_views_are_enforced_too(self):
        self.assertEqual(self._get(Role.STAFF, "/hospital-only/").status_code, 403)

    def test_denied_responses_leak_no_page_content(self):
        response = self._get(Role.DONOR, "/staff-only/")
        self.assertNotContains(response, "staff area", status_code=403)

    def test_each_denial_is_logged(self):
        with self.assertLogs("accounts.permissions", level="WARNING") as logs:
            self._get(Role.DONOR, "/admin-only/")
        self.assertIn("authorisation failure", logs.output[0])
