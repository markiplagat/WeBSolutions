from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from core.models import PatientProfile, PressureReading, FlaggedPressureEvent
from .forms import PressureCommentForm


# Home page
def home(request):
    return render(request, "web/home.html")


# Patient dashboard
@login_required
def patient_dashboard(request):
    patient_profile = PatientProfile.objects.filter(user=request.user).first()

    if not patient_profile:
        return render(request, "web/no_patient_profile.html")

    readings = PressureReading.objects.filter(patient=patient_profile).order_by("-recorded_at")

    if request.method == "POST":
        reading_id = request.POST.get("reading_id")
        reading = get_object_or_404(PressureReading, id=reading_id, patient=patient_profile)

        form = PressureCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.reading = reading
            comment.patient = patient_profile
            comment.save()
            return redirect("patient_dashboard")
    else:
        form = PressureCommentForm()

    return render(request, "web/patient_dashboard.html", {
        "readings": readings,
        "form": form,
    })


# Clinician flagged events
@login_required
def clinician_flagged_events(request):
    if request.method == "POST":
        event_id = request.POST.get("event_id")
        event = get_object_or_404(FlaggedPressureEvent, id=event_id)
        event.reviewed = True
        event.save()
        return redirect("clinician_flagged_events")

    events = FlaggedPressureEvent.objects.select_related(
        "patient__user", "reading"
    ).order_by("-created_at")

    return render(request, "web/clinician_flagged_events.html", {
        "events": events
    })