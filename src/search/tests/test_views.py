from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import make_user
from bloodrequests.tests.helpers import make_hospital_user
from inventory.tests.helpers import make_cleared_unit


class AvailabilityViewTests(TestCase):
    def setUp(self):
        self.hospital_user = make_hospital_user()
        self.url = reverse("search:availability")

    def test_hospital_can_open_availability_page(self):
        self.client.force_login(self.hospital_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_hospital_sees_counts_without_unit_or_donor_identifiers(self):
        self.client.force_login(self.hospital_user)
        make_cleared_unit(blood_group="B+", component_type="PRBC")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "B+")
        self.assertContains(response, "PRBC")
        self.assertContains(response, "Available quantity")
        self.assertNotContains(response, "BG-2026-0417")
        self.assertNotContains(response, "donor_id")
        self.assertNotContains(response, "unit_id")

    def test_hospital_can_filter_by_group_and_component(self):
        self.client.force_login(self.hospital_user)
        make_cleared_unit(blood_group="B+", component_type="PRBC")
        make_cleared_unit(blood_group="A+", component_type="FFP")

        response = self.client.get(
            self.url,
            {"blood_group": "B+", "component_type": "PRBC"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "B+")
        self.assertContains(response, "PRBC")
        self.assertEqual([item["blood_group"] for item in response.context["results"]], ["B+"])

    def test_staff_cannot_open_hospital_availability_page(self):
        staff = make_user("staff-search", Role.STAFF)
        self.client.force_login(staff)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_unlinked_hospital_user_gets_forbidden_response(self):
        user = make_user("unlinked-hospital", Role.HOSPITAL)
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
