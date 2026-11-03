"""Security, quality and performance hardening test suite (US-28).

Covers:
- NFR-SEC9: CSRF protection, contextual HTML escaping, SQL parameter binding.
- NFR-P1: Screen render response time under 3.0s at P95 across core views.
- ST-25 and ST-29 from the Software Test Plan.

NFR-Q5 (line coverage of at least 70 percent) is enforced by CI through `fail_under = 70` in
pyproject.toml, not by a test here.
"""

import time

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import make_hospital, make_user
from bloodrequests.models import RequestStatus
from bloodrequests.tests.helpers import make_hospital_user, make_request
from donors.tests.helpers import make_donor
from inventory.models import Status
from inventory.tests.helpers import make_unit


class SecurityHardeningTests(TestCase):
    """NFR-SEC9, ST-29: Security hardening verification."""

    def setUp(self):
        self.admin = make_user("admin_sec_01", Role.ADMIN)
        self.staff = make_user("staff_sec_01", Role.STAFF)

    def test_nfr_sec9_csrf_protection_on_state_changing_post(self):
        """State-changing POST request without valid CSRF token is rejected (HTTP 403)."""
        enforcing_client = Client(enforce_csrf_checks=True)
        enforcing_client.force_login(self.admin)

        # Attempt POST to an administrative state change endpoint without CSRF
        url = reverse("accounts:user_create")
        response = enforcing_client.post(
            url,
            {
                "username": "attacker",
                "role": Role.STAFF,
                "email": "attacker@example.com",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_nfr_sec9_contextual_html_escaping_prevents_xss(self):
        """User-supplied payload containing script tags is strictly escaped on output."""
        self.client.force_login(self.staff)
        xss_payload = "<script>alert('xss-exploit')</script>"
        make_donor(
            full_name=f"Jane {xss_payload}",
            blood_group="O+",
        )

        response = self.client.get(reverse("donors:search"), {"q": "Jane"})
        self.assertEqual(response.status_code, 200)
        # Raw unescaped script tag must never be in HTML body
        self.assertNotContains(response, xss_payload)
        # Escaped entity must be present
        escaped_needle = "&lt;script&gt;alert(&#x27;xss-exploit&#x27;)&lt;/script&gt;"
        self.assertContains(response, escaped_needle)

    def test_nfr_sec9_sql_injection_metacharacters_handled_safely(self):
        """SQL injection payloads in the donor search are bound as plain text."""
        self.client.force_login(self.staff)
        donor = make_donor(full_name="Asha Rao", blood_group="O+")
        make_donor(full_name="Vikram Shetty", blood_group="A+")

        # The search really queries the database: a real name finds its donor.
        response = self.client.get(reverse("donors:search"), {"q": "Asha"})
        self.assertEqual(list(response.context["page"]), [donor])

        # An injection payload is just text that matches no donor, not "every row".
        for payload in ("' OR 1=1 --", '" OR ""="', "%' OR '1'='1"):
            response = self.client.get(reverse("donors:search"), {"q": payload})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(list(response.context["page"]), [])


class PerformanceHardeningTests(TestCase):
    """NFR-P1, ST-25: Core screen latency and render performance benchmarks."""

    def setUp(self):
        self.staff = make_user("perf_staff_01", Role.STAFF)
        self.hospital = make_hospital(name="Perf Memorial Hospital")
        self.hosp_user = make_hospital_user("perf_hosp_01", self.hospital)

        # Seed sample data to simulate representative database load
        donor = make_donor(blood_group="B+")
        for _ in range(10):
            make_unit(donor=donor, status=Status.AVAILABLE)
        make_request(
            self.hosp_user,
            blood_group="B+",
            quantity_requested=2,
            status=RequestStatus.APPROVED,
        )

    def test_nfr_p1_screen_render_well_under_three_seconds_p95(self):
        """Interactive screens render in well under 3.0s boundary at P95."""
        self.client.force_login(self.staff)

        endpoints = [
            reverse("inventory:console"),
            reverse("requests:queue"),
            reverse("camps:manage"),
            reverse("donors:search"),
        ]

        # Each screen is timed several times so the 95th percentile means something.
        latencies = []
        for url in endpoints:
            for _ in range(5):
                start_time = time.perf_counter()
                response = self.client.get(url)
                latencies.append(time.perf_counter() - start_time)
                self.assertEqual(response.status_code, 200)

        latencies.sort()
        p95_latency = latencies[int(len(latencies) * 0.95) - 1]
        self.assertLess(
            p95_latency,
            3.0,
            f"Screen render latency {p95_latency:.4f}s exceeded the 3.0s P95 limit (NFR-P1)",
        )
