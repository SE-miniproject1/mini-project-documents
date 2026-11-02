from xml.etree import ElementTree

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import make_user
from donors.tests.helpers import PASSWORD
from inventory.services.barcode import code128_svg

from .helpers import make_unit


class BarcodeTests(SimpleTestCase):
    """ST-05 (SRS REQ-10, HI-1): the unit identifier is rendered as a Code 128 barcode."""

    def test_the_output_is_well_formed_svg_with_bars(self):
        svg = code128_svg("BU1000000001")
        root = ElementTree.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertGreater(len(list(root.iter("{http://www.w3.org/2000/svg}rect"))), 20)

    def test_the_same_identifier_always_gives_the_same_barcode(self):
        self.assertEqual(code128_svg("BU1000000001"), code128_svg("BU1000000001"))

    def test_different_identifiers_give_different_barcodes(self):
        self.assertNotEqual(code128_svg("BU1000000001"), code128_svg("BU1000000002"))

    def test_the_symbol_encodes_exactly_the_identifier(self):
        from barcode import Code128

        self.assertEqual(Code128("BU1000000001").get_fullcode(), "BU1000000001")


class LabelTests(TestCase):
    def setUp(self):
        make_user("staff1", role=Role.STAFF)
        self.client.login(username="staff1", password=PASSWORD)
        self.unit = make_unit()

    def test_the_label_shows_the_unit_details_and_a_barcode_image(self):
        response = self.client.get(reverse("inventory:label", args=[self.unit.unit_id]))
        self.assertContains(response, self.unit.unit_id)
        self.assertContains(response, self.unit.blood_group)
        self.assertContains(response, reverse("inventory:barcode", args=[self.unit.unit_id]))
        self.assertContains(response, "data-print")

    def test_the_label_never_shows_the_donor(self):
        response = self.client.get(reverse("inventory:label", args=[self.unit.unit_id]))
        self.assertNotContains(response, self.unit.donor.full_name)
        self.assertNotContains(response, self.unit.donor.donor_id)

    def test_the_barcode_is_served_as_svg(self):
        response = self.client.get(reverse("inventory:barcode", args=[self.unit.unit_id]))
        self.assertEqual(response["Content-Type"], "image/svg+xml")

    def test_unknown_units_give_not_found(self):
        self.assertEqual(
            self.client.get(reverse("inventory:label", args=["BU0000000000"])).status_code, 404
        )

    def test_donors_and_hospital_users_cannot_see_labels(self):
        for role in (Role.DONOR, Role.HOSPITAL):
            make_user(role, role=role)
            self.client.login(username=role, password=PASSWORD)
            for name in ("inventory:label", "inventory:barcode"):
                response = self.client.get(reverse(name, args=[self.unit.unit_id]))
                self.assertEqual(response.status_code, 403, (role, name))
