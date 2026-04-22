from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def admin_dashboard(request):
    context = {
        "admin_name": request.user.get_full_name() or request.user.username,
        "stats": {
            "patients": 24,
            "clinicians": 8,
            "devices": 18,
            "active_alerts": 6,
        },
        "recent_alerts": [
            {"patient": "John Smith", "type": "High Pressure", "severity": "Critical", "time": "11:09 AM"},
            {"patient": "Mary Wanjiku", "type": "Sustained Pressure", "severity": "High", "time": "10:42 AM"},
            {"patient": "David Kimani", "type": "Sensor Offline", "severity": "Medium", "time": "10:20 AM"},
        ],
        "recent_users": [
            {"name": "John Smith", "role": "Patient", "status": "Active"},
            {"name": "Dr. Amanda Wilson", "role": "Clinician", "status": "Active"},
            {"name": "Mary Wanjiku", "role": "Patient", "status": "Pending"},
        ],
        "assignments": [
            {"clinician": "Dr. Amanda Wilson", "patient": "John Smith"},
            {"clinician": "Dr. Brian Otieno", "patient": "Mary Wanjiku"},
            {"clinician": "Dr. Amanda Wilson", "patient": "David Kimani"},
        ],
    }
    return render(request, "adminpanel/dashboard.html", context)


