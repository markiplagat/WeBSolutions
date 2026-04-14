from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.models import (
    ClinicianProfile,
    Message,
    PatientProfile,
    PressureFrame,
    UserRole,
)


def pressure_level(value):
    value = float(value)
    if value <= 20:
        return 0
    if value <= 40:
        return 1
    if value <= 60:
        return 2
    if value <= 80:
        return 3
    return 4


def pressure_status(max_pressure):
    if max_pressure > 100:
        return "Critical"
    if max_pressure > 80:
        return "High"
    if max_pressure > 50:
        return "Elevated"
    return "Normal"
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

    latest_frame = None
    device = patient_profile.devices.first()
    if device:
        latest_frame = device.pressure_frames.order_by("-recorded_at").first()

    if latest_frame and latest_frame.data:
        frame_data = latest_frame.data
        flattened = [float(v) for row in frame_data for v in row]
        max_pressure = int(max(flattened))
        avg_pressure = int(sum(flattened) / len(flattened))
        grid = [[pressure_level(v) for v in row] for row in frame_data]
        status = pressure_status(max_pressure)
        recent_alerts = []
        if max_pressure > 80:
            recent_alerts.append(
                {
                    "title": "High Pressure",
                    "value": f"{max_pressure} mmHg",
                    "time": latest_frame.recorded_at.strftime("%I:%M:%S %p"),
                }
            )
        if max_pressure > 100:
            recent_alerts.append(
                {
                    "title": "Critical Pressure",
                    "value": f"{max_pressure} mmHg",
                    "time": latest_frame.recorded_at.strftime("%I:%M:%S %p"),
                }
            )
        if not recent_alerts:
            recent_alerts = [
                {
                    "title": "Pressure Stable",
                    "value": f"{max_pressure} mmHg",
                    "time": latest_frame.recorded_at.strftime("%I:%M:%S %p"),
                }
            ]
        history_frames = device.pressure_frames.order_by("-recorded_at")[:12]
        trend_points = [
            int(sum(float(v) for row in frame.data for v in row) / (len(frame.data) * len(frame.data[0])))
            for frame in reversed(history_frames)
        ]
    else:
        max_pressure = 98
        avg_pressure = 35
        status = "Critical"
        recent_alerts = [
            {"title": "High Pressure", "value": "98 mmHg", "time": "11:09:30 AM"},
            {"title": "High Pressure", "value": "92 mmHg", "time": "11:09:10 AM"},
        ]
        grid = [
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
        ]
        trend_points = [80, 70, 90, 65, 68, 88, 82, 86, 90, 100, 78, 82]

    context = {
        "alerts_on": True,
        "patient_name": user.get_full_name() or user.username,
        "max_pressure": max_pressure,
        "avg_pressure": avg_pressure,
        "status": status,
        "recent_alerts": recent_alerts,
        "tips": [
            "Shift weight every 15–30 minutes",
            "Use cushions for support",
            "Check skin regularly for redness",
            "Maintain good posture",
            "Stay hydrated and nourished",
        ],
        "grid": grid,
        "trend_points": trend_points,
        "message_thread": message_thread,
        "clinician": clinician,
    }
    return render(request, "auth/dashboard_patient.html", context)


@login_required
@require_http_methods(["GET"])
def get_pressure_data(request):
    user = request.user
    try:
        patient_profile = user.userprofile.patient_profile
    except Exception:
        return JsonResponse({"error": "Patient profile not found"}, status=404)

    device = patient_profile.devices.first()
    if not device:
        return JsonResponse({"frames": [], "error": "No device found"}, status=404)

    offset = request.GET.get("offset", 0)
    try:
        offset = int(offset)
    except (TypeError, ValueError):
        offset = 0
    offset = max(0, offset)

    def split_into_sections(frame_data):
        if (
            isinstance(frame_data, list)
            and len(frame_data) > 32
            and len(frame_data[0]) == 32
            and len(frame_data) % 32 == 0
            and all(isinstance(row, list) and len(row) == 32 for row in frame_data)
        ):
            return [frame_data[i : i + 32] for i in range(0, len(frame_data), 32)]
        return [frame_data]

    selected_section = None
    selected_frame = None
    total_sections = 0

    frames_qs = device.pressure_frames.order_by("-recorded_at").only("id", "data", "recorded_at")
    for frame in frames_qs:
        sections = split_into_sections(frame.data) if frame.data else [frame.data]
        if selected_section is None:
            if offset < total_sections + len(sections):
                selected_frame = frame
                selected_section = sections[offset - total_sections]
        total_sections += len(sections)

    if selected_frame is None or selected_section is None:
        return JsonResponse({"frames": [], "total_frames": 0})

    flattened = [float(v) for row in selected_section for v in row]
    frame_list = [
        {
            "id": selected_frame.id,
            "recorded_at": selected_frame.recorded_at.isoformat(),
            "data": selected_section,
            "max_pressure": int(max(flattened)),
            "avg_pressure": int(sum(flattened) / len(flattened)),
        }
    ]

    return JsonResponse({"frames": frame_list, "total_frames": total_sections})

