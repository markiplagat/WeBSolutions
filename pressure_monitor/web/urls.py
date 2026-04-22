from django.urls import path
from .views import home, patient_dashboard, clinician_flagged_events

urlpatterns = [
    path("", home, name="home"),
    path("patient/dashboard/", patient_dashboard, name="patient_dashboard"),
    path("clinician/flagged-events/", clinician_flagged_events, name="clinician_flagged_events"),
]