from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .forms import SignupForm

def signup(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = SignupForm()

    return render(request, "auth/signup.html", {"form": form})


@require_POST
def demo_login(request, role: str):
    """
    Quick login for demo accounts (only if DEBUG=True).
    role: patient | clinician | admin
    """
    if not settings.DEBUG:
        return redirect("login")

    role = role.lower()
    email_map = {
        "patient": "patient@demo.com",
        "clinician": "clinician@demo.com",
        "admin": "admin@demo.com",
    }
    email = email_map.get(role)
    if not email:
        return redirect("login")

    try:
        user = User.objects.get(username=email)
    except User.DoesNotExist:
        messages.error(request, "Demo user not found. Create demo users first.")
        return redirect("login")

    login(request, user)
    return redirect("home")
    