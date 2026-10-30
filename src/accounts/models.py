"""User model with exactly one role (SRS REQ-45, NFR-SEC5)."""

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.functions import Lower


class Role(models.TextChoices):
    DONOR = "donor", "Donor"
    STAFF = "staff", "Blood Bank Staff"
    HOSPITAL = "hospital", "Hospital User"
    ADMIN = "admin", "Administrator"


class BBMSUserManager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        return super()._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Every account has one role. Accounts are deactivated, never deleted (CON-6)."""

    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.DONOR)
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    objects = BBMSUserManager()
    REQUIRED_FIELDS = ["email", "role"]

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique"),
        ]

    def save(self, *args, **kwargs):
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)

    def has_role(self, *roles):
        return self.role in roles

    @property
    def display_role(self):
        return self.get_role_display()
