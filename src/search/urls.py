"""URLs for hospital availability search."""

from django.urls import path

from search import views

app_name = "search"

urlpatterns = [
    path("availability/", views.availability, name="availability"),
]
