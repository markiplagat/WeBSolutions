from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden

from core.models import (ClinicianProfile, Message, PatientProfile, UserRole)
from .permissions import require_role, get_patient_profile


@require_role(UserRole.PATIENT)
def patient_dashboard(request):
    user = request.user
    # get patient profile
    patient_profile = get_patient_profile(user)
    
    if not patient_profile:
        return HttpResponseForbidden("Patient profile not found.")

    # assigned clinician fallback
    clinician = (
        ClinicianProfile.objects.filter(assigned_patients=patient_profile).first()
        or ClinicianProfile.objects.first()
    )

    if request.method == "POST":
        body = request.POST.get("message", "").strip()
        if body and clinician:
            Message.objects.create(
                patient_profile=patient_profile,
                clinician_profile=clinician,
                sender_role=UserRole.PATIENT,
                body=body,
            )
        return redirect("dashboard_patient")

    message_thread = []
    if clinician:
        message_thread = Message.objects.filter(
            patient_profile=patient_profile,
            clinician_profile=clinician,
        ).order_by("created_at")

    context = {
        "alerts_on": True,
        "patient_name": user.get_full_name() or user.username,
        "max_pressure": 98,
        "avg_pressure": 35,
        "status": "Critical",
        "recent_alerts": [
            {"title": "High Pressure", "value": "98 mmHg", "time": "11:09:30 AM"},
            {"title": "High Pressure", "value": "92 mmHg", "time": "11:09:10 AM"},
        ],
        "tips": [
            "Shift weight every 15–30 minutes",
            "Use cushions for support",
            "Check skin regularly for redness",
            "Maintain good posture",
            "Stay hydrated and nourished",
        ],
        "grid": [
            [0,0,1,1,1,1,1,1,1,1,0,0],
            [0,1,1,2,2,2,2,2,2,1,1,0],
            [1,1,2,2,3,3,3,3,2,2,1,1],
            [1,2,2,3,3,4,4,3,3,2,2,1],
            [1,2,3,3,4,4,4,4,3,3,2,1],
            [1,2,3,4,4,4,4,4,4,3,2,1],
            [1,2,3,4,4,4,4,4,4,3,2,1],
            [1,2,3,3,4,4,4,4,3,3,2,1],
            [1,2,2,3,3,4,4,3,3,2,2,1],
            [1,1,2,2,3,3,3,3,2,2,1,1],
            [0,1,1,2,2,2,2,2,2,1,1,0],
            [0,0,1,1,1,1,1,1,1,1,0,0],
        ],
        "trend_points": [80, 70, 90, 65, 68, 88, 82, 86, 90, 100, 78, 82],
        "message_thread": message_thread,
        "clinician": clinician,
    }
    return render(request, "auth/dashboard_patient.html", context)

