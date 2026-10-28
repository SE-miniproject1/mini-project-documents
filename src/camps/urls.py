from django.urls import path

from . import views

app_name = "camps"

urlpatterns = [
    path("", views.camp_list, name="list"),
    path("manage/", views.manage, name="manage"),
    path("new/", views.new, name="new"),
    path("<str:camp_id>/", views.detail, name="detail"),
    path("<str:camp_id>/close/", views.close, name="close"),
    path("<str:camp_id>/enrol/", views.enrol, name="enrol"),
]
