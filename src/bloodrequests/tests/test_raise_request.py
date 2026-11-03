import re
from datetime import timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_hospital, make_user
from audit.models import AuditEntry, Event
from bloodrequests.models import BloodRequest, RequestStatus
from bloodrequests.services import RequestError, create_request, generate_request_id
from inventory.models import Status
from inventory.tests.helpers import make_unit

from .helpers import make_hospital_user, make_request

NOW = timezone.now()


def good(**overrides):
    fields = {
        "blood_group": "A+",
        "component_type": "Whole Blood",
        "quantity": 2,
        "urgency": "Urgent",
        "required_by": NOW + timedelta(hours=6),
        "patient_reference": "BED-12",
    }
    fields.update(overrides)
    return fields


class CreateRequestTests(TestCase):
    """UT-25, UT-26 (SRS REQ-24, REQ-25, BR-7)."""

    def setUp(self):
        self.user = make_hospital_user()

    def test_a_valid_request_is_pending_with_a_unique_identifier(self):
        first = create_request(self.user, **good())
        second = create_request(self.user, **good())
        self.assertRegex(first.request_id, r"^REQ\d{8}$")
        self.assertNotEqual(first.request_id, second.request_id)
        self.assertEqual(first.status, RequestStatus.PENDING)
        self.assertEqual((first.quantity_issued, first.hospital), (0, self.user.hospital))

    def test_identifiers_are_sequential_and_never_reused(self):
        a, b = generate_request_id(), generate_request_id()
        self.assertEqual(int(b[3:]), int(a[3:]) + 1)

    def test_invalid_input_is_refused_and_names_the_field(self):
        cases = (
            ({"quantity": 0}, "quantity"),
            ({"quantity": -3}, "quantity"),
            ({"quantity": 51}, "quantity"),
            ({"quantity": True}, "quantity"),
            ({"quantity": 1.5}, "quantity"),
            ({"required_by": NOW - timedelta(minutes=1)}, "required_by"),
            ({"required_by": None}, "required_by"),
            ({"blood_group": "Z+"}, "blood_group"),
            ({"component_type": "Plasma-ish"}, "component_type"),
            ({"urgency": "Whenever"}, "urgency"),
            ({"patient_reference": ""}, "patient_reference"),
        )
        for overrides, field in cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(RequestError) as caught:
                    create_request(self.user, **good(**overrides))
                self.assertEqual(caught.exception.field, field)
        self.assertEqual(BloodRequest.objects.count(), 0)

    def test_only_users_of_a_registered_active_hospital_may_raise_requests(self):
        no_hospital = make_user("hosp_none", Role.HOSPITAL)
        inactive = make_hospital_user(
            "hosp_off", make_hospital(licence_number="X9", is_active=False)
        )
        staff = make_user("staff01", Role.STAFF)
        for user in (no_hospital, inactive, staff):
            with (
                self.subTest(user=user.username),
                self.assertRaisesMessage(RequestError, "active registered hospital"),
            ):
                create_request(user, **good())
        self.assertEqual(BloodRequest.objects.count(), 0)

    def test_the_request_is_audited_and_staff_are_notified(self):
        make_user("staff01", Role.STAFF)
        request = create_request(self.user, **good(urgency="Emergency"))
        entry = AuditEntry.objects.get(event=Event.REQUEST_STATUS)
        self.assertEqual(
            (entry.entity_id, entry.new_value, entry.actor),
            (request.request_id, "Pending", self.user),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("[Emergency]", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[0].to, ["staff01@example.com"])

    def test_a_mail_failure_does_not_lose_the_request(self):
        make_user("staff01", Role.STAFF)
        from unittest import mock

        with (
            mock.patch("bloodrequests.services.send_mail", side_effect=OSError("smtp down")),
            self.assertLogs("bloodrequests.services", "ERROR"),
        ):
            request = create_request(self.user, **good())
        self.assertTrue(BloodRequest.objects.filter(pk=request.pk).exists())

    def test_no_staff_means_no_mail_and_no_error(self):
        create_request(self.user, **good())
        self.assertEqual(len(mail.outbox), 0)


class RequestScreenTests(TestCase):
    """ST-13, IT-14."""

    def setUp(self):
        self.user = make_hospital_user()
        self.client.login(username="hosp01", password=STRONG_PASSWORD)

    def post_data(self, **overrides):
        when = timezone.localtime(NOW + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        data = {
            "blood_group": "A+",
            "component_type": "Whole Blood",
            "quantity": "2",
            "urgency": "Urgent",
            "required_by": when,
            "patient_reference": "bed-12",
        }
        data.update(overrides)
        return data

    def test_the_menu_offers_the_hospital_screens(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("requests:new"))
        self.assertContains(response, reverse("requests:tracker"))

    def test_raising_a_request_with_enough_stock_confirms_it(self):
        response = self.client.post(reverse("requests:new"), self.post_data(), follow=True)
        request = BloodRequest.objects.get()
        self.assertEqual(request.patient_reference, "BED-12")
        self.assertContains(response, f"Request {request.request_id} was raised")

    def test_insufficient_stock_is_accepted_with_the_available_quantity_shown(self):
        make_unit(status=Status.AVAILABLE)
        response = self.client.post(
            reverse("requests:new"), self.post_data(quantity="5"), follow=True
        )
        self.assertContains(response, "only 1 unit(s)")
        self.assertEqual(BloodRequest.objects.count(), 1)

    def test_bad_input_shows_messages_naming_the_fields(self):
        url = reverse("requests:new")
        response = self.client.post(
            url, self.post_data(quantity="0", patient_reference="Rahul Sharma")
        )
        self.assertContains(response, "error-summary")
        self.assertContains(response, "Do not enter a patient")
        past = timezone.localtime(NOW - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        self.assertContains(
            self.client.post(url, self.post_data(required_by=past)), "must be in the future"
        )
        self.assertEqual(BloodRequest.objects.count(), 0)

    def test_the_tracker_lists_only_this_hospitals_requests(self):
        mine = make_request(self.user)
        other = make_request(make_hospital_user("hosp02", make_hospital(licence_number="L2")))
        response = self.client.get(reverse("requests:tracker"))
        self.assertContains(response, mine.request_id)
        self.assertNotContains(response, other.request_id)

    def test_another_hospitals_request_is_not_found(self):
        other = make_request(make_hospital_user("hosp02", make_hospital(licence_number="L2")))
        response = self.client.get(reverse("requests:detail", args=[other.request_id]))
        self.assertEqual(response.status_code, 404)
        self.assertContains(
            self.client.get(reverse("requests:detail", args=[make_request(self.user).request_id])),
            "Patient reference",
        )

    def test_an_unlinked_hospital_user_is_told_why(self):
        make_user("hosp_none", Role.HOSPITAL)
        self.client.logout()
        self.client.login(username="hosp_none", password=STRONG_PASSWORD)
        for name in ("new", "tracker"):
            response = self.client.get(reverse(f"requests:{name}"))
            self.assertContains(response, "not linked to a hospital", status_code=403)

    def test_donors_cannot_use_the_screens_and_staff_cannot_raise(self):
        make_user("donor01", Role.DONOR)
        make_user("staff01", Role.STAFF)
        for username in ("donor01", "staff01"):
            self.client.logout()
            self.client.login(username=username, password=STRONG_PASSWORD)
            self.assertEqual(self.client.get(reverse("requests:new")).status_code, 403)
            self.assertEqual(
                self.client.post(reverse("requests:new"), self.post_data()).status_code, 403
            )
        self.assertEqual(BloodRequest.objects.count(), 0)

    def test_the_tracker_sorts_by_column(self):
        make_request(self.user, urgency="Emergency")
        make_request(self.user, urgency="Routine")
        response = self.client.get(reverse("requests:tracker"), {"sort": "urgency", "dir": "asc"})
        body = response.content.decode()
        self.assertLess(body.index("Emergency"), body.index("Routine"))
        self.assertTrue(re.search(r"REQ\d{8}", body))
