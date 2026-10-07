"""Script to create or reset valid credentials for Admin and Student in Supabase database."""

import os
import sys
from pathlib import Path
from decimal import Decimal

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from apps.accounts.models import User, AdminProfile
from apps.students.models import StudentProfile

def create_credentials():
    print("Connecting to Supabase PostgreSQL database...", flush=True)

    # 1. Admin Account
    admin_email = os.environ.get("INITIAL_ADMIN_EMAIL", "admin@gqt.edu")
    admin_pass = os.environ.get("INITIAL_ADMIN_PASSWORD")
    admin_mobile = os.environ.get("INITIAL_ADMIN_MOBILE", "+919876543210")

    print("Creating/updating admin user...", flush=True)
    admin_user, created = User.objects.get_or_create(
        email=admin_email,
        defaults={
            "mobile_number": admin_mobile,
            "role": User.RoleChoices.ADMIN,
            "onboarding_status": User.OnboardingStatusChoices.ACTIVE,
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
        }
    )
    if admin_pass:
        admin_user.set_password(admin_pass)
    admin_user.role = User.RoleChoices.ADMIN
    admin_user.is_active = True
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.onboarding_status = User.OnboardingStatusChoices.ACTIVE
    admin_user.save()

    admin_profile, _ = AdminProfile.objects.get_or_create(
        user=admin_user,
        defaults={
            "department": "Academic Operations & Curriculum Management",
            "can_review_projects": True,
            "can_manage_curriculum": True,
        }
    )
    admin_profile.can_review_projects = True
    admin_profile.can_manage_curriculum = True
    admin_profile.save()

    print(f"[{'CREATED' if created else 'UPDATED'}] Admin User: {admin_email}", flush=True)

    # 2. Student Account
    student_email = os.environ.get("INITIAL_STUDENT_EMAIL", "student@gqt.edu")
    student_pass = os.environ.get("INITIAL_STUDENT_PASSWORD")
    student_mobile = os.environ.get("INITIAL_STUDENT_MOBILE", "+919876543211")

    print("Creating/updating student user...", flush=True)
    student_user, created_student = User.objects.get_or_create(
        email=student_email,
        defaults={
            "mobile_number": student_mobile,
            "role": User.RoleChoices.STUDENT,
            "onboarding_status": User.OnboardingStatusChoices.ACTIVE,
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
        }
    )
    if student_pass:
        student_user.set_password(student_pass)
    student_user.role = User.RoleChoices.STUDENT
    student_user.is_active = True
    student_user.onboarding_status = User.OnboardingStatusChoices.ACTIVE
    student_user.save()

    student_profile, _ = StudentProfile.objects.get_or_create(
        user=student_user,
        defaults={
            "student_id_number": "GQT2026-001",
            "full_name": "Rahul Sharma",
            "batch_code": "BATCH-2026-A",
            "college_name": "Global Institute of Technology",
            "graduation_year": 2026,
            "total_points": Decimal("150.00"),
            "current_streak_days": 5,
            "highest_streak_days": 7,
        }
    )
    student_profile.full_name = "Rahul Sharma"
    student_profile.batch_code = "BATCH-2026-A"
    student_profile.save()

    print(f"[{'CREATED' if created_student else 'UPDATED'}] Student User: {student_email}", flush=True)
    print(f"   Student ID: {student_profile.student_id_number}", flush=True)
    print(f"   Full Name:  {student_profile.full_name}", flush=True)
    print(f"   Batch:      {student_profile.batch_code}", flush=True)
    print(f"   Mobile:     {student_mobile}\n", flush=True)

    print(">>> Accounts provisioned successfully in database! <<<", flush=True)

if __name__ == "__main__":
    create_credentials()
