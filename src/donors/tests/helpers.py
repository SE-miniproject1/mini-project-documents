from datetime import date, timedelta

from django.utils import timezone

from accounts.models import Role, User
from donors.models import Donor
from donors.services.id_generator import generate_donor_id

PASSWORD = "Blood#Bank2026x"


def years_ago(years, today=None):
    today = today or date.today()
    try:
        return today.replace(year=today.year - years)
    except ValueError:  # 29 February
        return today.replace(year=today.year - years, day=28)


def registration_data(**overrides):
    data = {
        "full_name": "Ravi Kumar",
        "date_of_birth": years_ago(28).isoformat(),
        "gender": "Male",
        "blood_group": "O+",
        "mobile_number": "9880011223",
        "email": "ravi.k@example.com",
        "address_line": "12 MG Road",
        "city": "Bengaluru",
        "pin_code": "560085",
        "weight_kg": "68",
        "emergency_contact_name": "Sunita Kumar",
        "emergency_contact_number": "9880099887",
        "password1": PASSWORD,
        "password2": PASSWORD,
        "consent": "on",
    }
    data.update(overrides)
    return data


_counter = iter(range(1, 10_000))


def make_donor(**overrides):
    """A donor straight in the database, without going through the registration form."""
    n = next(_counter)
    fields = {
        "full_name": f"Donor {n}",
        "date_of_birth": years_ago(30),
        "gender": "Female",
        "blood_group": "A+",
        "mobile_number": f"98{n:08d}",
        "email": f"donor{n}@example.com",
        "address_line": "1 Test Street",
        "city": "Bengaluru",
        "pin_code": "560001",
        "weight_kg": 62,
        "emergency_contact_name": "Contact",
        "emergency_contact_number": "9000000000",
        "consent_timestamp": timezone.now() - timedelta(days=1),
    }
    fields.update(overrides)
    if "donor_id" not in fields:
        fields["donor_id"] = generate_donor_id()
    if "user" not in fields:
        fields["user"] = User.objects.create_user(
            fields["donor_id"], fields["email"], PASSWORD, role=Role.DONOR
        )
    return Donor.objects.create(**fields)
