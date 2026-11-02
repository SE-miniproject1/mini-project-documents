from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEntry, Event

from ..models import Hospital, Role, User
from .helpers import STRONG_PASSWORD, make_hospital, make_user


class AdminTestCase(TestCase):
    def setUp(self):
        self.admin = make_user("admin1", Role.ADMIN)
        self.client.login(username="admin1", password=STRONG_PASSWORD)


class UserAdminTests(AdminTestCase):
    """UC17 (SRS REQ-45)."""

    def new_user_data(self, **overrides):
        data = {
            "username": "staff02",
            "email": "staff02@example.com",
            "role": Role.STAFF,
            "password": "Another#Pass2026y",
        }
        data.update(overrides)
        return data

    def test_the_list_filters_by_role_and_search(self):
        make_user("staff01", Role.STAFF)
        make_user("hosp01", Role.HOSPITAL, hospital=make_hospital())
        url = reverse("accounts:user_admin")
        self.assertContains(self.client.get(url), "hosp01")
        response = self.client.get(url, {"role": "staff"})
        self.assertContains(response, "staff01")
        self.assertNotContains(response, "hosp01")
        self.assertContains(self.client.get(url, {"q": "HOSP"}), "City General")
        self.assertContains(self.client.get(url, {"q": "nobody"}), "No users match")

    def test_creating_a_staff_account_stores_a_hashed_password_and_audits(self):
        response = self.client.post(reverse("accounts:user_create"), self.new_user_data())
        self.assertRedirects(response, reverse("accounts:user_admin"))
        user = User.objects.get(username="staff02")
        self.assertEqual(user.role, Role.STAFF)
        self.assertTrue(user.check_password("Another#Pass2026y"))
        entry = AuditEntry.objects.get(event=Event.CONFIG_CHANGE, entity_id="staff02")
        self.assertEqual((entry.new_value, entry.actor), ("staff", self.admin))

    def test_a_weak_password_or_duplicate_email_is_refused(self):
        url = reverse("accounts:user_create")
        self.assertContains(
            self.client.post(url, self.new_user_data(password="12345678")), "error-summary"
        )
        make_user("other", Role.STAFF, email="staff02@example.com")
        response = self.client.post(url, self.new_user_data())
        self.assertContains(response, "error-summary")
        self.assertFalse(User.objects.filter(username="staff02").exists())

    def test_donor_is_not_offered_when_creating_an_account(self):
        response = self.client.get(reverse("accounts:user_create"))
        self.assertNotContains(response, ">Donor<")

    def test_hospital_users_need_a_hospital_and_others_must_not_have_one(self):
        url = reverse("accounts:user_create")
        response = self.client.post(url, self.new_user_data(role=Role.HOSPITAL))
        self.assertContains(response, "must belong to a hospital")
        hospital = make_hospital()
        response = self.client.post(url, self.new_user_data(hospital=hospital.pk))
        self.assertContains(response, "Only hospital users belong to a hospital")
        response = self.client.post(
            url, self.new_user_data(role=Role.HOSPITAL, hospital=hospital.pk)
        )
        self.assertRedirects(response, reverse("accounts:user_admin"))
        self.assertEqual(User.objects.get(username="staff02").hospital, hospital)

    def test_changing_a_role_is_audited_and_applies(self):
        user = make_user("staff01", Role.STAFF)
        data = {"username": "staff01", "email": user.email, "role": Role.ADMIN, "is_active": "on"}
        self.client.post(reverse("accounts:user_edit", args=[user.pk]), data)
        user.refresh_from_db()
        self.assertEqual(user.role, Role.ADMIN)
        entry = AuditEntry.objects.get(event=Event.CONFIG_CHANGE, entity_id="staff01")
        self.assertEqual((entry.previous_value, entry.new_value), ("staff/active", "admin/active"))

    def test_deactivating_keeps_the_record_and_ends_sign_in(self):
        user = make_user("staff01", Role.STAFF)
        data = {"username": "staff01", "email": user.email, "role": Role.STAFF}
        self.client.post(reverse("accounts:user_edit", args=[user.pk]), data)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.client.logout()
        self.assertFalse(self.client.login(username="staff01", password=STRONG_PASSWORD))

    def test_an_administrator_cannot_demote_or_deactivate_themselves(self):
        url = reverse("accounts:user_edit", args=[self.admin.pk])
        base = {"username": "admin1", "email": self.admin.email}
        self.assertContains(
            self.client.post(url, {**base, "role": Role.STAFF, "is_active": "on"}),
            "own administrator access",
        )
        self.assertContains(
            self.client.post(url, {**base, "role": Role.ADMIN}), "own administrator access"
        )
        self.admin.refresh_from_db()
        self.assertEqual((self.admin.role, self.admin.is_active), (Role.ADMIN, True))

    def test_a_blank_password_on_edit_keeps_the_old_one(self):
        user = make_user("staff01", Role.STAFF)
        data = {
            "username": "staff01",
            "email": user.email,
            "role": Role.STAFF,
            "is_active": "on",
            "password": "",
        }
        self.client.post(reverse("accounts:user_edit", args=[user.pk]), data)
        user.refresh_from_db()
        self.assertTrue(user.check_password(STRONG_PASSWORD))

    def test_non_administrators_are_refused_everywhere(self):
        make_user("staff01", Role.STAFF)
        self.client.logout()
        self.client.login(username="staff01", password=STRONG_PASSWORD)
        for name, args in (
            ("user_admin", []),
            ("user_create", []),
            ("user_edit", [self.admin.pk]),
            ("hospital_list", []),
            ("hospital_create", []),
        ):
            self.assertEqual(
                self.client.get(reverse(f"accounts:{name}", args=args)).status_code, 403, name
            )
        self.assertEqual(
            self.client.post(reverse("accounts:user_create"), self.new_user_data()).status_code,
            403,
        )
        self.assertFalse(User.objects.filter(username="staff02").exists())


class HospitalAdminTests(AdminTestCase):
    def data(self, **overrides):
        data = {
            "name": "St Mary's",
            "address": "5 Church St",
            "licence_number": " ka-h-0002 ",
            "contact_name": "Sr Joseph",
            "contact_phone": "9000000000",
            "contact_email": "lab@stmarys.example",
        }
        data.update(overrides)
        return data

    def test_registering_a_hospital_normalises_the_licence_and_audits(self):
        response = self.client.post(reverse("accounts:hospital_create"), self.data())
        self.assertRedirects(response, reverse("accounts:hospital_list"))
        hospital = Hospital.objects.get(name="St Mary's")
        self.assertEqual(hospital.licence_number, "KA-H-0002")
        self.assertTrue(hospital.is_active)
        self.assertTrue(
            AuditEntry.objects.filter(entity_type="Hospital", entity_id="KA-H-0002").exists()
        )

    def test_the_licence_number_must_be_unique(self):
        make_hospital(licence_number="KA-H-0002")
        response = self.client.post(reverse("accounts:hospital_create"), self.data())
        self.assertContains(response, "error-summary")
        self.assertEqual(Hospital.objects.count(), 1)

    def test_the_list_sorts_and_shows_status(self):
        make_hospital(name="Zeta", licence_number="Z1")
        make_hospital(name="Alpha", licence_number="A1", is_active=False)
        response = self.client.get(
            reverse("accounts:hospital_list"), {"sort": "name", "dir": "desc"}
        )
        content = response.content.decode()
        self.assertLess(content.index("Zeta"), content.index("Alpha"))
        self.assertContains(response, "Deactivated")

    def test_deactivating_a_hospital_is_audited_and_keeps_the_record(self):
        hospital = make_hospital()
        data = {k: v for k, v in self.data(licence_number=hospital.licence_number).items()}
        self.client.post(reverse("accounts:hospital_edit", args=[hospital.pk]), data)
        hospital.refresh_from_db()
        self.assertFalse(hospital.is_active)
        entry = AuditEntry.objects.get(entity_type="Hospital")
        self.assertEqual((entry.previous_value, entry.new_value), ("active", "inactive"))

    def test_editing_without_changing_status_writes_no_status_audit(self):
        hospital = make_hospital()
        data = self.data(licence_number=hospital.licence_number, is_active="on")
        self.client.post(reverse("accounts:hospital_edit", args=[hospital.pk]), data)
        self.assertFalse(AuditEntry.objects.filter(entity_type="Hospital").exists())

    def test_inactive_hospitals_cannot_be_chosen_for_new_users(self):
        make_hospital(name="Closed Clinic", licence_number="C1", is_active=False)
        response = self.client.get(reverse("accounts:user_create"))
        self.assertNotContains(response, "Closed Clinic")
