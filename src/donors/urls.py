from django.urls import path

from . import views

app_name = "donors"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("registered/", views.registered, name="registered"),
    path("search/", views.search, name="search"),
    path("screenings/<int:pk>/", views.screening_result, name="screening_result"),
    path("<str:donor_id>/screen/", views.screen, name="screen"),
]
