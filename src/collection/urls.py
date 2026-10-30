from django.urls import path

from . import views

app_name = "collection"

urlpatterns = [
    path("<str:donor_id>/new/", views.new_collection, name="new"),
    path("units/<str:unit_id>/recorded/", views.confirmation, name="confirmation"),
    path("units/<str:unit_id>/results/", views.results, name="results"),
]
