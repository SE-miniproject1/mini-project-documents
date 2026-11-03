from types import SimpleNamespace

from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase

from accounts.models import Role
from reports.access import allowed_reports, can_run, hospital_scope


def user(role, hospital=None):
    return SimpleNamespace(role=role, hospital=hospital)


class ReportAccessTests(SimpleTestCase):
    """REQ-44 and NFR-SEC7: which roles may run which reports."""

    def test_staff_and_admin_may_run_all_six_reports(self):
        for role in (Role.STAFF, Role.ADMIN):
            with self.subTest(role=role):
                self.assertEqual(len(allowed_reports(user(role))), 6)

    def test_hospital_user_may_run_only_the_request_and_issue_report(self):
        slugs = [spec.slug for spec in allowed_reports(user(Role.HOSPITAL))]
        self.assertEqual(slugs, ["request-issue"])

    def test_hospital_user_is_refused_reports_that_name_donors(self):
        for slug in ("registration", "collection", "expiry", "inventory", "camp"):
            with self.subTest(slug=slug):
                self.assertFalse(can_run(user(Role.HOSPITAL), slug))

    def test_donor_may_run_no_report(self):
        self.assertEqual(allowed_reports(user(Role.DONOR)), [])
        self.assertFalse(can_run(user(Role.DONOR), "request-issue"))

    def test_unknown_report_is_refused(self):
        self.assertFalse(can_run(user(Role.ADMIN), "no-such-report"))


class HospitalScopeTests(SimpleTestCase):
    """UT-46: a hospital user is limited to their own hospital."""

    def test_staff_and_admin_are_not_restricted(self):
        for role in (Role.STAFF, Role.ADMIN):
            self.assertIsNone(hospital_scope(user(role)))

    def test_hospital_user_is_limited_to_their_own_hospital(self):
        apollo = SimpleNamespace(name="Apollo", is_active=True)
        self.assertIs(hospital_scope(user(Role.HOSPITAL, apollo)), apollo)

    def test_hospital_user_without_a_hospital_is_refused(self):
        with self.assertRaises(PermissionDenied):
            hospital_scope(user(Role.HOSPITAL, None))

    def test_hospital_user_of_an_inactive_hospital_is_refused(self):
        closed = SimpleNamespace(name="Closed", is_active=False)
        with self.assertRaises(PermissionDenied):
            hospital_scope(user(Role.HOSPITAL, closed))
