"""Test Plan cases IT-06, SV-04, SV-06 and SV-07 (Deliverable 3).

IT-06  A Quarantined unit is invisible to availability search and to allocation.
SV-04  HTTPS redirect and HSTS header. The TLS version handshake cannot be tested here and is
       left to a scanner against a deployed server (see docs/test-reports).
SV-06  Logs never contain passwords, session tokens or declared medical conditions.
SV-07  Hostile input never produces a server error and is stored or shown as inert text.
"""

import logging

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_user
from bloodrequests.allocation import allocate_units
from bloodrequests.models import RequestStatus
from bloodrequests.tests.helpers import make_hospital_user, make_request
from bloodrequests.workflow import WorkflowError
from donors.models import DeferralCondition, Donor
from donors.tests.helpers import make_donor, registration_data
from inventory.models import Status
from inventory.tests.helpers import make_unit


class QuarantineEnforcementTests(TestCase):
    """IT-06: a Quarantined unit is not counted and cannot be allocated."""

    def test_a_quarantined_unit_is_not_counted_in_the_hospital_search(self):
        donor = make_donor(blood_group="A+")
        make_unit(status=Status.QUARANTINED, donor=donor, component_type="Whole Blood")
        hospital_user = make_hospital_user()
        self.client.login(username=hospital_user.username, password=STRONG_PASSWORD)
        response = self.client.get(
            reverse("search:availability"), {"group": "A+", "component": "Whole Blood"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["counts"], [])

    def test_a_quarantined_unit_cannot_be_allocated(self):
        staff = make_user("staff_it06", Role.STAFF)
        request = make_request(quantity_requested=1, status=RequestStatus.APPROVED)
        unit = make_unit(
            status=Status.QUARANTINED,
            donor=make_donor(blood_group="A+"),
            component_type="Whole Blood",
        )
        with self.assertRaises(WorkflowError):
            allocate_units(request, [unit.unit_id], by=staff)
        unit.refresh_from_db()
        self.assertEqual(unit.status, Status.QUARANTINED)


class TransportSecurityTests(TestCase):
    """SV-04, the part that can run without a deployed server."""

    @override_settings(SECURE_SSL_REDIRECT=True, ALLOWED_HOSTS=["testserver"])
    def test_plain_http_gets_a_permanent_redirect_to_https(self):
        response = Client().get("/accounts/login/", secure=False)
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response["Location"].startswith("https://"))

    @override_settings(
        SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=31536000, ALLOWED_HOSTS=["testserver"]
    )
    def test_https_responses_carry_the_hsts_header(self):
        response = Client().get("/accounts/login/", secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("max-age=31536000", response["Strict-Transport-Security"])


class LogContentTests(TestCase):
    """SV-06: secrets never reach the log output."""

    def test_login_registration_and_screening_log_no_secrets(self):
        with self.assertLogs(level=logging.DEBUG) as captured:
            logging.getLogger("sv06").info("marker so assertLogs has a record")

            user = make_user("staff_sv06", Role.STAFF)
            client = Client()
            client.post(
                reverse("accounts:login"), {"username": user.username, "password": "wrong-Pass1!"}
            )
            client.post(
                reverse("accounts:login"),
                {"username": user.username, "password": STRONG_PASSWORD},
            )
            session_id = client.cookies["sessionid"].value

            condition = DeferralCondition.objects.filter(is_active=True).first()
            self.assertIsNotNone(condition, "the seeded condition list is empty")
            condition_name = condition.name
            data = registration_data(email="sv06@example.com")
            data["declared_conditions"] = [condition.pk]
            Client().post(reverse("donors:register"), data)
            self.assertTrue(Donor.objects.filter(email="sv06@example.com").exists())

        text = "\n".join(captured.output)
        self.assertNotIn(STRONG_PASSWORD, text)
        self.assertNotIn("wrong-Pass1!", text)
        self.assertNotIn(session_id, text)
        self.assertNotIn(condition_name, text)


class HostileInputTests(TestCase):
    """SV-07: fuzzed payloads give field messages or inert text, never a 500."""

    PAYLOADS = [
        "x" * 10_000,
        "",
        "-1",
        "' OR 1=1 --",
        "<script>alert(1)</script>",
        "‮\u0000ünïcödé 血",
    ]

    def test_registration_fields_survive_every_payload(self):
        anonymous = Client()
        text_fields = [
            "full_name",
            "address_line",
            "city",
            "pin_code",
            "mobile_number",
            "emergency_contact_name",
            "weight_kg",
        ]
        for field in text_fields:
            for payload in self.PAYLOADS:
                with self.subTest(field=field, payload=payload[:20]):
                    response = anonymous.post(
                        reverse("donors:register"),
                        registration_data(
                            **{field: payload}, email=f"f{abs(hash(payload))}@x.test"
                        ),
                    )
                    self.assertLess(response.status_code, 500)
                    self.assertNotIn(b"<script>alert(1)</script>", response.content)

    def test_search_boxes_survive_every_payload(self):
        staff = make_user("staff_sv07", Role.STAFF)
        self.client.login(username=staff.username, password=STRONG_PASSWORD)
        for payload in self.PAYLOADS:
            with self.subTest(payload=payload[:20]):
                response = self.client.get(reverse("donors:search"), {"q": payload})
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "<script>alert(1)</script>")

    def test_a_bad_quantity_in_a_blood_request_is_refused(self):
        hospital_user = make_hospital_user()
        self.client.login(username=hospital_user.username, password=STRONG_PASSWORD)
        for payload in ("-1", "0", "abc", "9" * 40):
            with self.subTest(payload=payload):
                response = self.client.post(
                    reverse("requests:new"),
                    {"blood_group": "A+", "component_type": "PRBC", "quantity": payload},
                )
                self.assertLess(response.status_code, 500)
                self.assertEqual(response.status_code, 200)  # form shown again with an error
