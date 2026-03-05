from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def patient_dashboard(request):
    # Step 1: static demo data
    context = {
        "alerts_on": True,
        "patient_name": request.user.get_full_name() or request.user.username,
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
        # 12x12 demo grid (we’ll upgrade to 32x32 later)
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
    }
    return render(request, "patient/dashboard.html", context)
