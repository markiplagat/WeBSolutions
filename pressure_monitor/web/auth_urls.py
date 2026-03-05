from django.urls import path
from django.contrib.auth import views as auth_views
from .views_auth import signup, demo_login

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", signup, name="signup"),
]
