from django.contrib import admin

from .models import BloodUnit


@admin.register(BloodUnit)
class BloodUnitAdmin(admin.ModelAdmin):
    """Read only. Units are created by collection and change status through the state machine."""

    list_display = ("unit_id", "component_type", "blood_group", "status", "expiry_date")
    list_filter = ("status", "component_type", "blood_group")
    search_fields = ("unit_id",)

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False  # units are never deleted (SRS CON-6, BR-10)
