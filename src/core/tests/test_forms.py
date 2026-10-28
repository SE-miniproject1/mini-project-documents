from django.test import TestCase, override_settings

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_user


@override_settings(ROOT_URLCONF="core.tests.urls_for_tests")
class FormStandardTests(TestCase):
    """US-03 (SRS UI-2, UI-4): error display and the standard Save and Cancel controls."""

    def setUp(self):
        make_user("staff", role=Role.STAFF)
        self.client.login(username="staff", password=STRONG_PASSWORD)

    def test_a_blank_form_has_save_and_cancel(self):
        response = self.client.get("/form/")
        self.assertContains(response, ">Save</button>")
        self.assertContains(response, 'data-shortcut="cancel"')
        self.assertContains(response, "(required)")

    def test_errors_appear_beside_the_field_prefixed_with_its_label(self):
        response = self.client.post("/form/", {"full_name": "", "mobile": ""})
        self.assertContains(response, 'class="field-error" id="id_full_name_error">Full name: ')
        self.assertContains(response, 'class="field-error" id="id_mobile_error">Mobile number: ')

    def test_a_summary_banner_at_the_top_lists_every_error(self):
        response = self.client.post("/form/", {"full_name": "", "mobile": ""})
        html = response.content.decode()
        start = html.index('class="error-summary"')
        summary = html[start : html.index('<form method="post" novalidate', start)]
        self.assertIn("Full name:", summary)
        self.assertIn("Mobile number:", summary)
        self.assertIn('role="alert"', summary)

    def test_form_level_errors_are_in_the_summary_too(self):
        response = self.client.post("/form/", {"full_name": "A", "mobile": "0000000000"})
        self.assertContains(response, "That number is reserved.")

    def test_fields_in_error_are_tied_to_their_message_for_screen_readers(self):
        response = self.client.post("/form/", {"full_name": "", "mobile": ""})
        self.assertContains(response, 'aria-invalid="true"')
        self.assertContains(response, 'aria-describedby="id_full_name_error"')

    def test_a_valid_form_shows_no_errors(self):
        response = self.client.post("/form/", {"full_name": "A", "mobile": "9880011223"})
        self.assertContains(response, "saved")

    def test_help_text_is_shown(self):
        self.assertContains(self.client.get("/form/"), "Ten digits.")


@override_settings(ROOT_URLCONF="core.tests.urls_for_tests")
class ErrorPageTests(TestCase):
    """SRS UI-4: errors never expose stack traces, SQL or internal identifiers."""

    def test_an_unhandled_error_shows_a_generic_page(self):
        self.client.raise_request_exception = False
        make_user("staff", role=Role.STAFF)
        self.client.login(username="staff", password=STRONG_PASSWORD)
        with self.assertLogs("django.request", level="ERROR"):
            response = self.client.get("/broken/")
        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Something went wrong", status_code=500)
        for leaked in ("SELECT", "internal_table", "Traceback", "ValueError"):
            self.assertNotContains(response, leaked, status_code=500)

    def test_not_found_and_forbidden_pages_are_friendly(self):
        make_user("donor", role=Role.DONOR)
        self.client.login(username="donor", password=STRONG_PASSWORD)
        with self.assertLogs("django.request", level="WARNING"):
            response = self.client.get("/missing-page/")
        self.assertContains(response, "Page not found", status_code=404)
