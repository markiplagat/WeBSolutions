from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def patient_dashboard(request):
    patient_name = request.user.get_full_name() or request.user.username

    context = {
        "alerts_on": True,
        "patient_name": patient_name,
        "max_pressure": 98,
        "avg_pressure": 35,
        "status": "Critical - Immediate attention required",
        "status_color": "danger",
        "last_updated": "11:10:00 AM",
        "recent_alerts": [
            {
                "title": "High Pressure Detected",
                "value": "98 mmHg",
                "time": "11:09:30 AM",
            },
            {
                "title": "Sustained Pressure Warning",
                "value": "92 mmHg",
                "time": "11:09:10 AM",
            },
        ],
        "tips": [
            "Shift weight every 15–30 minutes",
            "Use cushions for extra support",
            "Check skin regularly for redness",
            "Maintain a healthy sitting posture",
            "Stay hydrated and well nourished",
        ],
        "summary_cards": [
            {"label": "Peak Pressure", "value": "98 mmHg"},
            {"label": "Average Pressure", "value": "35 mmHg"},
            {"label": "Risk Level", "value": "Critical"},
            {"label": "Alerts Today", "value": 2},
        ],
        # 12x12 demo pressure grid (placeholder for future 32x32 live sensor data)
        "grid": [
            [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0],
            [1, 1, 2, 2, 3, 3, 3, 3, 2, 2, 1, 1],
            [1, 2, 2, 3, 3, 4, 4, 3, 3, 2, 2, 1],
            [1, 2, 3, 3, 4, 4, 4, 4, 3, 3, 2, 1],
            [1, 2, 3, 4, 4, 4, 4, 4, 4, 3, 2, 1],
            [1, 2, 3, 4, 4, 4, 4, 4, 4, 3, 2, 1],
            [1, 2, 3, 3, 4, 4, 4, 4, 3, 3, 2, 1],
            [1, 2, 2, 3, 3, 4, 4, 3, 3, 2, 2, 1],
            [1, 1, 2, 2, 3, 3, 3, 3, 2, 2, 1, 1],
            [0, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        ],
        "trend_points": [80, 70, 90, 65, 68, 88, 82, 86, 90, 100, 78, 82],
    }

    return render(request, "patient/dashboard.html", context)