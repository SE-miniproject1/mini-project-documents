from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Hospital, SystemConfiguration, User


@admin.register(User)
class ApplicationUserAdmin(UserAdmin):
    """Manage application users and their assigned roles."""

    fieldsets = UserAdmin.fieldsets + (
        ("Application role", {"fields": ("role",)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Application role", {"fields": ("role",)}),
    )

    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email")


@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    """Manage hospital registrations."""

    list_display = ("name", "registration_number", "phone", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "registration_number", "email")
    list_editable = ("is_active",)


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Manage blood bank thresholds without changing application code."""

    list_display = (
        "donation_interval_days",
        "minimum_age",
        "maximum_age",
        "minimum_weight_kg",
        "minimum_haemoglobin",
        "updated_at",
    )
    readonly_fields = ("updated_at",)
