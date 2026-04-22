from django.contrib import admin
from .models import (
    UserProfile,
    PatientProfile,
    ClinicianProfile,
    PressureReading,
    PressureComment,
    PressureCommentReply,
    FlaggedPressureEvent,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone", "created_at")


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "nhs_number")


@admin.register(ClinicianProfile)
class ClinicianProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "organization")


@admin.register(PressureReading)
class PressureReadingAdmin(admin.ModelAdmin):
    list_display = ("patient", "recorded_at", "pressure_value", "is_flagged")
    list_filter = ("is_flagged",)


@admin.register(PressureComment)
class PressureCommentAdmin(admin.ModelAdmin):
    list_display = ("patient", "reading", "created_at")


@admin.register(PressureCommentReply)
class PressureCommentReplyAdmin(admin.ModelAdmin):
    list_display = ("author", "comment", "created_at")


@admin.register(FlaggedPressureEvent)
class FlaggedPressureEventAdmin(admin.ModelAdmin):
    list_display = ("patient", "severity", "reason", "reviewed", "created_at")
    list_filter = ("severity", "reviewed")