from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from django.utils import timezone


from core.models import ClinicianProfile, Message, PatientProfile, PressureFrame, UserRole
from .permissions import require_role, get_clinician_profile, can_view_patient




def pressure_status(max_pressure):
   if max_pressure > 100:
       return "Critical"
   if max_pressure > 80:
       return "High"
   if max_pressure > 50:
       return "Elevated"
   return "Normal"




def compute_patient_pressure_summary(patient_profile):
   device = patient_profile.devices.first()
   if not device:
       return {
           "patient_name": patient_profile.user.get_full_name() or patient_profile.user.username,
           "latest_recorded_at": None,
           "current_peak": 0,
           "average": 0,
           "contact_area": 0,
           "frame_count": 0,
           "high_risk_frames": 0,
           "critical_frames": 0,
           "average_peak": 0,
           "risk": "Unknown",
           "generated_at": timezone.localtime(),
       }


   frames = list(device.pressure_frames.order_by("-recorded_at").only("data", "recorded_at"))
   if not frames:
       return {
           "patient_name": patient_profile.user.get_full_name() or patient_profile.user.username,
           "latest_recorded_at": None,
           "current_peak": 0,
           "average": 0,
           "contact_area": 0,
           "frame_count": 0,
           "high_risk_frames": 0,
           "critical_frames": 0,
           "average_peak": 0,
           "risk": "Unknown",
           "generated_at": timezone.localtime(),
       }


   def flatten_frame(frame_data):
       return [float(v) for row in frame_data for v in row]


   latest_values = flatten_frame(frames[0].data)
   latest_peak = int(max(latest_values))
   latest_avg = int(sum(latest_values) / len(latest_values))
   latest_contact_area = int(sum(1 for v in latest_values if v > 1) / len(latest_values) * 100)


   peaks = []
   for frame in frames:
       values = flatten_frame(frame.data)
       peaks.append(max(values))


   average_peak = int(sum(peaks) / len(peaks))
   high_risk_frames = sum(1 for peak in peaks if peak > 80)
   critical_frames = sum(1 for peak in peaks if peak > 100)


   return {
       "patient_name": patient_profile.user.get_full_name() or patient_profile.user.username,
       "latest_recorded_at": frames[0].recorded_at,
       "current_peak": latest_peak,
       "average": latest_avg,
       "contact_area": latest_contact_area,
       "frame_count": len(frames),
       "high_risk_frames": high_risk_frames,
       "critical_frames": critical_frames,
       "average_peak": average_peak,
       "risk": pressure_status(latest_peak),
       "generated_at": timezone.localtime(),
   }




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
       "analysis": compute_patient_pressure_summary(patient),
   }
   return render(request, "auth/dashboard_clinician.html", context)




@require_role(UserRole.CLINICIAN)
def clinician_report(request):
   user = request.user
   clinician_profile = get_clinician_profile(user)


   if not clinician_profile:
       return HttpResponseForbidden("Clinician profile not found.")


   assigned_patients = clinician_profile.assigned_patients.all()
   patient_id = request.GET.get("patient_id")
   selected_patient = None


   if patient_id:
       selected_patient = PatientProfile.objects.filter(id=patient_id).first()
       if not selected_patient or selected_patient not in assigned_patients:
           return HttpResponseForbidden(
               "You are not authorized to generate a report for this patient."
           )


   if not selected_patient:
       selected_patient = assigned_patients.first()


   if not selected_patient:
       return HttpResponseForbidden("No assigned patients available.")


   report = compute_patient_pressure_summary(selected_patient)


   context = {
       "clinician": clinician_profile,
       "assigned_patients": assigned_patients,
       "selected_patient": selected_patient,
       "report": report,
   }
   return render(request, "auth/clinician_report.html", context)


