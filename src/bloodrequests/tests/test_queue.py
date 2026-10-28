from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from accounts.tests.helpers import STRONG_PASSWORD, make_hospital, make_user
from audit.models import AuditEntry, Event
from bloodrequests.models import RequestStatus
from bloodrequests.workflow import WorkflowError, approve_request, queue, reject_request

from .helpers import make_hospital_user, make_request

REASON = "Insufficient stock of the requested group"


def hours(n):
    return timezone.now() + timedelta(hours=n)


class QueueOrderTests(TestCase):
    """UT-27 (SRS REQ-26)."""

    def test_emergency_first_then_by_required_by_ascending(self):
        user = make_hospital_user()
        routine_soon = make_request(user, urgency="Routine", required_by=hours(1))
        emergency_late = make_request(user, urgency="Emergency", required_by=hours(30))
        urgent = make_request(user, urgency="Urgent", required_by=hours(5))
        emergency_soon = make_request(user, urgency="Emergency", required_by=hours(2))
        self.assertEqual(list(queue()), [emergency_soon, emergency_late, urgent, routine_soon])

    def test_closed_requests_are_left_out_unless_asked_for(self):
        user = make_hospital_user()
        open_one = make_request(user)
        for status in (RequestStatus.REJECTED, RequestStatus.CANCELLED, RequestStatus.FULFILLED):
            make_request(user, status=status, rejection_reason="x" if status == "Rejected" else "")
        self.assertEqual(list(queue()), [open_one])
        self.assertEqual(queue(tuple(RequestStatus.values)).count(), 4)


class DecisionTests(TestCase):
    """UT-28, IT-15 (SRS REQ-27)."""

    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)
        self.request = make_request()

    def test_approve_moves_pending_to_approved_audits_and_emails_the_hospital(self):
        with self.captureOnCommitCallbacks(execute=True):
            approve_request(self.request, by=self.staff)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, RequestStatus.APPROVED)
        entry = AuditEntry.objects.get(event=Event.REQUEST_STATUS, previous_value="Pending")
        self.assertEqual((entry.new_value, entry.actor), ("Approved", self.staff))
        self.assertEqual(mail.outbox[-1].to, [self.request.requested_by.email])
        self.assertIn("approved", mail.outbox[-1].body)

    def test_rejection_needs_a_reason_from_the_list_and_tells_the_hospital(self):
        for bad in ("", "because", None):
            with (
                self.subTest(reason=bad),
                self.assertRaisesMessage(WorkflowError, "from the list"),
            ):
                reject_request(self.request, by=self.staff, reason=bad)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, RequestStatus.PENDING)
        with self.captureOnCommitCallbacks(execute=True):
            reject_request(self.request, by=self.staff, reason=REASON)
        self.request.refresh_from_db()
        self.assertEqual(
            (self.request.status, self.request.rejection_reason), ("Rejected", REASON)
        )
        self.assertIn(REASON, mail.outbox[-1].body)

    def test_only_pending_requests_can_be_decided(self):
        approve_request(self.request, by=self.staff)
        with self.assertRaisesMessage(WorkflowError, "is Approved"):
            approve_request(self.request, by=self.staff)
        with self.assertRaisesMessage(WorkflowError, "is Approved"):
            reject_request(self.request, by=self.staff, reason=REASON)

    def test_a_mail_failure_does_not_undo_the_decision(self):
        with (
            mock.patch("bloodrequests.workflow.send_mail", side_effect=OSError("down")),
            self.assertLogs("bloodrequests.workflow", "ERROR"),
            self.captureOnCommitCallbacks(execute=True),
        ):
            approve_request(self.request, by=self.staff)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, RequestStatus.APPROVED)


class QueueScreenTests(TestCase):
    """ST-14."""

    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)
        self.client.login(username="staff01", password=STRONG_PASSWORD)
        user = make_hospital_user()
        self.routine = make_request(user, urgency="Routine", required_by=hours(1))
        self.emergency = make_request(user, urgency="Emergency", required_by=hours(40))

    def test_the_queue_lists_emergency_first_and_marks_it_in_words(self):
        response = self.client.get(reverse("requests:queue"))
        body = response.content.decode()
        self.assertLess(body.index(self.emergency.request_id), body.index(self.routine.request_id))
        self.assertContains(response, "EMERGENCY")
        self.assertContains(response, 'class="emergency"')

    def test_staff_can_approve_from_the_request_page(self):
        url = reverse("requests:detail", args=[self.routine.request_id])
        self.assertContains(self.client.get(url), "Approve")
        response = self.client.post(
            reverse("requests:approve", args=[self.routine.request_id]), follow=True
        )
        self.assertContains(response, "was approved")
        self.assertNotContains(response, "<h2>Decision</h2>")

    def test_rejecting_without_a_reason_is_refused_and_with_one_is_recorded(self):
        url = reverse("requests:reject", args=[self.routine.request_id])
        response = self.client.post(url, {"reason": ""}, follow=True)
        self.assertContains(response, "Choose a reason")
        response = self.client.post(url, {"reason": REASON}, follow=True)
        self.assertContains(response, "was rejected")
        self.assertContains(response, REASON)

    def test_deciding_twice_shows_an_error_not_a_crash(self):
        url = reverse("requests:approve", args=[self.routine.request_id])
        self.client.post(url)
        self.assertContains(self.client.post(url, follow=True), "is Approved")

    def test_closed_requests_can_be_shown(self):
        reject_request(self.routine, by=self.staff, reason=REASON)
        self.assertNotContains(self.client.get(reverse("requests:queue")), self.routine.request_id)
        self.assertContains(
            self.client.get(reverse("requests:queue"), {"show": "all"}), self.routine.request_id
        )

    def test_hospital_users_and_donors_cannot_use_the_queue_or_decide(self):
        make_hospital_user("hosp_x", make_hospital(licence_number="LX"))
        make_user("donor01", Role.DONOR)
        for username in ("hosp_x", "donor01"):
            self.client.logout()
            self.client.login(username=username, password=STRONG_PASSWORD)
            self.assertEqual(self.client.get(reverse("requests:queue")).status_code, 403)
            for name in ("approve", "reject"):
                response = self.client.post(
                    reverse(f"requests:{name}", args=[self.routine.request_id]), {"reason": REASON}
                )
                self.assertEqual(response.status_code, 403)
        self.routine.refresh_from_db()
        self.assertEqual(self.routine.status, RequestStatus.PENDING)

    def test_the_hospital_sees_the_rejection_reason_but_no_decision_buttons(self):
        reject_request(self.routine, by=self.staff, reason=REASON)
        self.client.logout()
        self.client.login(username="hosp01", password=STRONG_PASSWORD)
        response = self.client.get(reverse("requests:detail", args=[self.routine.request_id]))
        self.assertContains(response, REASON)
        self.assertNotContains(response, "Approve")

    def test_the_menu_links_the_queue_for_staff(self):
        self.assertContains(self.client.get(reverse("home")), reverse("requests:queue"))
