from accounts.models import Hospital, Role, User

STRONG_PASSWORD = "Blood#Bank2026x"


def make_user(username="user1", role=Role.DONOR, password=STRONG_PASSWORD, **extra):
    extra.setdefault("email", f"{username}@example.com")
    return User.objects.create_user(username=username, password=password, role=role, **extra)


def make_hospital(**overrides):
    fields = {
        "name": "City General",
        "address": "1 MG Road, Bengaluru",
        "licence_number": "KA-H-0001",
        "contact_name": "Dr Rao",
        "contact_phone": "9876543210",
        "contact_email": "bloodbank@citygeneral.example",
    }
    fields.update(overrides)
    return Hospital.objects.create(**fields)
