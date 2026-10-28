from django.urls import path

from . import views

app_name = "requests"

urlpatterns = [
    path("new/", views.new_request, name="new"),
    path("queue/", views.staff_queue, name="queue"),
    path("mine/", views.tracker, name="tracker"),
    path("<str:request_id>/", views.detail, name="detail"),
    path("<str:request_id>/approve/", views.approve, name="approve"),
    path("<str:request_id>/reject/", views.reject, name="reject"),
]
