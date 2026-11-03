from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts.models import Role, User

from .helpers import make_user


class UserModelTests(TestCase):
    def test_every_user_has_exactly_one_role(self):
        user = make_user(role=Role.STAFF)
        self.assertEqual(user.role, Role.STAFF)
        self.assertEqual(user.display_role, "Blood Bank Staff")
        self.assertTrue(user.has_role(Role.STAFF, Role.ADMIN))
        self.assertFalse(user.has_role(Role.DONOR))

    def test_default_role_is_the_least_privileged(self):
        user = User.objects.create_user("plain", "plain@example.com", "Blood#Bank2026x")
        self.assertEqual(user.role, Role.DONOR)

    def test_email_is_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("noemail", "", "Blood#Bank2026x")

    def test_email_is_unique_ignoring_case(self):
        make_user("first", email="Person@Example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_user("second", email="person@example.com")

    def test_email_is_stored_lowercase(self):
        user = make_user("mixed", email="Mixed@Example.COM")
        user.refresh_from_db()
        self.assertEqual(user.email, "mixed@example.com")

    def test_superuser_is_an_administrator(self):
        admin = User.objects.create_superuser("root", "root@example.com", "Blood#Bank2026x")
        self.assertEqual(admin.role, Role.ADMIN)
        self.assertTrue(admin.is_superuser)
