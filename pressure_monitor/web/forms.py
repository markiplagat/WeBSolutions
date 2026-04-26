# Custom signup form for the registration workflow.
# This form captures the user's full name, email, password, and account type.
# The selected account type determines whether a PatientProfile or ClinicianProfile is created.
from django import forms
from django.contrib.auth.models import User
from core.models import UserProfile, UserRole, PatientProfile, ClinicianProfile

class SignupForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    account_type = forms.ChoiceField(choices=UserRole.choices)

    def clean_email(self):
        # Normalize and validate email uniqueness before creating the account.
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self):
        # Create the User and the associated profile objects.
        full_name = self.cleaned_data["full_name"].strip()
        email = self.cleaned_data["email"].strip().lower()
        password = self.cleaned_data["password"]
        role = self.cleaned_data["account_type"]

        first_name = full_name.split(" ")[0]
        last_name = " ".join(full_name.split(" ")[1:]) if len(full_name.split(" ")) > 1 else ""

        user = User.objects.create_user(
            username=email,     # use email as the login identifier
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        user_profile = UserProfile.objects.create(user=user, role=role)

        if role == UserRole.PATIENT:
            PatientProfile.objects.create(user_profile=user_profile)
        elif role == UserRole.CLINICIAN:
            ClinicianProfile.objects.create(user_profile=user_profile)

        return user
