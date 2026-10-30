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


class Hospital(models.Model):
    """A hospital that may raise blood requests (SRS REQ-45). Deactivated, never deleted."""

    name = models.CharField(max_length=120)
    address = models.CharField(max_length=250)
    licence_number = models.CharField(max_length=40, unique=True)
    contact_name = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Every account has one role. Accounts are deactivated, never deleted (CON-6)."""

    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.DONOR)
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    hospital = models.ForeignKey(
        Hospital, null=True, blank=True, on_delete=models.PROTECT, related_name="users"
    )

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
