from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


class User(AbstractUser):
    """Application user with exactly one assigned role."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        HOSPITAL = "HOSPITAL", "Hospital"
        STAFF = "STAFF", "Staff"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STAFF,
    )


class Hospital(models.Model):
    """Hospital registered in the blood bank system."""

    name = models.CharField(max_length=150, unique=True)
    registration_number = models.CharField(max_length=50, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class SystemConfiguration(models.Model):
    """Editable operational thresholds for the blood bank."""

    donation_interval_days = models.PositiveIntegerField(
        default=90,
        validators=[MinValueValidator(1)],
    )
    minimum_age = models.PositiveIntegerField(
        default=18,
        validators=[MinValueValidator(1)],
    )
    maximum_age = models.PositiveIntegerField(
        default=65,
        validators=[MinValueValidator(1)],
    )
    minimum_weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50,
        validators=[MinValueValidator(0.01)],
    )
    minimum_haemoglobin = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=12.5,
        validators=[MinValueValidator(0.1)],
    )
    whole_blood_shelf_life_days = models.PositiveIntegerField(
        default=35,
        validators=[MinValueValidator(1)],
    )
    platelet_shelf_life_days = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1)],
    )
    plasma_shelf_life_days = models.PositiveIntegerField(
        default=365,
        validators=[MinValueValidator(1)],
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Blood bank configuration"

    class Meta:
        verbose_name = "System configuration"
        verbose_name_plural = "System configuration"
