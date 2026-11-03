from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.console, name="console"),
    path("units/<str:unit_id>/", views.unit_detail, name="unit_detail"),
    path("units/<str:unit_id>/separate/", views.separate, name="separate"),
    path("units/<str:unit_id>/label/", views.unit_label, name="label"),
    path("units/<str:unit_id>/barcode.svg", views.unit_barcode, name="barcode"),
]
