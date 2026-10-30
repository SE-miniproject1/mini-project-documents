from django.contrib import admin

from .models import Donor


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("donor_id", "full_name", "blood_group", "eligibility_status", "is_active")
    list_filter = ("blood_group", "eligibility_status", "is_active")
    search_fields = ("donor_id", "full_name", "mobile_number", "email")
    readonly_fields = ("donor_id", "consent_timestamp")
