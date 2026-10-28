"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("donors/", include("donors.urls")),
    path("collection/", include("collection.urls")),
    path("inventory/", include("inventory.urls")),
    path("", include("core.urls")),
]
