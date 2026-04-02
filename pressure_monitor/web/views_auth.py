from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from core.models import UserRole
from .forms import SignupForm
from .permissions import require_role


def _dashboard_for_user(user):
    role = None
    try:
        role = user.userprofile.role
    except Exception:
        return "home"
    if role == UserRole.PATIENT:
        return "dashboard_patient"
    if role == UserRole.CLINICIAN:
        return "dashboard_clinician"
    if role == UserRole.ADMIN:
        return "dashboard_admin"
    return "home"


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = SignupForm()

    return render(request, "auth/signup.html", {"form": form})


@login_required
def dashboard(request):
    target = _dashboard_for_user(request.user)
    return redirect(target)


@require_role(UserRole.PATIENT)
def dashboard_patient(request):
    return render(request, "auth/dashboard_patient.html")


@require_role(UserRole.CLINICIAN)
def dashboard_clinician(request):
    return render(request, "auth/dashboard_clinician.html")


@require_role(UserRole.ADMIN)
def dashboard_admin(request):
    return render(request, "auth/dashboard_admin.html")


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
    return redirect("dashboard")

