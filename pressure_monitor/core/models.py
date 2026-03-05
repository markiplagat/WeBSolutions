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
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patient_profile")
    nhs_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Patient: {self.user.username}"


class ClinicianProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clinician_profile")
    organization = models.CharField(max_length=160, blank=True)

    def __str__(self):
        return f"Clinician: {self.user.username}"
        