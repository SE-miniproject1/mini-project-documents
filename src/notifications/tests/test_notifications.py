import urllib.error
from datetime import date, datetime, time, timedelta
from io import StringIO
from unittest import mock

from django.core import mail
from django.core.management import call_command
from django.db import transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import Role
from accounts.tests.helpers import make_user
from camps.models import Camp, Enrolment
from core import config
from donors.models import Eligibility
from donors.tests.helpers import make_donor
from inventory.tests.helpers import make_cleared_unit
from notifications.dispatcher import dispatch_due, enqueue
from notifications.models import Channel, Kind, Notification, NotificationStatus
from notifications.sms import HttpBackend, LocmemBackend, SMSError
from notifications.tasks.reminders import queue_camp_reminders, queue_eligibility_reminders
from notifications.tasks.shortage import queue_shortage_appeals, short_groups

LOCMEM = override_settings(
    BBMS_SMS_BACKEND="notifications.sms.LocmemBackend",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)


def queue_one(donor=None, **kwargs):
    donor = donor or make_donor()
    return enqueue(
        Kind.ELIGIBILITY, donor, subject="Subject", body="Body text", sms_body="SMS", **kwargs
    )


@LOCMEM
class DispatcherTests(TestCase):
    """UT-41 (SRS REQ-39)."""

    def setUp(self):
        LocmemBackend.outbox = []

    def test_a_message_goes_by_sms_when_the_gateway_accepts_it(self):
        note = queue_one()
        self.assertEqual(dispatch_due(), 1)
        note.refresh_from_db()
        self.assertEqual(note.status, NotificationStatus.SENT)
        self.assertEqual(note.sent_via, Channel.SMS)
        self.assertEqual(note.gateway_status, "accepted")
        self.assertEqual(LocmemBackend.outbox, [(note.mobile_number, "SMS")])
        self.assertEqual(mail.outbox, [])

    def test_sms_is_tried_three_times_at_increasing_intervals_then_email(self):
        note = queue_one()
        start = timezone.now()
        waits = []
        with mock.patch.object(LocmemBackend, "send", side_effect=SMSError("gateway down")) as gw:
            now = start
            for _ in range(3):
                self.assertEqual(dispatch_due(now=now), 1)
                note.refresh_from_db()
                if note.status == NotificationStatus.QUEUED:
                    waits.append(note.next_attempt_at - now)
                    # Nothing is retried before its time.
                    self.assertEqual(dispatch_due(now=note.next_attempt_at - timedelta(1)), 0)
                    now = note.next_attempt_at
        self.assertEqual(gw.call_count, 3)
        self.assertEqual(len(waits), 2)
        self.assertLess(waits[0], waits[1])
        self.assertEqual(note.status, NotificationStatus.SENT)
        self.assertEqual(note.sent_via, Channel.EMAIL)
        self.assertEqual(note.sms_attempts, 3)
        self.assertIn("SMS attempt 3: gateway down", note.last_error)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [note.email])
        self.assertEqual(mail.outbox[0].alternatives[0][1], "text/html")  # SRS CI-4

    def test_a_donor_without_a_mobile_number_is_emailed(self):
        note = queue_one(make_donor(mobile_number=""))
        self.assertEqual(note.channel, Channel.EMAIL)
        dispatch_due()
        note.refresh_from_db()
        self.assertEqual(note.sent_via, Channel.EMAIL)
        self.assertEqual(LocmemBackend.outbox, [])

    def test_a_message_that_cannot_be_delivered_any_way_is_marked_failed(self):
        note = queue_one(make_donor(mobile_number=""))
        far = timezone.now() + timedelta(days=1)
        with mock.patch("notifications.dispatcher._send_email", side_effect=OSError("smtp")):
            for day in range(3):
                dispatch_due(now=far + timedelta(days=day))
        note.refresh_from_db()
        self.assertEqual(note.status, NotificationStatus.FAILED)
        self.assertEqual(note.email_attempts, 3)
        self.assertEqual(dispatch_due(now=far), 0)

    def test_a_sent_message_is_never_sent_again(self):
        queue_one()
        dispatch_due()
        self.assertEqual(dispatch_due(), 0)
        self.assertEqual(len(LocmemBackend.outbox), 1)

    def test_a_dedup_key_queues_a_message_only_once(self):
        donor = make_donor()
        self.assertIsNotNone(queue_one(donor, dedup_key="k1"))
        self.assertIsNone(queue_one(donor, dedup_key="k1"))
        self.assertEqual(Notification.objects.count(), 1)

    def test_the_sms_text_is_cut_to_160_characters(self):
        note = enqueue(Kind.ELIGIBILITY, make_donor(), subject="s", body="b", sms_body="x" * 200)
        self.assertEqual(len(note.sms_body), 160)

    def test_the_worker_command_reports_what_it_tried(self):
        queue_one()
        out = StringIO()
        call_command("dispatch_notifications", stdout=out)
        self.assertIn("1 notification(s) tried.", out.getvalue())


@LOCMEM
class AsynchronousDispatchTests(TestCase):
    """IT-22 (SRS REQ-39, NFR-P6, CI-6)."""

    def test_queueing_never_calls_a_gateway_or_blocks_the_transaction(self):
        with mock.patch.object(LocmemBackend, "send") as gw, transaction.atomic():
            note = queue_one()
        gw.assert_not_called()
        self.assertEqual(note.status, NotificationStatus.QUEUED)
        self.assertLessEqual(note.next_attempt_at, timezone.now())

    def test_a_rolled_back_transaction_leaves_no_message(self):
        donor = make_donor()
        try:
            with transaction.atomic():
                queue_one(donor)
                raise RuntimeError("the caller failed")
        except RuntimeError:
            pass
        self.assertFalse(Notification.objects.exists())


class EligibilityReminderTests(TestCase):
    """UT-42 and ST-21 (SRS REQ-40)."""

    def setUp(self):
        self.today = date(2026, 11, 3)

    def test_only_the_donor_eligible_today_is_reminded(self):
        due = make_donor(next_eligible_date=self.today)
        make_donor(next_eligible_date=self.today + timedelta(days=5))
        self.assertEqual(queue_eligibility_reminders(self.today), 1)
        note = Notification.objects.get()
        self.assertEqual(note.donor, due)
        self.assertEqual(note.kind, Kind.ELIGIBILITY)
        self.assertIn(due.full_name, note.body)
        self.assertIn("03-11-2026", note.body)
        self.assertIn("03-11-2026", note.sms_body)

    def test_running_again_does_not_repeat_the_reminder(self):
        make_donor(next_eligible_date=self.today)
        queue_eligibility_reminders(self.today)
        self.assertEqual(queue_eligibility_reminders(self.today), 0)
        self.assertEqual(queue_eligibility_reminders(self.today + timedelta(days=1)), 0)

    def test_a_missed_day_is_caught_up_but_old_dates_are_not(self):
        make_donor(next_eligible_date=self.today - timedelta(days=2))
        make_donor(next_eligible_date=self.today - timedelta(days=60))
        self.assertEqual(queue_eligibility_reminders(self.today), 1)

    def test_the_interval_deferral_counts_but_other_deferrals_do_not(self):
        make_donor(
            next_eligible_date=self.today,
            eligibility_status=Eligibility.TEMPORARY,
            deferral_review_date=self.today,
        )
        make_donor(
            next_eligible_date=self.today,
            eligibility_status=Eligibility.TEMPORARY,
            deferral_review_date=self.today + timedelta(days=30),
        )
        make_donor(next_eligible_date=self.today, eligibility_status=Eligibility.PERMANENT)
        make_donor(next_eligible_date=self.today, is_active=False)
        self.assertEqual(queue_eligibility_reminders(self.today), 1)


class CampReminderTests(TestCase):
    """UT-42 and ST-21 (SRS REQ-40)."""

    def setUp(self):
        self.staff = make_user("staff01", Role.STAFF)
        self.now = timezone.make_aware(datetime(2026, 11, 3, 9, 0))

    def camp(self, days_ahead, at=time(8, 0), **extra):
        n = Camp.objects.count() + 1
        fields = {
            "camp_id": f"CMP{n:07d}",
            "name": f"Camp {n}",
            "venue_address": "Town Hall",
            "camp_date": self.now.date() + timedelta(days=days_ahead),
            "start_time": at,
            "end_time": time(16, 0),
            "organiser_name": "Organiser",
            "organiser_contact": "9000000000",
            "target_units": 20,
            "created_by": self.staff,
        }
        fields.update(extra)
        return Camp.objects.create(**fields)

    def test_only_the_camp_in_the_next_24_hours_sends_reminders(self):
        donor = make_donor()
        soon, later = self.camp(1), self.camp(5)
        Enrolment.objects.create(camp=soon, donor=donor)
        Enrolment.objects.create(camp=later, donor=donor)
        self.assertEqual(queue_camp_reminders(self.now), 1)
        note = Notification.objects.get()
        self.assertEqual(note.kind, Kind.CAMP_REMINDER)
        self.assertIn(donor.full_name, note.body)
        self.assertIn(f"{soon.camp_date:%d-%m-%Y}", note.body)
        self.assertNotIn(later.name, note.body)

    def test_each_enrolled_donor_gets_their_own_reminder_once(self):
        camp = self.camp(1)
        donors = [make_donor(), make_donor()]
        for donor in donors:
            Enrolment.objects.create(camp=camp, donor=donor)
        self.assertEqual(queue_camp_reminders(self.now), 2)
        self.assertEqual(queue_camp_reminders(self.now + timedelta(hours=1)), 0)
        for donor in donors:
            body = Notification.objects.get(donor=donor).body
            other = next(d for d in donors if d != donor)
            self.assertNotIn(other.full_name, body)

    def test_a_camp_already_started_or_closed_sends_nothing(self):
        Enrolment.objects.create(camp=self.camp(0, at=time(8, 0)), donor=make_donor())
        Enrolment.objects.create(camp=self.camp(1, status="Cancelled"), donor=make_donor())
        self.assertEqual(queue_camp_reminders(self.now), 0)


@override_settings(BBMS_MIN_STOCK={"O-": 10})
class ShortageAppealTests(TestCase):
    """UT-43 and IT-23 (SRS REQ-41)."""

    def setUp(self):
        self.now = timezone.now()
        for _ in range(8):
            make_cleared_unit(donor=make_donor(blood_group="O-"))
        Notification.objects.all().delete()

    def test_a_group_below_its_threshold_is_short(self):
        self.assertEqual(short_groups(), {"O-": (8, 10)})

    def test_only_eligible_donors_of_the_short_group_are_asked(self):
        before = set(Notification.objects.values_list("donor", flat=True))
        deferred = make_donor(blood_group="O-", eligibility_status=Eligibility.TEMPORARY)
        other_group = make_donor(blood_group="A+")
        asked = queue_shortage_appeals(now=self.now)
        recipients = set(
            Notification.objects.filter(kind=Kind.SHORTAGE_APPEAL).values_list("donor", flat=True)
        )
        self.assertEqual(asked, {"O-": len(recipients)})
        self.assertGreater(len(recipients), 0)
        self.assertNotIn(deferred.pk, recipients)
        self.assertNotIn(other_group.pk, recipients)
        self.assertFalse(recipients & before)

    def test_an_appeal_is_not_repeated_within_30_days(self):
        first = queue_shortage_appeals(now=self.now)["O-"]
        self.assertEqual(queue_shortage_appeals(now=self.now + timedelta(days=1)), {"O-": 0})
        Notification.objects.update(created_at=self.now - timedelta(days=31))
        self.assertEqual(queue_shortage_appeals(now=self.now), {"O-": first})

    def test_enough_stock_or_no_threshold_means_no_appeal(self):
        for _ in range(2):
            make_cleared_unit(donor=make_donor(blood_group="O-"))
        self.assertEqual(queue_shortage_appeals(now=self.now), {})
        with override_settings(BBMS_MIN_STOCK={}):
            self.assertEqual(short_groups(), {})

    def test_the_administrators_threshold_is_used(self):
        admin = make_user("admin01", Role.ADMIN)
        config.save({"min_stock.O-": 5}, by=admin)
        self.assertEqual(short_groups(), {})

    def test_the_reminder_command_queues_appeals(self):
        out = StringIO()
        call_command("send_reminders", stdout=out)
        self.assertIn("O- is below its minimum", out.getvalue())


class HttpBackendTests(TestCase):
    """SRS SI-4: HTTPS with a bearer token, and the reply's status kept."""

    def send(self, url="https://sms.example.com/v1"):
        with override_settings(BBMS_SMS_URL=url, BBMS_SMS_TOKEN="t0ken"):
            return HttpBackend().send("9800000001", "Hello")

    def test_the_message_is_posted_with_the_token(self):
        reply = mock.MagicMock()
        reply.__enter__.return_value.read.return_value = b'{"status": "queued"}'
        with mock.patch("urllib.request.urlopen", return_value=reply) as urlopen:
            self.assertEqual(self.send(), "queued")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer t0ken")
        self.assertEqual(request.data, b'{"to": "9800000001", "message": "Hello"}')

    def test_plain_http_and_network_errors_are_failures(self):
        with self.assertRaisesMessage(SMSError, "HTTPS"):
            self.send("http://sms.example.com/v1")
        with (
            mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("down")),
            self.assertRaises(SMSError),
        ):
            self.send()
