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
    path("<str:request_id>/allocate/", views.allocate, name="allocate"),
    path("<str:request_id>/issue/", views.issue, name="issue"),
    path("<str:request_id>/release/<int:allocation_id>/", views.release, name="release"),
    path("<str:request_id>/cancel/", views.cancel, name="cancel"),
]
