from django.urls import path

from . import views

app_name = "search"

urlpatterns = [
    path("availability/", views.availability_search, name="availability"),
]
