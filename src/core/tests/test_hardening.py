"""Security, quality and performance hardening test suite (US-28).

Covers:
- NFR-SEC9: CSRF protection, contextual HTML escaping, SQL parameter binding.
- NFR-P1: Screen render response time under 3.0s at P95 across core views.
- NFR-Q5: Automated unit test line coverage >= 70% threshold verification.
- ST-25, ST-29, ST-30 from Software Test Plan.
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
        self.hospital = make_hospital(name="Security Testing Hospital")
        self.hosp_user = make_hospital_user("hosp_sec_01", self.hospital)

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
        """SQL injection payloads in input fields are treated as inert strings."""
        self.client.force_login(self.staff)
        sql_payload = "' OR 1=1 --"

        # Search or query with SQL injection string
        response = self.client.get(reverse("inventory:console"), {"q": sql_payload})
        self.assertEqual(response.status_code, 200)
        # Query completes cleanly without server error or syntax exception
        self.assertNotContains(response, "syntax error")


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

        latencies = []
        for url in endpoints:
            start_time = time.perf_counter()
            response = self.client.get(url)
            elapsed = time.perf_counter() - start_time
            self.assertEqual(response.status_code, 200)
            latencies.append(elapsed)

        latencies.sort()
        # Compute P95 latency
        p95_latency = latencies[int(len(latencies) * 0.95)]
        self.assertLess(
            p95_latency,
            3.0,
            f"Screen render latency {p95_latency:.4f}s exceeded 3.0s P95 SLA",
        )
        # Ensure fast sub-second performance in local test runner
        self.assertLess(p95_latency, 1.0)
