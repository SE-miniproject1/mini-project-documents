from datetime import date, time, timedelta

from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_user
from audit.models import AuditEntry, Event
from camps.models import Camp, CampStatus, Enrolment
from camps.services import CampError, create_camp, eligible_from, enrol_donor, upcoming_camps
from donors.tests.helpers import PASSWORD, make_donor

TODAY = date.today()


def camp_fields(**overrides):
    fields = {
        "name": "City Hall Drive",
        "venue_address": "City Hall, MG Road",
        "camp_date": TODAY + timedelta(days=10),
        "start_time": time(9, 0),
        "end_time": time(16, 0),
        "organiser_name": "Rotary Club",
        "organiser_contact": "9876543210",
        "target_units": 100,
    }
    fields.update(overrides)
    return fields


def make_camp(user, **overrides):
    return create_camp(user, **camp_fields(**overrides))


class CreateCampTests(TestCase):
    """UT-34, UT-35 (SRS REQ-32, REQ-33)."""

    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)

    def test_a_valid_camp_is_scheduled_with_a_unique_id_and_audited(self):
        first = create_camp(self.staff, **camp_fields())
        second = create_camp(self.staff, **camp_fields(name="Other"))
        self.assertRegex(first.camp_id, r"^CMP\d{7}$")
        self.assertNotEqual(first.camp_id, second.camp_id)
        self.assertEqual((first.status, first.units_collected), (CampStatus.SCHEDULED, None))
        self.assertTrue(
            AuditEntry.objects.filter(event=Event.CONFIG_CHANGE, entity_id=first.camp_id).exists()
        )

    def test_today_is_allowed_but_the_past_is_not(self):
        create_camp(self.staff, **camp_fields(camp_date=TODAY))
        with self.assertRaises(CampError) as caught:
            create_camp(self.staff, **camp_fields(camp_date=TODAY - timedelta(days=1)))
        self.assertEqual(caught.exception.field, "camp_date")

    def test_end_time_must_be_after_start_time_and_target_positive(self):
        for overrides, field in (
            ({"end_time": time(9, 0)}, "end_time"),
            ({"end_time": time(8, 0)}, "end_time"),
            ({"target_units": 0}, "target_units"),
        ):
            with self.subTest(overrides=overrides), self.assertRaises(CampError) as caught:
                create_camp(self.staff, **camp_fields(**overrides))
            self.assertEqual(caught.exception.field, field)
        self.assertEqual(Camp.objects.count(), 0)

    def test_the_database_enforces_the_time_rule_too(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Camp.objects.create(
                camp_id="CMP9999999",
                created_by=self.staff,
                **camp_fields(end_time=time(8, 0)),
            )


class ListingTests(TestCase):
    """UT-36 (SRS REQ-34)."""

    def test_only_scheduled_future_camps_in_date_order(self):
        staff = make_user("staff01", Role.STAFF)
        later = create_camp(
            staff, **camp_fields(camp_date=TODAY + timedelta(days=20), name="Later")
        )
        sooner = create_camp(
            staff, **camp_fields(camp_date=TODAY + timedelta(days=3), name="Sooner")
        )
        done = create_camp(staff, **camp_fields(name="Done"))
        cancelled = create_camp(staff, **camp_fields(name="Cancelled"))
        Camp.objects.filter(pk=done.pk).update(status=CampStatus.COMPLETED)
        Camp.objects.filter(pk=cancelled.pk).update(status=CampStatus.CANCELLED)
        past = create_camp(staff, **camp_fields(camp_date=TODAY, name="Past"))
        Camp.objects.filter(pk=past.pk).update(camp_date=TODAY - timedelta(days=1))
        self.assertEqual(list(upcoming_camps()), [sooner, later])


class EnrolmentTests(TestCase):
    """UT-37, IT-19 (SRS REQ-35)."""

    def setUp(self):
        self.camp = make_camp(make_user("staff01", Role.STAFF))

    def test_an_eligible_donor_is_enrolled_and_confirmed_by_email(self):
        donor = make_donor()
        with self.captureOnCommitCallbacks(execute=True):
            enrol_donor(self.camp, donor)
        self.assertTrue(Enrolment.objects.filter(camp=self.camp, donor=donor).exists())
        self.assertEqual(mail.outbox[-1].to, [donor.email])
        self.assertIn("City Hall Drive", mail.outbox[-1].body)

    def test_a_recent_donor_who_will_be_eligible_by_the_camp_date_is_accepted(self):
        donor = make_donor(last_donation_date=self.camp.camp_date - timedelta(days=90))
        enrol_donor(self.camp, donor)

    def test_a_donor_not_eligible_until_after_the_camp_is_refused_with_the_date(self):
        donor = make_donor(last_donation_date=self.camp.camp_date - timedelta(days=60))
        expected = self.camp.camp_date + timedelta(days=30)
        with self.assertRaises(CampError) as caught:
            enrol_donor(self.camp, donor)
        self.assertIn(f"{expected:%d-%m-%Y}", str(caught.exception))
        self.assertFalse(Enrolment.objects.exists())

    def test_deferral_cases(self):
        permanent = make_donor(eligibility_status="Permanently Deferred")
        with self.assertRaisesMessage(CampError, "cannot donate"):
            enrol_donor(self.camp, permanent)
        no_date = make_donor(eligibility_status="Temporarily Deferred")
        with self.assertRaisesMessage(CampError, "temporarily deferred"):
            enrol_donor(self.camp, no_date)
        late = make_donor(
            eligibility_status="Temporarily Deferred",
            deferral_review_date=self.camp.camp_date + timedelta(days=5),
        )
        with self.assertRaisesMessage(CampError, "become eligible on"):
            enrol_donor(self.camp, late)
        early = make_donor(
            eligibility_status="Temporarily Deferred",
            deferral_review_date=self.camp.camp_date - timedelta(days=1),
        )
        enrol_donor(self.camp, early)
        self.assertEqual(eligible_from(make_donor()), None)

    def test_a_deactivated_donor_cannot_enrol(self):
        with self.assertRaisesMessage(CampError, "deactivated"):
            enrol_donor(self.camp, make_donor(is_active=False))

    def test_enrolling_twice_or_in_a_closed_camp_is_refused(self):
        donor = make_donor()
        enrol_donor(self.camp, donor)
        with self.assertRaisesMessage(CampError, "already enrolled"):
            enrol_donor(self.camp, donor)
        Camp.objects.filter(pk=self.camp.pk).update(status=CampStatus.COMPLETED)
        self.camp.refresh_from_db()
        with self.assertRaisesMessage(CampError, "not open"):
            enrol_donor(self.camp, make_donor())
        self.assertEqual(Enrolment.objects.count(), 1)

    def test_a_camp_that_has_already_happened_is_not_open(self):
        with self.assertRaisesMessage(CampError, "not open"):
            enrol_donor(self.camp, make_donor(), today=self.camp.camp_date + timedelta(days=1))


class CampScreenTests(TestCase):
    """ST-17, ST-18, IT-18."""

    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)
        self.donor = make_donor()

    def staff_login(self):
        self.client.login(username="staff01", password=STRONG_PASSWORD)

    def donor_login(self, donor=None):
        self.client.login(username=(donor or self.donor).donor_id, password=PASSWORD)

    def post_data(self, **overrides):
        data = {
            "name": "Campus Drive",
            "venue_address": "Main Auditorium",
            "camp_date": (TODAY + timedelta(days=7)).isoformat(),
            "start_time": "09:00",
            "end_time": "15:00",
            "organiser_name": "NSS Unit",
            "organiser_contact": "9000000001",
            "target_units": "80",
        }
        data.update(overrides)
        return data

    def test_staff_schedule_a_camp_and_the_donor_sees_it(self):
        self.staff_login()
        response = self.client.post(reverse("camps:new"), self.post_data(), follow=True)
        self.assertContains(response, "was scheduled as CMP")
        self.assertContains(self.client.get(reverse("camps:manage")), "Campus Drive")
        self.client.logout()
        self.donor_login()
        self.assertContains(self.client.get(reverse("camps:list")), "Campus Drive")

    def test_invalid_schedules_are_refused_with_messages(self):
        self.staff_login()
        url = reverse("camps:new")
        past = (TODAY - timedelta(days=1)).isoformat()
        self.assertContains(
            self.client.post(url, self.post_data(camp_date=past)), "cannot be in the past"
        )
        self.assertContains(
            self.client.post(url, self.post_data(end_time="08:00")), "later than the start time"
        )
        self.assertContains(
            self.client.post(url, self.post_data(organiser_contact="12ab")), "10-digit"
        )
        self.assertContains(
            self.client.post(url, self.post_data(target_units="0")), "error-summary"
        )
        self.assertEqual(Camp.objects.count(), 0)

    def test_a_donor_enrols_from_the_listing(self):
        camp = create_camp(self.staff, **camp_fields())
        self.donor_login()
        response = self.client.post(reverse("camps:enrol", args=[camp.camp_id]), follow=True)
        self.assertContains(response, "You are enrolled in City Hall Drive")
        self.assertContains(response, "Enrolled</td>")
        self.assertNotContains(response, ">Enrol</button>")

    def test_an_ineligible_donor_sees_the_date_they_become_eligible(self):
        camp = create_camp(self.staff, **camp_fields())
        recent = make_donor(last_donation_date=camp.camp_date - timedelta(days=10))
        self.donor_login(recent)
        response = self.client.post(reverse("camps:enrol", args=[camp.camp_id]), follow=True)
        self.assertContains(response, "You become eligible on")
        self.assertFalse(Enrolment.objects.exists())

    def test_staff_see_who_enrolled(self):
        camp = create_camp(self.staff, **camp_fields())
        enrol_donor(camp, self.donor)
        self.staff_login()
        response = self.client.get(reverse("camps:detail", args=[camp.camp_id]))
        self.assertContains(response, self.donor.donor_id)
        self.assertContains(response, "Enrolled donors (1)")

    def test_manage_can_show_closed_camps(self):
        camp = create_camp(self.staff, **camp_fields())
        Camp.objects.filter(pk=camp.pk).update(status=CampStatus.COMPLETED)
        self.staff_login()
        self.assertNotContains(self.client.get(reverse("camps:manage")), camp.name)
        self.assertContains(self.client.get(reverse("camps:manage"), {"show": "all"}), camp.name)

    def test_role_boundaries(self):
        camp = create_camp(self.staff, **camp_fields())
        self.donor_login()
        for name, args in (("manage", []), ("new", []), ("detail", [camp.camp_id])):
            self.assertEqual(self.client.get(reverse(f"camps:{name}", args=args)).status_code, 403)
        self.client.logout()
        make_user("hosp01", Role.HOSPITAL)
        self.client.login(username="hosp01", password=STRONG_PASSWORD)
        self.assertEqual(self.client.get(reverse("camps:list")).status_code, 403)
        self.assertEqual(
            self.client.post(reverse("camps:enrol", args=[camp.camp_id])).status_code, 403
        )
        self.client.logout()
        self.staff_login()
        self.assertEqual(self.client.get(reverse("camps:list")).status_code, 403)

    def test_the_menus_link_the_camp_screens(self):
        self.staff_login()
        self.assertContains(self.client.get(reverse("home")), reverse("camps:manage"))
        self.client.logout()
        self.donor_login()
        self.assertContains(self.client.get(reverse("home")), reverse("camps:list"))
