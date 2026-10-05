from django.contrib import admin
from apps.placements.models import PlacementDrive, PlacementApplication


@admin.register(PlacementDrive)
class PlacementDriveAdmin(admin.ModelAdmin):
    list_display = [
        "company_name",
        "company_code",
        "role",
        "mode_of_work",
        "stipend_or_ctc",
        "status",
        "application_deadline",
        "is_active",
        "created_at",
    ]
    list_filter = ["status", "mode_of_work", "is_active", "created_at"]
    search_fields = ["company_name", "company_code", "role", "skills", "location"]


@admin.register(PlacementApplication)
class PlacementApplicationAdmin(admin.ModelAdmin):
    list_display = [
        "student_name",
        "student_id_number",
        "drive",
        "status",
        "cgpa_or_percentage",
        "branch",
        "submitted_at",
        "reviewed_at",
    ]
    list_filter = ["status", "submitted_at", "reviewed_at"]
    search_fields = [
        "student_name",
        "student_id_number",
        "email",
        "drive__company_name",
        "drive__role",
        "branch",
    ]
