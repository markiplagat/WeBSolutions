from django.urls import path
from django.contrib.auth import views as auth_views
from .views_auth import (
    signup,
    dashboard,
    dashboard_patient,
    dashboard_clinician,
    dashboard_admin,
    demo_login,
)

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", signup, name="signup"),
    path("dashboard/", dashboard, name="dashboard"),
    path("dashboard/patient/", dashboard_patient, name="dashboard_patient"),
    path("dashboard/clinician/", dashboard_clinician, name="dashboard_clinician"),
    path("dashboard/admin/", dashboard_admin, name="dashboard_admin"),
    path("demo-login/<str:role>/", demo_login, name="demo_login"),
]
