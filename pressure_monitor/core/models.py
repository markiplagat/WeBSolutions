from django.conf import settings
from django.db import models


class UserRole(models.TextChoices):
    PATIENT = "PATIENT", "Patient"
    CLINICIAN = "CLINICIAN", "Clinician"
    ADMIN = "ADMIN", "Admin"


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=UserRole.choices)

    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class PatientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile"
    )
    nhs_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Patient: {self.user.username}"


class ClinicianProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clinician_profile"
    )
    organization = models.CharField(max_length=160, blank=True)

    def __str__(self):
        return f"Clinician: {self.user.username}"


class PressureReading(models.Model):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="pressure_readings"
    )
    recorded_at = models.DateTimeField()
    pressure_value = models.FloatField()
    contact_area = models.FloatField(default=0)
    peak_pressure = models.FloatField(default=0)
    is_flagged = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient.user.username} - {self.recorded_at}"


class PressureComment(models.Model):
    reading = models.ForeignKey(
        PressureReading,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="pressure_comments"
    )
    comment_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.patient.user.username} on {self.reading.recorded_at}"


class PressureCommentReply(models.Model):
    comment = models.ForeignKey(
        PressureComment,
        on_delete=models.CASCADE,
        related_name="replies"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pressure_comment_replies"
    )
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply by {self.author.username}"


class FlaggedPressureEvent(models.Model):
    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="flagged_events"
    )
    reading = models.ForeignKey(
        PressureReading,
        on_delete=models.CASCADE,
        related_name="flagged_events"
    )
    reason = models.CharField(max_length=255)
    severity = models.CharField(
        max_length=10,
        choices=Severity.choices,
        default=Severity.MEDIUM
    )
    reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.user.username} - {self.severity} - {self.reason}"
        