"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path, include
from web.views_adminpanel import admin_dashboard

urlpatterns = [
    path("admin/", admin.site.urls),

    # main app urls
    path("", include("web.urls")),

    # authentication urls
    path("accounts/", include("web.auth_urls")),

    # admin dashboard
    path("system-admin/dashboard/", admin_dashboard, name="admin_dashboard"),
]
