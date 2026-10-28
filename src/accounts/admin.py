from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class BBMSUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_active", "locked_until")
    list_filter = ("role", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Blood bank", {"fields": ("role", "failed_login_count", "locked_until")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (("Blood bank", {"fields": ("email", "role")}),)
