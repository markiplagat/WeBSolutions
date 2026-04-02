"""
Authorization and permissions module for role-based access control.
Provides decorators and permission checking functions for the pressure monitor app.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from core.models import UserRole, PatientProfile, ClinicianProfile


def require_role(*allowed_roles):
    """
    Decorator to restrict access to views based on user role.
    
    Usage:
        @require_role(UserRole.PATIENT)
        def my_view(request):
            ...
        
        @require_role(UserRole.CLINICIAN, UserRole.ADMIN)
        def admin_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            try:
                user_role = request.user.userprofile.role
            except Exception:
                return HttpResponseForbidden("No user profile found.")
            
            if user_role not in allowed_roles:
                return HttpResponseForbidden(
                    f"Access denied. Required role(s): {', '.join(allowed_roles)}. "
                    f"Your role: {user_role}"
                )
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def get_user_role(user):
    """Get the role of a user, or None if no profile exists."""
    try:
        return user.userprofile.role
    except Exception:
        return None


def get_patient_profile(user):
    """Get the patient profile for a user, or None if not a patient."""
    try:
        return user.userprofile.patient_profile
    except Exception:
        return None


def get_clinician_profile(user):
    """Get the clinician profile for a user, or None if not a clinician."""
    try:
        return user.userprofile.clinician_profile
    except Exception:
        return None


def is_patient(user):
    """Check if user is a patient."""
    return get_user_role(user) == UserRole.PATIENT


def is_clinician(user):
    """Check if user is a clinician."""
    return get_user_role(user) == UserRole.CLINICIAN


def is_admin(user):
    """Check if user is an admin."""
    return get_user_role(user) == UserRole.ADMIN


def can_view_patient(clinician_user, patient_profile):
    """
    Check if a clinician has permission to view a patient's data.
    Returns True if the clinician is assigned to the patient.
    """
    if not is_clinician(clinician_user):
        return False
    
    try:
        clinician_profile = get_clinician_profile(clinician_user)
        if clinician_profile and patient_profile in clinician_profile.assigned_patients.all():
            return True
    except Exception:
        pass
    
    return False


def can_edit_patient(clinician_user, patient_profile):
    """
    Check if a clinician can edit a patient's data.
    Currently same as view permissions, but extensible for future use.
    """
    return can_view_patient(clinician_user, patient_profile)


def require_patient_permission(view_func):
    """
    Decorator for views that operate on a patient (identified by patient_id in request).
    Ensures the logged-in user is either:
    - The patient themselves, OR
    - A clinician assigned to that patient
    
    Usage:
        @require_patient_permission
        def view_patient_data(request):
            patient_id = request.GET.get('patient_id')
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        patient_id = request.GET.get('patient_id') or request.POST.get('patient_id')
        
        if not patient_id:
            return view_func(request, *args, **kwargs)
        
        try:
            patient_profile = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return HttpResponseForbidden("Patient not found.")
        
        user_role = get_user_role(request.user)
        
        # Patient can view their own data
        if user_role == UserRole.PATIENT:
            user_patient = get_patient_profile(request.user)
            if user_patient and user_patient.id == patient_profile.id:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("You can only view your own data.")
        
        # Clinician can view assigned patients
        if user_role == UserRole.CLINICIAN:
            if can_view_patient(request.user, patient_profile):
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden(
                    "You are not assigned to this patient."
                )
        
        # Admin can view any patient
        if user_role == UserRole.ADMIN:
            return view_func(request, *args, **kwargs)
        
        return HttpResponseForbidden("Insufficient permissions.")
    
    return wrapper
