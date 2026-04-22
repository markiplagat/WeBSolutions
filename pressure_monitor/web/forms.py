from django import forms
from django.contrib.auth.models import User
from core.models import UserProfile, UserRole, PatientProfile, ClinicianProfile, PressureComment


class SignupForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    role = forms.ChoiceField(choices=UserRole.choices)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        user = User(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            first_name=self.cleaned_data.get("first_name", ""),
            last_name=self.cleaned_data.get("last_name", ""),
        )
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

            role = self.cleaned_data["role"]

            user_profile = UserProfile.objects.create(user=user, role=role)

            if role == UserRole.PATIENT:
                PatientProfile.objects.create(user_profile=user_profile)

            elif role == UserRole.CLINICIAN:
                ClinicianProfile.objects.create(user_profile=user_profile)

        return user


class PressureCommentForm(forms.ModelForm):
    class Meta:
        model = PressureComment
        fields = ["comment_text"]
        widgets = {
            "comment_text": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Add your comment about this pressure reading..."
            })
        }
