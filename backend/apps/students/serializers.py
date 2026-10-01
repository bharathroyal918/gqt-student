from rest_framework import serializers

from apps.students.models import AttendanceRecord, StudentProfile


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer strictly allowing students to update only approved personal fields.
    
    CRITICAL SECURITY & POLICY RULE:
    Students are STRICTLY PREVENTED from altering email, full_name, student_id_number,
    course_opted, batch_code, total_points, or role.
    """

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
