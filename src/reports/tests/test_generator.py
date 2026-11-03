import csv
import io
from datetime import UTC, date, datetime, time, timedelta

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from accounts.tests.helpers import make_hospital, make_user
from bloodrequests.models import RequestStatus
from bloodrequests.tests.helpers import make_hospital_user, make_request
from camps.models import Camp, Enrolment
from collection.models import Donation, TestName
from donors.tests.helpers import make_donor
from inventory.models import Status
from inventory.tests.helpers import clear_screening, make_cleared_unit, make_unit
from reports.definitions import REPORTS
from reports.services.generator import ReportError, generate, screening_outcome
from reports.services.result import format_value

TODAY = date.today()
RANGE = (TODAY - timedelta(days=30), TODAY)


def donate(unit, staff, when=None, site="Centre"):
    return Donation.objects.create(
        donor=unit.donor,
        unit=unit,
        collected_at=when or timezone.now(),
        volume_ml=unit.volume_ml,
        bag_lot_number=unit.bag_lot_number,
        collection_site=site,
        recorded_by=staff,
    )


class GeneratorTestCase(TestCase):
    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)

    def run_report(self, slug, user=None, start=RANGE[0], end=RANGE[1]):
        return generate(slug, start, end, user or self.staff)


class EveryReportTests(GeneratorTestCase):
    """UT-44 (SRS REQ-42): each report runs over a range with its exact columns."""

    def test_every_report_returns_rows_in_its_column_order(self):
        for slug, spec in REPORTS.items():
            with self.subTest(slug=slug):
                result = self.run_report(slug)
                self.assertEqual(result.columns, spec.columns)
                self.assertEqual(result.title, spec.title)
                for row in result.rows:
                    self.assertEqual(len(row), len(spec.columns))

    def test_the_range_is_checked(self):
        with self.assertRaisesMessage(ReportError, "before the start"):
            self.run_report("registration", start=TODAY, end=TODAY - timedelta(days=1))
        with self.assertRaisesMessage(ReportError, "12 months"):
            self.run_report("registration", start=TODAY - timedelta(days=400), end=TODAY)

    def test_unknown_or_forbidden_reports_are_refused(self):
        with self.assertRaises(PermissionDenied):
            self.run_report("nonsense")
        with self.assertRaises(PermissionDenied):
            self.run_report("registration", user=make_user("donor01", Role.DONOR))


class RegistrationAndCollectionTests(GeneratorTestCase):
    def test_registration_counts_donations_and_respects_the_range(self):
        donor = make_donor(blood_group="B+")
        donate(make_unit(donor=donor), self.staff)
        rows = self.run_report("registration").rows
        self.assertEqual([r[0] for r in rows], [donor.donor_id])
        self.assertEqual(rows[0][9], 1)
        future = self.run_report(
            "registration", start=TODAY + timedelta(1), end=TODAY + timedelta(2)
        )
        self.assertEqual(future.rows, ())

    def test_collection_shows_site_and_screening_outcome(self):
        cleared = make_cleared_unit(status=Status.QUARANTINED)
        pending = make_unit()
        donate(cleared, self.staff, site="CMP1000001")
        donate(pending, self.staff)
        old = make_unit()
        donate(old, self.staff, when=timezone.now() - timedelta(days=60))
        rows = {r[0]: r for r in self.run_report("collection").rows}
        self.assertEqual(set(rows), {cleared.unit_id, pending.unit_id})
        self.assertEqual(rows[cleared.unit_id][6], "CMP1000001")
        self.assertEqual(rows[cleared.unit_id][8], "Cleared")
        self.assertEqual(rows[pending.unit_id][8], "Pending")

    def test_screening_outcome(self):
        clean = [(name, "Non-Reactive") for name in TestName.values]
        self.assertEqual(screening_outcome(clean), "Cleared")
        self.assertEqual(screening_outcome(clean[:2]), "Pending")
        self.assertEqual(screening_outcome([(TestName.values[0], "Reactive")]), "Reactive")


class InventoryAndExpiryTests(GeneratorTestCase):
    def test_inventory_counts_by_group_and_component(self):
        donor = make_donor(blood_group="O-")
        make_cleared_unit(donor=donor, expiry_date=TODAY + timedelta(days=3))
        make_cleared_unit(donor=donor, expiry_date=TODAY + timedelta(days=30))
        make_cleared_unit(donor=donor, status=Status.RESERVED)
        make_unit(donor=donor)
        make_cleared_unit(donor=donor, status=Status.ISSUED)
        rows = self.run_report("inventory").rows
        self.assertEqual(len(rows), 1)
        group, component, available, reserved, quarantined, near, expired, *_rest = rows[0]
        self.assertEqual((group, component), ("O-", "Whole Blood"))
        self.assertEqual((available, reserved, quarantined, near, expired), (2, 1, 1, 1, 0))
        self.assertEqual(rows[0][8], TODAY + timedelta(days=3))
        self.assertEqual(rows[0][9], 900)

    def test_expiry_lists_units_expiring_in_range_with_who_moved_them(self):
        unit = make_cleared_unit(expiry_date=TODAY + timedelta(days=2))
        unit.transition_to(Status.DISCARDED, by=self.staff, reason="Bag damaged")
        make_cleared_unit(expiry_date=TODAY + timedelta(days=200))
        rows = self.run_report("expiry", end=TODAY + timedelta(days=10)).rows
        self.assertEqual([r[0] for r in rows], [unit.unit_id])
        self.assertEqual(rows[0][5], 2)
        self.assertEqual(rows[0][7], Status.DISCARDED)
        self.assertEqual(rows[0][9], "staff01")


class RequestAndCampTests(GeneratorTestCase):
    def test_hospital_users_see_only_their_own_requests(self):
        """UT-46 (SRS REQ-44)."""
        own = make_hospital_user("hosp01")
        other = make_hospital_user("hosp02", hospital=make_hospital(licence_number="KA-H-0002"))
        mine = make_request(own, status=RequestStatus.APPROVED)
        theirs = make_request(other)
        as_hospital = {r[0] for r in self.run_report("request-issue", user=own).rows}
        self.assertEqual(as_hospital, {mine.request_id})
        as_staff = {r[0] for r in self.run_report("request-issue").rows}
        self.assertEqual(as_staff, {mine.request_id, theirs.request_id})

    def test_camp_performance(self):
        camp = Camp.objects.create(
            camp_id="CMP1000001",
            name="College camp",
            venue_address="Hall",
            camp_date=TODAY - timedelta(days=1),
            start_time=time(9),
            end_time=time(15),
            organiser_name="Organiser",
            organiser_contact="9000000000",
            target_units=4,
            created_by=self.staff,
        )
        donors = [make_donor(), make_donor()]
        for donor in donors:
            Enrolment.objects.create(camp=camp, donor=donor)
        donate(make_unit(donor=donors[0]), self.staff, site=camp.camp_id)
        row = self.run_report("camp").rows[0]
        self.assertEqual(row[0], camp.camp_id)
        self.assertEqual(row[5:], (2, 1, 4, 1, "25.0%"))


class FormatTests(TestCase):
    def test_aware_times_are_shown_in_local_time(self):
        utc = datetime(2026, 11, 3, 20, 0, tzinfo=UTC)
        self.assertEqual(format_value(utc), "04-11-2026 01:30:00")


class ReportScreenTests(TestCase):
    """IT-24, UT-45 and ST-23 (SRS REQ-42 to REQ-44)."""

    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)
        donor = make_donor(blood_group="A+")
        clear_screening(make_unit(donor=donor))

    def url(self, slug, **params):
        params.setdefault("start", f"{RANGE[0]:%Y-%m-%d}")
        params.setdefault("end", f"{RANGE[1]:%Y-%m-%d}")
        return (
            reverse("reports:run", args=[slug])
            + "?"
            + "&".join(f"{k}={v}" for k, v in params.items())
        )

    def test_the_index_lists_only_allowed_reports(self):
        self.client.force_login(make_hospital_user())
        response = self.client.get(reverse("reports:index"))
        self.assertContains(response, "Hospital Request and Issue Report")
        self.assertNotContains(response, "Donor Registration Report")

    def test_a_report_on_screen_matches_its_csv_export(self):
        self.client.force_login(self.staff)
        page = self.client.get(self.url("registration"))
        self.assertEqual(page.status_code, 200)
        export = self.client.get(self.url("registration", format="csv"))
        self.assertEqual(export["Content-Type"], "text/csv")
        lines = list(csv.reader(io.StringIO(export.content.decode())))
        self.assertEqual(lines[0][:2], ["Report", "Donor Registration Report"])
        self.assertEqual(lines[2][:2], ["Generated by", "staff01"])
        header = lines.index(list(REPORTS["registration"].columns))
        self.assertEqual(lines[header + 1 :], page.context["rows"])

    def test_pdf_export(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url("inventory", format="pdf"))
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertIn("inventory-", response["Content-Disposition"])

    def test_hospital_users_and_donors_cannot_open_other_reports(self):
        self.client.force_login(make_hospital_user())
        self.assertEqual(self.client.get(self.url("registration")).status_code, 403)
        self.assertEqual(self.client.get(self.url("request-issue")).status_code, 200)
        self.client.force_login(make_user("donor01", Role.DONOR))
        self.assertEqual(self.client.get(reverse("reports:index")).status_code, 403)

    def test_a_bad_range_shows_the_reason(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url("registration", start="2026-12-01", end="2026-11-01"))
        self.assertContains(response, "before the start date")

    def test_the_first_visit_offers_the_last_30_days(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("reports:run", args=["camp"]))
        self.assertEqual(response.context["form"].initial["end"], TODAY)
        self.assertIsNone(response.context["result"])
