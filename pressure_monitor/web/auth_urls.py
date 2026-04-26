from django.urls import path
from django.contrib.auth import views as auth_views
from .views_auth import (
    signup,
    dashboard,
    dashboard_admin,
    demo_login,
)
from .views_patient import patient_dashboard
from .views_clinician import clinician_dashboard, clinician_report

# Auth URL patterns for login, signup, and role-based dashboards.
urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="auth/login.html",
            redirect_authenticated_user=True
        ),
        name="login"
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("signup/", signup, name="signup"),

    # Role-based dashboard redirect entrypoint and specific role pages.
    path("dashboard/", dashboard, name="dashboard"),
    path("dashboard/patient/", patient_dashboard, name="dashboard_patient"),
    path("dashboard/clinician/", clinician_dashboard, name="dashboard_clinician"),
    path("dashboard/clinician/report/", clinician_report, name="clinician_report"),
    path("dashboard/admin/", dashboard_admin, name="dashboard_admin"),

    # Demo login helper for development only.
    path("demo-login/<str:role>/", demo_login, name="demo_login"),
]