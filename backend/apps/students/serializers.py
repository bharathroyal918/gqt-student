from rest_framework import serializers

from apps.students.models import AttendanceRecord, College, StudentProfile


class CollegeSerializer(serializers.ModelSerializer):
    """Institutional college option for student profile and registration selection."""

    class Meta:
        model = College
        fields = ["id", "name", "code", "city", "state", "is_active"]


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer strictly allowing students to update only approved personal fields.

    CRITICAL SECURITY & POLICY RULE:
    Students are STRICTLY PREVENTED from altering email, full_name, student_id_number,
    course_opted, batch_code, total_points, or role.
    """

    dob = serializers.DateField(required=False, allow_null=True)
    branch = serializers.CharField(
        max_length=100, required=False, allow_blank=True, default=""
    )
    college_name = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )
    graduation_year = serializers.IntegerField(required=False, allow_null=True)
    avatar_url = serializers.CharField(
        max_length=500, required=False, allow_blank=True, default=""
    )
    bio = serializers.CharField(required=False, allow_blank=True, default="")
    github_url = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )
    linkedin_url = serializers.CharField(
        max_length=255, required=False, allow_blank=True, default=""
    )

    class Meta:
        model = StudentProfile
        fields = [
            "dob",
            "branch",
            "college_name",
            "graduation_year",
            "avatar_url",
            "bio",
            "github_url",
            "linkedin_url",
        ]

    def validate_college_name(self, value):
        if not value or not value.strip():
            return ""
        trimmed = value.strip()
        matching_college = College.objects.filter(name__iexact=trimmed, is_active=True).first()
        if not matching_college:
            if not College.objects.filter(is_active=True).exists():
                from apps.students.seeds import seed_default_colleges
                seed_default_colleges()
                matching_college = College.objects.filter(name__iexact=trimmed, is_active=True).first()

        if not matching_college:
            raise serializers.ValidationError(
                "Please select an approved college from the institutional options list."
            )
        return matching_college.name

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, "copy") else dict(data)
        if "dob" in data and (data["dob"] == "" or data["dob"] is None):
            data["dob"] = None
        if "graduation_year" in data and (
            data["graduation_year"] == "" or data["graduation_year"] is None
        ):
            data["graduation_year"] = None
        return super().to_internal_value(data)


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Individual daily attendance record."""

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "date",
            "session_title",
            "status",
            "remarks",
            "created_at",
        ]


class StudentAttendanceSummarySerializer(serializers.Serializer):
    """Aggregate attendance telemetry and session history."""

    attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_classes = serializers.IntegerField()
    attended_classes = serializers.IntegerField()
    missed_classes = serializers.IntegerField()
    records = AttendanceRecordSerializer(many=True)


class StudentAttendanceScanSerializer(serializers.Serializer):
    qr_data = serializers.CharField(required=False, default="", allow_blank=True)
    session_code = serializers.CharField(required=False, default="", allow_blank=True)


class StudentModuleCompleteSerializer(serializers.Serializer):
    score_percentage = serializers.FloatField(required=False, allow_null=True)
