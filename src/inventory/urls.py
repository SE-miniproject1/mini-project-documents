from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("units/<str:unit_id>/label/", views.unit_label, name="label"),
    path("units/<str:unit_id>/barcode.svg", views.unit_barcode, name="barcode"),
]
