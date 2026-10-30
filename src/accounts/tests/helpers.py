from accounts.models import Role, User

STRONG_PASSWORD = "Blood#Bank2026x"


def make_user(username="user1", role=Role.DONOR, password=STRONG_PASSWORD, **extra):
    extra.setdefault("email", f"{username}@example.com")
    return User.objects.create_user(username=username, password=password, role=role, **extra)
