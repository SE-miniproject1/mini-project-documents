"""Load a small, repeatable data set for development, demos and manual testing.

The Test Plan assumes a deterministic seed fixture (SRS NFR-Q6): the same accounts and
the same donor IDs every time. Units are created through the real services, so the
data obeys the same safety rules as production data. Never runs in production.
"""

import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.models import Role, User
from collection.services.collect import record_collection
from collection.services.screening import PANEL, record_results, release_unit
from donors.models import Donor, Eligibility
from donors.services.id_generator import generate_donor_id

DONORS = [
    # name, blood group, weight, days since last donation to show (None = never)
    ("Ravi Kumar", "O+", "68", None),
    ("Meena Rao", "A+", "55", None),
    ("Arjun Nair", "B+", "74", None),
    ("Sunita Shah", "O-", "58", None),
    ("Karan Mehta", "AB+", "81", None),
    ("Divya Iyer", "A-", "52", None),
    ("Imran Khan", "B-", "77", None),
    ("Latha Reddy", "O+", "61", None),
    ("Vikram Singh", "A+", "70", None),
    ("Pooja Das", "AB-", "49", None),  # underweight: starts deferred
]


class Command(BaseCommand):
    help = "Load deterministic demo accounts, donors and units. Development only."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password", help="Password for every demo account. Random if omitted."
        )

    def handle(self, *args, **options):
        if settings.ENVIRONMENT == "production":
            raise CommandError("seed_demo never runs in production.")
        if User.objects.filter(username="staff01").exists():
            self.stdout.write("Demo data is already loaded. Nothing changed.")
            return

        password = options["password"] or secrets.token_urlsafe(12) + "#1a"
        accounts = {}
        for username, role in (
            ("staff01", Role.STAFF),
            ("admin01", Role.ADMIN),
            ("hosp01", Role.HOSPITAL),
        ):
            accounts[username] = User.objects.create_user(
                username,
                f"{username}@bbms.local",
                password,
                role=role,
                first_name=username.title(),
            )

        donors = [self._donor(index, row, password) for index, row in enumerate(DONORS)]
        staff = accounts["staff01"]

        # Units in every state a demo needs, all reached through the real rules.
        now = timezone.now()
        released = 0
        for offset, donor in enumerate(donors[:6]):
            donor.refresh_from_db()
            if donor.eligibility_status != Eligibility.ELIGIBLE:
                continue
            _, unit = record_collection(
                donor,
                volume_ml=450,
                bag_lot_number=f"BG-DEMO-{offset + 1:03d}",
                collection_site="Centre",
                recorded_by=staff,
                collected_at=now - timedelta(days=2 + offset),
            )
            if offset == 4:
                continue  # left in quarantine, waiting for results
            if offset == 5:
                record_results(unit, {"HIV": "Reactive"}, by=staff)  # discarded
                continue
            record_results(unit, dict.fromkeys(PANEL, "Non-Reactive"), by=staff)
            release_unit(unit, by=staff)
            released += 1

        self.stdout.write(self.style.SUCCESS("Demo data loaded."))
        self.stdout.write("  Accounts: staff01, admin01, hosp01, and donors by donor ID")
        self.stdout.write(f"  Password: {password}")
        self.stdout.write(f"  {Donor.objects.count()} donors, {released} units released")

    def _donor(self, index, row, password):
        name, group, weight, _ = row
        donor_id = generate_donor_id()
        slug = name.lower().replace(" ", ".")
        user = User.objects.create_user(
            donor_id,
            f"{slug}@bbms.local",
            password,
            role=Role.DONOR,
            first_name=name.split()[0],
            last_name=name.split()[-1],
        )
        donor = Donor(
            donor_id=donor_id,
            user=user,
            full_name=name,
            date_of_birth=timezone.localdate().replace(
                year=timezone.localdate().year - (25 + index)
            ),
            gender="Female"
            if name.split()[0] in {"Meena", "Sunita", "Divya", "Latha", "Pooja"}
            else "Male",
            blood_group=group,
            mobile_number=f"98{index:08d}",
            email=f"{slug}@bbms.local",
            address_line=f"{index + 1} Demo Street",
            city="Bengaluru",
            pin_code="560001",
            weight_kg=Decimal(weight),
            emergency_contact_name="Demo Contact",
            emergency_contact_number="9000000000",
            consent_timestamp=timezone.now(),
        )
        from donors.services.eligibility import apply_result, evaluate_eligibility

        apply_result(donor, evaluate_eligibility(donor))
        donor.save()
        return donor
