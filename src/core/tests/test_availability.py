from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_user
from bloodrequests.tests.helpers import make_hospital_user
from donors.tests.helpers import make_donor
from inventory.models import Status
from inventory.tests.helpers import make_unit


class AvailabilitySearchTests(TestCase):
    def setUp(self):
        self.hospital = make_hospital_user()
        self.client.login(username=self.hospital.username, password=STRONG_PASSWORD)
        self.url = reverse("search:availability")

    def test_hospital_sees_aggregated_counts_by_group_and_component_only(self):
        donor = make_donor(blood_group="A+")
        first = make_unit(status=Status.AVAILABLE, donor=donor, component_type="PRBC")
        second = make_unit(status=Status.AVAILABLE, donor=donor, component_type="PRBC")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A+")
        self.assertContains(response, "PRBC")
        self.assertEqual(
            response.context["counts"],
            [{"blood_group": "A+", "component_type": "PRBC", "available_count": 2}],
        )
        body = response.content.decode()
        self.assertNotIn(first.unit_id, body)
        self.assertNotIn(second.unit_id, body)
        self.assertNotIn(donor.donor_id, body)
        self.assertNotIn(donor.full_name, body)
        self.assertNotIn(donor.mobile_number, body)
        self.assertNotIn(donor.email, body)

    def test_search_filters_by_group_and_component(self):
        donor_a = make_donor(blood_group="A+")
        donor_b = make_donor(blood_group="B+")
        make_unit(status=Status.AVAILABLE, donor=donor_a, component_type="PRBC")
        make_unit(status=Status.AVAILABLE, donor=donor_b, component_type="FFP")
        response = self.client.get(self.url, {"group": "A+", "component": "PRBC"})
        # The page always lists every group in the filter, so check the result rows.
        self.assertEqual(
            response.context["counts"],
            [{"blood_group": "A+", "component_type": "PRBC", "available_count": 1}],
        )
        self.assertNotContains(response, "<td>B+</td>")

    def test_quarantined_reserved_expired_and_discarded_units_are_not_counted(self):
        donor = make_donor(blood_group="O+")
        make_unit(status=Status.QUARANTINED, donor=donor, component_type="PRBC")
        make_unit(status=Status.AVAILABLE, donor=donor, component_type="PRBC")
        make_unit(status=Status.RESERVED, donor=donor, component_type="PRBC")
        make_unit(status=Status.EXPIRED, donor=donor, component_type="PRBC")
        make_unit(status=Status.DISCARDED, donor=donor, component_type="PRBC")
        response = self.client.get(self.url, {"group": "O+", "component": "PRBC"})
        self.assertEqual([row["available_count"] for row in response.context["counts"]], [1])

    def test_an_unknown_filter_value_is_ignored(self):
        make_unit(status=Status.AVAILABLE, donor=make_donor(blood_group="A+"))
        response = self.client.get(self.url, {"group": "Z+", "component": "Plasma'--"})
        self.assertEqual(response.context["selected_group"], "")
        self.assertEqual(len(response.context["counts"]), 1)

    def test_unlinked_hospital_account_is_refused(self):
        user = make_user("unlinked", role=Role.HOSPITAL)
        self.client.logout()
        self.client.login(username=user.username, password=STRONG_PASSWORD)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_non_hospital_roles_cannot_use_the_search(self):
        for role in (Role.DONOR, Role.STAFF, Role.ADMIN):
            user = make_user(f"user_{role}", role=role)
            self.client.logout()
            self.client.login(username=user.username, password=STRONG_PASSWORD)
            self.assertEqual(self.client.get(self.url).status_code, 403)
