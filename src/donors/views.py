from django.contrib.auth.decorators import login_not_required
from django.db import IntegrityError
from django.shortcuts import redirect, render

from .forms import DonorRegistrationForm

SESSION_KEY = "registered_donor_id"


@login_not_required
def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = DonorRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            donor = form.save()
        except IntegrityError:
            # Another request registered the same mobile number or email a moment earlier.
            form.add_error(None, "These details could not be saved. Check them and try again.")
        else:
            request.session[SESSION_KEY] = donor.donor_id
            return redirect("donors:registered")
    return render(request, "donors/register.html", {"form": form})


@login_not_required
def registered(request):
    """Confirmation page. The identifier travels in the session, not in the URL."""
    donor_id = request.session.pop(SESSION_KEY, None)
    if not donor_id:
        return redirect("accounts:login")
    return render(request, "donors/registered.html", {"donor_id": donor_id})
