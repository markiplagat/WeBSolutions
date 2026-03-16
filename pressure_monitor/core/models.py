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
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="patient_profile", null=True, blank=True)
    nhs_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    @property
    def user(self):
        return self.user_profile.user

    def __str__(self):
        return f"Patient: {self.user.username}"


class ClinicianProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name="clinician_profile", null=True, blank=True)
    organization = models.CharField(max_length=160, blank=True)
    assigned_patients = models.ManyToManyField(PatientProfile, related_name="clinicians", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    @property
    def user(self):
        return self.user_profile.user

    def __str__(self):
        return f"Clinician: {self.user.username}"


class Device(models.Model):
    patient_profile = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="devices")
    name = models.CharField(max_length=120, blank=True)
    serial_number = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Device {self.name or self.serial_number} for {self.patient_profile.user.username}"


class PressureReading(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="pressure_readings")
    pressure_value = models.FloatField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pressure_value} mmHg @ {self.recorded_at:%Y-%m-%d %H:%M}"


class Alert(models.Model):
    patient_profile = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="alerts")
    message = models.CharField(max_length=340)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert for {self.patient_profile.user.username}: {self.message[:50]}"


class Message(models.Model):
    patient_profile = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name="messages")
    clinician_profile = models.ForeignKey(ClinicianProfile, on_delete=models.CASCADE, related_name="messages")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message [{self.pk}] {self.patient_profile.user.username} <-> {self.clinician_profile.user.username}"
        