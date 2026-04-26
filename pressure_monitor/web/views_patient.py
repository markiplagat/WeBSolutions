from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.models import (
    ClinicianProfile,
    Message,
    PatientProfile,
    PressureFrame,
    UserRole,
)


def pressure_level(value):
    # Map a pressure value (mmHg) to a discrete level (0-4) for color coding.
    # This determines which CSS class (swatch) is used in the heatmap.
    # 0=low (blue), 1=normal (green), 2=moderate (yellow), 3=high (orange), 4=critical (red)
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


def build_trend_points(values, width=560, height=140, minimum=None, maximum=None):
    if not values:
        return ""
    if minimum is None:
        minimum = min(values)
    if maximum is None:
        maximum = max(values)
    if minimum == maximum:
        minimum -= 1
        maximum += 1

    count = len(values)
    points = []
    for idx, value in enumerate(values):
        x = int((width * idx) / max(count - 1, 1))
        normalized = (value - minimum) / (maximum - minimum)
        y = int(height - (normalized * height))
        points.append(f"{x},{y}")
    return " ".join(points)


def format_trend_label(dt):
    return dt.strftime("%-I:%M %p")


def compute_trend_series(frames, minimum=None, maximum=None):
    peak_values = []
    avg_values = []
    contact_area_values = []

    for frame in frames:
        values = [float(v) for row in frame.data for v in row]
        count = len(values)
        peak_values.append(int(max(values)))
        avg_values.append(int(sum(values) / count))
        contact_area_values.append(int(sum(1 for v in values if v > 1) / count * 100))

    peak_points = build_trend_points(peak_values, minimum=minimum, maximum=maximum)
    avg_points = build_trend_points(avg_values, minimum=minimum, maximum=maximum)
    area_points = build_trend_points(contact_area_values, minimum=0, maximum=100)

    return peak_points, avg_points, area_points


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

    # Handle incoming messages from patient to their clinician.
    if request.method == "POST":
        body = request.POST.get("message", "").strip()
        if body and clinician:
            # Create message with sender marked as PATIENT so clinician can identify who sent it.
            Message.objects.create(
                patient_profile=patient_profile,
                clinician_profile=clinician,
                sender_role=UserRole.PATIENT,
                body=body,
            )
        return redirect("dashboard_patient")

    # Retrieve message thread: all messages between this patient and their clinician, ordered chronologically.
    message_thread = []
    if clinician:
        message_thread = Message.objects.filter(
            patient_profile=patient_profile,
            clinician_profile=clinician,
        ).order_by("created_at")  # Chronological order from oldest to newest.

    # Get the latest pressure frame for this patient (if any) and compute display values.
    latest_frame = None
    device = patient_profile.devices.first()
    if device:
        latest_frame = device.pressure_frames.order_by("-recorded_at").first()

    if latest_frame and latest_frame.data:
        frame_data = latest_frame.data
        flattened = [float(v) for row in frame_data for v in row]
        # Compute max and average pressure, as well as the status level for the latest frame.
        max_pressure = int(max(flattened))
        avg_pressure = int(sum(flattened) / len(flattened))
        # Convert the raw pressure matrix into a grid of pressure_level codes (0-4).
        # This grid is passed to the template where each cell renders as a colored div.
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
        latest_time = latest_frame.recorded_at
        ranges = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
        }

        trend_series = {}
        for label, window in ranges.items():
            cutoff = latest_time - window
            frames_in_window = list(
                device.pressure_frames.filter(recorded_at__gte=cutoff).order_by("recorded_at").only("data", "recorded_at")
            )
            if len(frames_in_window) < 2:
                frames_in_window = list(device.pressure_frames.order_by("-recorded_at")[: max(4, len(frames_in_window) or 4)])
                frames_in_window.reverse()

            peak_points, avg_points, area_points = compute_trend_series(
                frames_in_window,
                minimum=0,
                maximum=110,
            )
            trend_series[f"trend_peak_points_{label}"] = peak_points
            trend_series[f"trend_avg_points_{label}"] = avg_points
            trend_series[f"trend_area_points_{label}"] = area_points

        trend_labels = [format_trend_label(frame.recorded_at) for frame in device.pressure_frames.order_by("-recorded_at")[:12]][::-1]
        trend_peak_points = trend_series["trend_peak_points_1h"]
        trend_avg_points = trend_series["trend_avg_points_1h"]
        trend_area_points = trend_series["trend_area_points_1h"]
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
        trend_labels = [f"T{i+1}" for i in range(12)]
        trend_series = {
            "trend_peak_points_1h": build_trend_points([98, 92, 95, 90, 92, 94, 100, 96, 98, 97, 95, 98], minimum=0, maximum=110),
            "trend_avg_points_1h": build_trend_points([60, 56, 58, 55, 57, 59, 62, 61, 60, 58, 57, 59], minimum=0, maximum=110),
            "trend_area_points_1h": build_trend_points([48, 50, 52, 49, 51, 53, 54, 52, 51, 50, 52, 53], minimum=0, maximum=100),
            "trend_peak_points_6h": build_trend_points([92, 90, 96, 91, 94, 98, 100, 97, 95, 93, 94, 96], minimum=0, maximum=110),
            "trend_avg_points_6h": build_trend_points([55, 54, 56, 55, 57, 58, 60, 59, 58, 57, 56, 58], minimum=0, maximum=110),
            "trend_area_points_6h": build_trend_points([50, 48, 51, 52, 50, 49, 51, 52, 52, 50, 51, 53], minimum=0, maximum=100),
            "trend_peak_points_24h": build_trend_points([90, 92, 96, 95, 93, 97, 99, 98, 100, 96, 94, 95], minimum=0, maximum=110),
            "trend_avg_points_24h": build_trend_points([54, 56, 57, 56, 55, 57, 59, 58, 60, 59, 57, 58], minimum=0, maximum=110),
            "trend_area_points_24h": build_trend_points([49, 50, 52, 51, 50, 52, 53, 52, 54, 53, 52, 51], minimum=0, maximum=100),
        }
        trend_peak_points = trend_series["trend_peak_points_1h"]
        trend_avg_points = trend_series["trend_avg_points_1h"]
        trend_area_points = trend_series["trend_area_points_1h"]

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
        "trend_labels": trend_labels,
        "trend_peak_points": trend_peak_points,
        "trend_avg_points": trend_avg_points,
        "trend_area_points": trend_area_points,
        "trend_peak_points_1h": trend_series["trend_peak_points_1h"],
        "trend_avg_points_1h": trend_series["trend_avg_points_1h"],
        "trend_area_points_1h": trend_series["trend_area_points_1h"],
        "trend_peak_points_6h": trend_series["trend_peak_points_6h"],
        "trend_avg_points_6h": trend_series["trend_avg_points_6h"],
        "trend_area_points_6h": trend_series["trend_area_points_6h"],
        "trend_peak_points_24h": trend_series["trend_peak_points_24h"],
        "trend_avg_points_24h": trend_series["trend_avg_points_24h"],
        "trend_area_points_24h": trend_series["trend_area_points_24h"],
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

    return render(request, "patient/dashboard.html", context)