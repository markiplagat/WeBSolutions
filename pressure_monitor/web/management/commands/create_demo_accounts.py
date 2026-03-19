from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from core.models import ClinicianProfile, PatientProfile, UserProfile, UserRole


class Command(BaseCommand):
    help = "Create demo patient/clinician/admin accounts with known passwords."

    def handle(self, *args, **options):
        demo_password = "demo123"
        users = [
            {"email": "patient@local.test", "role": UserRole.PATIENT, "name": "Demo Patient"},
            {"email": "clinician@local.test", "role": UserRole.CLINICIAN, "name": "Demo Clinician"},
            {"email": "admin@local.test", "role": UserRole.ADMIN, "name": "Demo Admin"},
        ]

        created = []
        updated = []

        for u in users:
            user, user_created = User.objects.get_or_create(
                username=u["email"],
                defaults={
                    "email": u["email"],
                    "first_name": u["name"].split(" ")[0],
                    "last_name": " ".join(u["name"].split(" ")[1:]),
                },
            )
            if user_created:
                user.set_password(demo_password)
                user.save()
                created.append(user.username)
            else:
                # ensure password is set to known demo password
                user.set_password(demo_password)
                updated.append(user.username)

            if u["role"] == UserRole.ADMIN:
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False
            user.save()

            user_profile, _ = UserProfile.objects.get_or_create(user=user)
            if user_profile.role != u["role"]:
                user_profile.role = u["role"]
                user_profile.save()

            if u["role"] == UserRole.PATIENT:
                PatientProfile.objects.get_or_create(user_profile=user_profile)
            elif u["role"] == UserRole.CLINICIAN:
                ClinicianProfile.objects.get_or_create(user_profile=user_profile)

        # Assign the demo patient to the demo clinician
        clinician = None
        patient = None
        try:
            clinician = User.objects.get(username="clinician@local.test").userprofile.clinician_profile
        except Exception:
            pass
        try:
            patient = User.objects.get(username="patient@local.test").userprofile.patient_profile
        except Exception:
            pass

        if clinician and patient:
            clinician.assigned_patients.add(patient)
            clinician.save()

        self.stdout.write(self.style.SUCCESS("Demo accounts ready."))
        self.stdout.write(self.style.SUCCESS("User/password: patient@local.test/demo123"))
        self.stdout.write(self.style.SUCCESS("User/password: clinician@local.test/demo123"))
        self.stdout.write(self.style.SUCCESS("User/password: admin@local.test/demo123"))
        if created:
            self.stdout.write(self.style.NOTICE(f"Created: {', '.join(created)}"))
        if updated:
            self.stdout.write(self.style.WARNING(f"Updated passwords: {', '.join(updated)}"))
