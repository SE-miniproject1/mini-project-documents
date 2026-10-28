import subprocess
import sys
from datetime import timedelta
from pathlib import Path

from django.contrib.auth.password_validation import validate_password
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts import lockout
from accounts.models import User

from .helpers import STRONG_PASSWORD, make_user

SRC = Path(__file__).resolve().parents[2]
LOGIN = "accounts:login"


class PublicAccessTests(TestCase):
    """NFR-SEC1: nothing except the sign-in, reset and health pages is public."""

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f"{reverse(LOGIN)}?next=/")

    def test_login_reset_and_health_are_public(self):
        for name in (LOGIN, "accounts:password_reset", "health"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_successful_login_reaches_home(self):
        make_user("alice")
        response = self.client.post(
            reverse(LOGIN), {"username": "alice", "password": STRONG_PASSWORD}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alice")

    def test_logout_requires_post(self):
        make_user("alice")
        self.client.login(username="alice", password=STRONG_PASSWORD)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)


class PasswordPolicyTests(TestCase):
    """SV-01 (NFR-SEC3)."""

    def test_weak_and_compromised_passwords_are_rejected(self):
        # password1! is long enough and has a letter, digit and symbol, so only the
        # compromised-password list rejects it.
        for bad in (
            "short1!",
            "longenoughbutnodigits!",
            "password1!",
            "12345678901!",
            "abcdefghijk1",
        ):
            with self.assertRaises(ValidationError, msg=bad):
                validate_password(bad)

    def test_a_strong_password_is_accepted(self):
        validate_password("Blood#Bank2026x")

    def test_change_view_enforces_the_policy(self):
        make_user("alice")
        self.client.login(username="alice", password=STRONG_PASSWORD)
        response = self.client.post(
            reverse("accounts:password_change"),
            {
                "old_password": STRONG_PASSWORD,
                "new_password1": "weakpass",
                "new_password2": "weakpass",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)


class PasswordStorageTests(TestCase):
    """SV-05 (NFR-SEC2): salted, slow hashes only."""

    @override_settings(
        PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"],
    )
    def test_identical_passwords_get_different_salted_hashes(self):
        first = make_user("one")
        second = make_user("two")
        self.assertTrue(first.password.startswith("pbkdf2_sha256$"))
        self.assertNotEqual(first.password, second.password)
        self.assertNotIn(STRONG_PASSWORD, first.password)


class LockoutTests(TestCase):
    """SV-02 (NFR-SEC4)."""

    def setUp(self):
        self.user = make_user("alice")

    def _attempt(self, password):
        return self.client.post(reverse(LOGIN), {"username": "alice", "password": password})

    def test_five_failures_lock_the_account_even_for_the_right_password(self):
        with self.captureOnCommitCallbacks(execute=True):
            for _ in range(5):
                self._attempt("wrong-password")
        self.user.refresh_from_db()
        self.assertTrue(lockout.is_locked(self.user))
        response = self._attempt(STRONG_PASSWORD)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(response, "locked after repeated failed sign-ins")

    def test_the_holder_is_emailed_when_the_account_locks(self):
        with self.captureOnCommitCallbacks(execute=True):
            for _ in range(5):
                self._attempt("wrong-password")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["alice@example.com"])
        self.assertIn("locked", mail.outbox[0].subject.lower())

    def test_the_lock_ends_after_fifteen_minutes(self):
        with self.captureOnCommitCallbacks(execute=True):
            for _ in range(5):
                self._attempt("wrong-password")
        self.user.refresh_from_db()
        later = timezone.now() + timedelta(minutes=15, seconds=1)
        self.assertFalse(lockout.is_locked(self.user, now=later))
        User.objects.filter(pk=self.user.pk).update(
            locked_until=timezone.now() - timedelta(seconds=1)
        )
        self._attempt(STRONG_PASSWORD)
        self.assertIn("_auth_user_id", self.client.session)

    def test_four_failures_do_not_lock(self):
        for _ in range(4):
            self._attempt("wrong-password")
        self.user.refresh_from_db()
        self.assertFalse(lockout.is_locked(self.user))
        self.assertEqual(self.user.failed_login_count, 4)

    def test_a_successful_login_resets_the_count(self):
        for _ in range(3):
            self._attempt("wrong-password")
        self._attempt(STRONG_PASSWORD)
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_count, 0)

    def test_unknown_usernames_do_not_error_or_reveal_anything(self):
        response = self.client.post(reverse(LOGIN), {"username": "nobody", "password": "x"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "locked")

    def test_a_mail_failure_does_not_break_sign_in(self):
        with override_settings(EMAIL_BACKEND="django.core.mail.backends.dummy.NoSuchBackend"):
            with self.captureOnCommitCallbacks(execute=True):
                for _ in range(5):
                    self._attempt("wrong-password")
        self.user.refresh_from_db()
        self.assertTrue(lockout.is_locked(self.user))


class SessionTests(TestCase):
    """SV-03 (NFR-SEC11)."""

    def setUp(self):
        make_user("alice")

    def test_expiry_is_thirty_minutes_and_slides_with_activity(self):
        self.client.login(username="alice", password=STRONG_PASSWORD)
        self.client.get(reverse("home"))
        self.assertAlmostEqual(self.client.session.get_expiry_age(), 30 * 60, delta=5)

    def test_replaying_a_session_cookie_after_logout_is_refused(self):
        self.client.login(username="alice", password=STRONG_PASSWORD)
        stolen = self.client.cookies["sessionid"].value
        self.client.post(reverse("accounts:logout"))
        replay = Client()
        replay.cookies["sessionid"] = stolen
        self.assertEqual(replay.get(reverse("home")).status_code, 302)

    def test_a_password_change_ends_every_other_session(self):
        first, second = Client(), Client()
        first.login(username="alice", password=STRONG_PASSWORD)
        second.login(username="alice", password=STRONG_PASSWORD)
        response = first.post(
            reverse("accounts:password_change"),
            {
                "old_password": STRONG_PASSWORD,
                "new_password1": "Another#Pass2026",
                "new_password2": "Another#Pass2026",
            },
        )
        self.assertRedirects(response, reverse("accounts:password_change_done"))
        self.assertEqual(first.get(reverse("home")).status_code, 200)
        self.assertEqual(second.get(reverse("home")).status_code, 302)


class CookieAndTransportSettingsTests(TestCase):
    def test_cookie_flags_in_development(self):
        from django.conf import settings

        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SAMESITE, "Lax")
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, "Lax")

    def test_production_turns_on_secure_cookies_https_and_hsts(self):
        code = (
            "import bbms.settings as s;"
            "print(s.SESSION_COOKIE_SECURE, s.CSRF_COOKIE_SECURE, s.SECURE_SSL_REDIRECT,"
            " s.SECURE_HSTS_SECONDS > 0)"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=SRC,
            env={"BBMS_ENV": "production", "DJANGO_SECRET_KEY": "x" * 50, "PATH": ""},
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), ["True"] * 4)


class PasswordResetTests(TestCase):
    def test_reset_request_sends_an_email_for_a_known_address(self):
        make_user("alice")
        response = self.client.post(
            reverse("accounts:password_reset"), {"email": "alice@example.com"}
        )
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/password/reset/", mail.outbox[0].body)

    def test_unknown_address_gets_the_same_response_and_no_email(self):
        response = self.client.post(
            reverse("accounts:password_reset"), {"email": "no@example.com"}
        )
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)
