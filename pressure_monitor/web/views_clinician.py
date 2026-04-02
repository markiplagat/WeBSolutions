from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden

from core.models import ClinicianProfile, Message, PatientProfile, UserRole
from .permissions import require_role, get_clinician_profile, can_view_patient


@require_role(UserRole.CLINICIAN)
def clinician_dashboard(request):
    user = request.user
    clinician_profile = get_clinician_profile(user)
    
    if not clinician_profile:
        return HttpResponseForbidden("Clinician profile not found.")

    patient = clinician_profile.assigned_patients.first()

    if request.method == "POST":
        body = request.POST.get("message", "").strip()
        patient_id = request.POST.get("patient_id")
        
        # Verify patient is assigned to this clinician before creating message
        if patient_id:
            selected_patient = PatientProfile.objects.filter(id=patient_id).first()
            if selected_patient and selected_patient in clinician_profile.assigned_patients.all():
                patient = selected_patient
            else:
                return HttpResponseForbidden(
                    "You are not authorized to contact this patient."
                )
        
        if body and patient:
            Message.objects.create(
                patient_profile=patient,
                clinician_profile=clinician_profile,
                sender_role=UserRole.CLINICIAN,
                body=body,
            )
        return redirect("dashboard_clinician")

    # Handle patient selection from query parameter
    patient_id = request.GET.get("patient")
    if patient_id:
        selected_patient = PatientProfile.objects.filter(id=patient_id).first()
        if selected_patient and selected_patient in clinician_profile.assigned_patients.all():
            patient = selected_patient
        else:
            return HttpResponseForbidden(
                "You are not authorized to view this patient's data."
            )

    assigned_patients = clinician_profile.assigned_patients.all()
    message_thread = []
    if patient:
        message_thread = Message.objects.filter(
            clinician_profile=clinician_profile,
            patient_profile=patient,
        ).order_by("created_at")

    context = {
        "clinician": clinician_profile,
        "assigned_patients": assigned_patients,
        "selected_patient": patient,
        "message_thread": message_thread,
        "metrics": {
            "total_patients": assigned_patients.count(),
            "high_risk": assigned_patients.count() // 2 or 1,
            "active_alerts": 2,
            "improving": 1,
        },
        "flagged_events": [
            {"patient": "John Smith", "time": "3/19/2026, 9:51 AM", "peak": "97 mmHg", "duration": "15 min", "status": "active"},
            {"patient": "Emily Davis", "time": "3/19/2026, 10:21 AM", "peak": "88 mmHg", "duration": "8 min", "status": "active"},
            {"patient": "Michael Brown", "time": "3/19/2026, 8:51 AM", "peak": "76 mmHg", "duration": "12 min", "status": "resolved"},
        ],
        "analysis": {
            "risk": "High",
            "current_peak": 92,
            "average": 68,
            "last_alert": "9:51:28 AM",
        },
    }
    return render(request, "auth/dashboard_clinician.html", context)
