
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
import csv
import io




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




def build_report_csv(report):
  output = io.StringIO()
  writer = csv.writer(output)


  writer.writerow(["Patient Pressure Report"])
  writer.writerow([])
  writer.writerow(["Patient", report["patient_name"]])
  writer.writerow(["Generated", report["generated_at"].strftime("%m/%d/%Y %I:%M %p")])
  writer.writerow([])
  writer.writerow(["Metric", "Value"])
  writer.writerow(["Risk Level", report["risk"]])
  writer.writerow(["Latest Peak", f"{report['current_peak']} mmHg"])
  writer.writerow(["Latest Average", f"{report['average']} mmHg"])
  writer.writerow(["Contact Area", f"{report['contact_area']}%"])
  writer.writerow(["Frames Recorded", report["frame_count"]])
  writer.writerow(["High Risk Frames", report["high_risk_frames"]])
  writer.writerow(["Critical Frames", report["critical_frames"]])
  writer.writerow(["Average Peak", f"{report['average_peak']} mmHg"])
  if report["latest_recorded_at"]:
      writer.writerow(["Latest Measurement", report["latest_recorded_at"].strftime("%m/%d/%Y %I:%M %p")])


  return output.getvalue()




def escape_pdf_text(text):
  return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")




def build_report_pdf(report):
  lines = [
      f"Patient Pressure Report",
      f"Patient: {report['patient_name']}",
      f"Generated: {report['generated_at'].strftime('%m/%d/%Y %I:%M %p')}",
      "",
      f"Risk Level: {report['risk']}",
      f"Latest Peak: {report['current_peak']} mmHg",
      f"Latest Average: {report['average']} mmHg",
      f"Contact Area: {report['contact_area']}%",
      f"Frames Recorded: {report['frame_count']}",
      f"High Risk Frames: {report['high_risk_frames']}",
      f"Critical Frames: {report['critical_frames']}",
      f"Average Peak: {report['average_peak']} mmHg",
  ]


  content_lines = [b"BT /F1 12 Tf 50 760 Td\n"]
  for idx, line in enumerate(lines):
      content_lines.append(b"(" + escape_pdf_text(line).encode("latin1") + b") Tj\n")
      if idx < len(lines) - 1:
          content_lines.append(b"0 -18 Td\n")
  content_lines.append(b"ET\n")
  content_stream = b"".join(content_lines)


  objs = [
      (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
      (2, b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
      (3, b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"),
      (4, b"<< /Length %d >>\nstream\n" % len(content_stream) + content_stream + b"endstream"),
      (5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
  ]


  output = bytearray(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")
  offsets = []
  for obj_num, data in objs:
      offsets.append(len(output))
      output.extend(f"{obj_num} 0 obj\n".encode("latin1"))
      output.extend(data)
      output.extend(b"\nendobj\n")


  xref_start = len(output)
  output.extend(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode("latin1"))
  for offset in offsets:
      output.extend(f"{offset:010d} 00000 n \n".encode("latin1"))
  output.extend(f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("latin1"))


  return bytes(output)




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
    
      # Handle incoming messages from clinician to a patient.
      if body and patient:
          # Create message with sender marked as CLINICIAN so patient can identify who sent it.
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
  # Retrieve message thread: all messages between clinician and selected patient, ordered chronologically.
  message_thread = []
  if patient:
      message_thread = Message.objects.filter(
          clinician_profile=clinician_profile,
          patient_profile=patient,
      ).order_by("created_at")  # Chronological order from oldest to newest.




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
  format_type = request.GET.get("format", "view").lower()


  if format_type == "csv":
      csv_content = build_report_csv(report)
      filename = f"pressure-report-{selected_patient.id}.csv"
      return HttpResponse(
          csv_content,
          content_type="text/csv",
          headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
      )


  if format_type == "pdf":
      pdf_content = build_report_pdf(report)
      filename = f"pressure-report-{selected_patient.id}.pdf"
      return HttpResponse(
          pdf_content,
          content_type="application/pdf",
          headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
      )


  context = {
      "clinician": clinician_profile,
      "assigned_patients": assigned_patients,
      "selected_patient": selected_patient,
      "report": report,
  }
  return render(request, "auth/clinician_report.html", context)


