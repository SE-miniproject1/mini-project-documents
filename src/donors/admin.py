from django.contrib import admin

from .models import DeferralCondition, Donor, DonorDeclaration


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("donor_id", "full_name", "blood_group", "eligibility_status", "is_active")
    list_filter = ("blood_group", "eligibility_status", "is_active")
    search_fields = ("donor_id", "full_name", "mobile_number", "email")
    readonly_fields = ("donor_id", "consent_timestamp")


@admin.register(DeferralCondition)
class DeferralConditionAdmin(admin.ModelAdmin):
    """The list of declarable conditions. Retire a condition rather than deleting it."""

    list_display = ("name", "kind", "deferral_days", "is_active", "sort_order")
    list_filter = ("kind", "is_active")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DonorDeclaration)
class DonorDeclarationAdmin(admin.ModelAdmin):
    list_display = ("donor", "condition", "declared_at", "recorded_by")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
