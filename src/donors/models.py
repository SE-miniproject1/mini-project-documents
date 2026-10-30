"""Donor record (SRS REQ-1 to REQ-8, Appendix B.1)."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

TEN_DIGITS = RegexValidator(r"^\d{10}$", "Enter a 10-digit number.")
SIX_DIGITS = RegexValidator(r"^\d{6}$", "Enter a 6-digit PIN code.")


class Gender(models.TextChoices):
    MALE = "Male", "Male"
    FEMALE = "Female", "Female"
    OTHER = "Other", "Other"


class BloodGroup(models.TextChoices):
    A_POS = "A+", "A+"
    A_NEG = "A-", "A-"
    B_POS = "B+", "B+"
    B_NEG = "B-", "B-"
    AB_POS = "AB+", "AB+"
    AB_NEG = "AB-", "AB-"
    O_POS = "O+", "O+"
    O_NEG = "O-", "O-"


class Eligibility(models.TextChoices):
    ELIGIBLE = "Eligible", "Eligible"
    TEMPORARY = "Temporarily Deferred", "Temporarily Deferred"
    PERMANENT = "Permanently Deferred", "Permanently Deferred"


class Donor(models.Model):
    donor_id = models.CharField(max_length=11, unique=True, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="donor_profile",
    )
    full_name = models.CharField(max_length=60)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    blood_group = models.CharField(max_length=3, choices=BloodGroup.choices)
    mobile_number = models.CharField(max_length=10, validators=[TEN_DIGITS])
    email = models.EmailField(max_length=100)
    address_line = models.CharField(max_length=120)
    city = models.CharField(max_length=40)
    pin_code = models.CharField(max_length=6, validators=[SIX_DIGITS])
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        validators=[MinValueValidator(1), MaxValueValidator(300)],
    )
    haemoglobin = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    last_donation_date = models.DateField(null=True, blank=True)
    next_eligible_date = models.DateField(null=True, blank=True)
    eligibility_status = models.CharField(
        max_length=20, choices=Eligibility.choices, default=Eligibility.ELIGIBLE
    )
    deferral_reason = models.CharField(max_length=100, blank=True)
    deferral_review_date = models.DateField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=60)
    emergency_contact_number = models.CharField(max_length=10, validators=[TEN_DIGITS])
    consent_timestamp = models.DateTimeField()
    registration_date = models.DateField(auto_now_add=True)
    # Donors are deactivated, never deleted (SRS CON-6, BR-10).
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["donor_id"]
        constraints = [
            # SRS REQ-3: unique across active donors.
            models.UniqueConstraint(
                fields=["mobile_number"],
                condition=Q(is_active=True),
                name="donor_active_mobile_unique",
            ),
            models.UniqueConstraint(
                fields=["email"], condition=Q(is_active=True), name="donor_active_email_unique"
            ),
        ]

    def __str__(self):
        return f"{self.donor_id} {self.full_name}"

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._loaded_donor_id = instance.__dict__.get("donor_id")
        return instance

    def save(self, *args, **kwargs):
        # The identifier never changes once assigned (SRS REQ-2).
        loaded = getattr(self, "_loaded_donor_id", None)
        if loaded is not None and self.donor_id != loaded:
            raise ValueError("A donor identifier cannot be changed.")
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)
        self._loaded_donor_id = self.donor_id
