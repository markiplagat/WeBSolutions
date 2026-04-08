#!/usr/bin/env python
import os
import sys
import django

# Set up Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pressure_monitor'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import PatientProfile, Device, PressureFrame

source_patient = PatientProfile.objects.get(user__username='patient@local.test')
source_device = source_patient.devices.first()
target_patient = PatientProfile.objects.first()

if source_device and target_patient:
    new_device = Device.objects.create(
        patient_profile=target_patient,
        name='Pressure Device',
        serial_number='TEST-001'
    )
    print(f'Created device for {target_patient.user.username}')
    
    frames = source_device.pressure_frames.all()
    for frame in frames:
        PressureFrame.objects.create(
            device=new_device,
            recorded_at=frame.recorded_at,
            data=frame.data,
            source_filename=frame.source_filename,
            frame_index=frame.frame_index
        )
    print(f'Copied {frames.count()} frames to new device')
else:
    print('Error: Missing source device or target patient')
