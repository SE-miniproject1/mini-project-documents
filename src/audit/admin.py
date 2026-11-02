from django.contrib import admin

from .models import AuditEntry


@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    """Read only. Nobody edits or deletes the audit log, not even an administrator."""

    list_display = ("occurred_at", "event", "actor_username", "entity_type", "entity_id")
    list_filter = ("event",)

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
