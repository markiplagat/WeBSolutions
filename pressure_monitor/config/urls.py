"""
URL configuration for config project.
"""

from django.contrib import admin
from django.urls import path, include
from web.views_patient import patient_dashboard, get_pressure_data
from web.views_adminpanel import admin_dashboard

urlpatterns = [
    path("admin/", admin.site.urls),

    # main app urls
    path("", include("web.urls")),

    # authentication urls
    path("accounts/", include("web.auth_urls")),
    path("patient/dashboard/", patient_dashboard, name="patient_dashboard"),
    path("api/pressure-data/", get_pressure_data, name="get_pressure_data"),

    # admin dashboard
    path("system-admin/dashboard/", admin_dashboard, name="admin_dashboard"),
]
