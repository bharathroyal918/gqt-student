from decimal import Decimal
from rest_framework import serializers
from apps.placements.models import PlacementDrive, PlacementApplication


class PlacementDriveSerializer(serializers.ModelSerializer):
    """Full serializer for PlacementDrive with application metrics."""

    total_applications = serializers.SerializerMethodField()
    selected_count = serializers.SerializerMethodField()
    shortlisted_count = serializers.SerializerMethodField()
    rejected_count = serializers.SerializerMethodField()
    has_applied = serializers.SerializerMethodField()
    my_application_status = serializers.SerializerMethodField()
    my_application_id = serializers.SerializerMethodField()

    class Meta:
        model = PlacementDrive
        fields = [
            "id",
            "company_name",
            "company_code",
            "company_logo_url",
            "role",
            "skills",
            "location",
            "mode_of_work",
            "stipend_or_ctc",
            "bond_period",
            "eligibility_criteria",
            "min_cgpa",
            "eligible_batches",
            "job_description",
            "application_deadline",
            "drive_date",
            "status",
            "is_active",
            "created_at",
            "updated_at",
            "total_applications",
            "selected_count",
            "shortlisted_count",
            "rejected_count",
            "has_applied",
            "my_application_status",
            "my_application_id",
        ]

    def get_total_applications(self, obj) -> int:
        return obj.applications.count()

    def get_selected_count(self, obj) -> int:
        return obj.applications.filter(status=PlacementApplication.ApplicationStatus.SELECTED).count()

    def get_shortlisted_count(self, obj) -> int:
        return obj.applications.filter(status=PlacementApplication.ApplicationStatus.SHORTLISTED).count()

    def get_rejected_count(self, obj) -> int:
        return obj.applications.filter(status=PlacementApplication.ApplicationStatus.REJECTED).count()

    def _get_student_app(self, obj):
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return None
        student_profile = getattr(request.user, "student_profile", None)
        if not student_profile:
            return None
        if not hasattr(self, "_student_apps_cache"):
            self._student_apps_cache = {
                app.drive_id: app
                for app in PlacementApplication.objects.filter(student=student_profile)
            }
        return self._student_apps_cache.get(obj.id)

    def get_has_applied(self, obj) -> bool:
        return self._get_student_app(obj) is not None

    def get_my_application_status(self, obj) -> str | None:
        app = self._get_student_app(obj)
        return app.status if app else None

    def get_my_application_id(self, obj) -> str | None:
        app = self._get_student_app(obj)
        return str(app.id) if app else None


class PlacementDriveCreateUpdateSerializer(serializers.ModelSerializer):
    """Admin create / update serializer for placement drives."""

    company_code = serializers.CharField(required=False, allow_blank=True, default="")
    company_logo_url = serializers.CharField(required=False, allow_blank=True, default="")
    bond_period = serializers.CharField(required=False, allow_blank=True, default="None")
    eligibility_criteria = serializers.CharField(required=False, allow_blank=True, default="")
    eligible_batches = serializers.CharField(required=False, allow_blank=True, default="All")
    job_description = serializers.CharField(required=False, allow_blank=True, default="")
    drive_date = serializers.DateTimeField(required=False, allow_null=True)
    min_cgpa = serializers.DecimalField(max_digits=4, decimal_places=2, required=False, default=Decimal("0.00"))

    class Meta:
        model = PlacementDrive
        fields = [
            "id",
            "company_name",
            "company_code",
            "company_logo_url",
            "role",
            "skills",
            "location",
            "mode_of_work",
            "stipend_or_ctc",
            "bond_period",
            "eligibility_criteria",
            "min_cgpa",
            "eligible_batches",
            "job_description",
            "application_deadline",
            "drive_date",
            "status",
            "is_active",
        ]

    def to_internal_value(self, data):
        # Sanitize empty strings for datetime and numerical fields before validation
        if isinstance(data, dict):
            data = data.copy()
            if data.get("drive_date") == "":
                data["drive_date"] = None
            if data.get("application_deadline") == "":
                data["application_deadline"] = None
            if data.get("min_cgpa") == "" or data.get("min_cgpa") is None:
                data["min_cgpa"] = "0.00"
        return super().to_internal_value(data)


class PlacementApplicationSerializer(serializers.ModelSerializer):
    """Detailed serializer for student placement application submissions."""

    drive_details = serializers.SerializerMethodField()
    has_resume_file = serializers.SerializerMethodField()
    resume_download_url = serializers.SerializerMethodField()
    student_avatar_url = serializers.CharField(source="student.avatar_url", read_only=True, default="")

    class Meta:
        model = PlacementApplication
        fields = [
            "id",
            "drive",
            "drive_details",
            "student",
            "status",
            "submitted_at",
            "reviewed_at",
            "admin_notes",
            "rejection_reason",
            "student_name",
            "student_id_number",
            "student_avatar_url",
            "email",
            "phone_number",
            "college_name",
            "branch",
            "graduation_year",
            "cgpa_or_percentage",
            "resume_file",
            "resume_filename",
            "has_resume_file",
            "resume_download_url",
            "resume_url",
            "portfolio_url",
            "github_url",
            "linkedin_url",
            "skills_summary",
            "cover_note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "submitted_at", "reviewed_at", "created_at", "updated_at"]

    def get_drive_details(self, obj) -> dict:
        return {
            "id": str(obj.drive.id),
            "company_name": obj.drive.company_name,
            "company_code": obj.drive.company_code,
            "role": obj.drive.role,
            "stipend_or_ctc": obj.drive.stipend_or_ctc,
            "location": obj.drive.location,
            "mode_of_work": obj.drive.mode_of_work,
            "bond_period": obj.drive.bond_period,
            "application_deadline": obj.drive.application_deadline,
            "status": obj.drive.status,
        }

    def get_has_resume_file(self, obj) -> bool:
        return bool(obj.resume_file)

    def get_resume_download_url(self, obj) -> str | None:
        if obj.resume_file:
            return f"/api/v1/students/placements/applications/{obj.id}/resume/"
        return None


class StudentApplyPlacementSerializer(serializers.Serializer):
    """Input payload for a student applying to a placement drive."""

    phone_number = serializers.CharField(max_length=30, required=True)
    college_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    branch = serializers.CharField(max_length=100, required=False, allow_blank=True)
    graduation_year = serializers.IntegerField(required=False, allow_null=True)
    cgpa_or_percentage = serializers.CharField(max_length=50, required=True)
    resume_file = serializers.FileField(required=False, allow_null=True)
    resume_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    portfolio_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    github_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    linkedin_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    skills_summary = serializers.CharField(required=False, allow_blank=True)
    cover_note = serializers.CharField(required=False, allow_blank=True)

    def to_internal_value(self, data):
        if hasattr(data, "dict"):
            data = data.dict()
        elif isinstance(data, dict):
            data = data.copy()
        if isinstance(data, dict):
            if data.get("graduation_year") == "" or data.get("graduation_year") == "null":
                data["graduation_year"] = None
            if data.get("resume_file") == "" or data.get("resume_file") == "null":
                data["resume_file"] = None
        return super().to_internal_value(data)

    def validate(self, attrs):
        resume_file = attrs.get("resume_file")
        resume_url = attrs.get("resume_url")
        if not resume_file and not resume_url:
            raise serializers.ValidationError(
                {"resume_file": "Please upload a resume file (PDF/DOCX) or provide a resume link."}
            )
        return attrs


class UpdateApplicationStatusSerializer(serializers.Serializer):
    """Admin payload to update student application status and feedback."""

    status = serializers.ChoiceField(choices=PlacementApplication.ApplicationStatus.choices)
    admin_notes = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
