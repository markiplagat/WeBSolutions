import csv
import os
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import Device, PatientProfile, PressureFrame


class Command(BaseCommand):
    help = "Import pressure-mapping CSV files into the database as PressureFrame records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            required=True,
            help="Directory containing one or more 32x32 pressure CSV files.",
        )
        parser.add_argument(
            "--patient",
            required=True,
            help="Patient username or email to attach imported frames to.",
        )
        parser.add_argument(
            "--device-name",
            default="Pressure Sensor",
            help="Name for the device that will own imported frames.",
        )
        parser.add_argument(
            "--device-serial",
            default="",
            help="Optional serial number for the imported device.",
        )
        parser.add_argument(
            "--use-filetime",
            action="store_true",
            help="Use file modification time for recorded_at timestamps.",
        )

    def parse_csv_frames(self, csv_path):
        frames = []
        current_frame = []
        with open(csv_path, newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if not row or all(cell.strip() == "" for cell in row):
                    if current_frame:
                        frames.append(current_frame)
                        current_frame = []
                    continue
                values = [int(cell.strip()) for cell in row if cell.strip() != ""]
                if values:
                    current_frame.append(values)
            if current_frame:
                frames.append(current_frame)

        if not frames:
            raise ValueError(f"No valid matrix frames found in {csv_path}")

        normalized = []
        for frame in frames:
            width = len(frame[0])
            if width == 0:
                raise ValueError(f"Empty row found in {csv_path}")
            if any(len(row) != width for row in frame):
                raise ValueError(
                    f"Inconsistent row lengths in {csv_path}: expected {width}, got {[len(row) for row in frame]}"
                )

            if width == 32 and len(frame) > 32 and len(frame) % 32 == 0:
                for i in range(0, len(frame), 32):
                    normalized.append(frame[i : i + 32])
            else:
                normalized.append(frame)

        return normalized

    def handle(self, *args, **options):
        directory = options["dir"]
        patient_id = options["patient"]
        device_name = options["device_name"]
        device_serial = options["device_serial"]
        use_filetime = options["use_filetime"]

        if not os.path.isdir(directory):
            raise CommandError(f"Directory not found: {directory}")

        User = get_user_model()
        patient_user = None
        try:
            patient_user = User.objects.get(username=patient_id)
        except User.DoesNotExist:
            try:
                patient_user = User.objects.get(email=patient_id)
            except User.DoesNotExist:
                raise CommandError(f"Patient user not found for '{patient_id}'")

        try:
            patient_profile = patient_user.userprofile.patient_profile
        except Exception:
            raise CommandError(f"User '{patient_id}' is not a patient or has no PatientProfile")

        device, device_created = Device.objects.get_or_create(
            patient_profile=patient_profile,
            serial_number=device_serial,
            defaults={"name": device_name},
        )
        if device_created:
            self.stdout.write(self.style.SUCCESS(f"Created device '{device}'"))

        file_paths = sorted(
            [
                os.path.join(directory, f)
                for f in os.listdir(directory)
                if f.lower().endswith(".csv")
            ]
        )

        if not file_paths:
            raise CommandError(f"No CSV files found in {directory}")

        created = 0
        skipped = 0
        for csv_path in file_paths:
            try:
                frames = self.parse_csv_frames(csv_path)
            except ValueError as exc:
                raise CommandError(str(exc))

            for frame_index, frame_data in enumerate(frames):
                if use_filetime:
                    timestamp = datetime.fromtimestamp(os.path.getmtime(csv_path))
                    recorded_at = timezone.make_aware(timestamp)
                else:
                    recorded_at = timezone.now()

                obj, created_flag = PressureFrame.objects.get_or_create(
                    device=device,
                    source_filename=os.path.basename(csv_path),
                    frame_index=frame_index,
                    defaults={
                        "recorded_at": recorded_at,
                        "data": frame_data,
                    },
                )
                if created_flag:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {created} new pressure frames."))
        if skipped:
            self.stdout.write(self.style.WARNING(f"Skipped {skipped} existing frames."))
