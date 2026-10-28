"""URL configuration used only by the layout, navigation and form tests."""

from django import forms
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import include, path


class SampleForm(forms.Form):
    full_name = forms.CharField(label="Full name")
    mobile = forms.CharField(label="Mobile number", help_text="Ten digits.")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("mobile") == "0000000000":
            raise forms.ValidationError("That number is reserved.")
        return cleaned


def sample_form(request):
    form = SampleForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        return HttpResponse("saved")
    return render(request, "core/tests/form_page.html", {"form": form, "cancel_url": "/"})


def broken(request):
    raise ValueError("SELECT secret FROM internal_table")


def page(request):
    return render(request, "core/home.html")


def stub(name):
    def view(request):
        return render(request, "core/home.html")

    return view


urlpatterns = [
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("form/", sample_form, name="sample_form"),
    path("broken/", broken),
    path("page/", page, name="page"),
    path("donors/", include(([path("me/", stub("me"), name="dashboard")], "donors"))),
    path("inventory/", include(([path("", stub("inv"), name="console")], "inventory"))),
    path("requests/", include(([path("new/", stub("new"), name="new")], "requests"))),
]

handler404 = "django.views.defaults.page_not_found"
