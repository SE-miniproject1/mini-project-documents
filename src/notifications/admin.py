from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Read only: the record of what was sent, and how, is not edited by hand."""

    list_display = ("created_at", "kind", "donor", "status", "sent_via", "sms_attempts")
    list_filter = ("kind", "status", "sent_via")
    search_fields = ("donor__donor_id",)

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
