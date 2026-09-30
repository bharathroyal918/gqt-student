"""Admin serializers for student management and academic tracking."""

from rest_framework import serializers

from apps.accounts.models import User
from apps.courses.models import CourseEnrollment
from apps.students.models import StudentProfile


class StudentEnrollmentBriefSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(source="course.id")
    course_title = serializers.CharField(source="course.title")

    class Meta:
        model = CourseEnrollment
        fields = ["id", "course_id", "course_title", "status", "enrolled_at", "completed_at"]


class StudentAdminListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    mobile_number = serializers.CharField(source="user.mobile_number", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    onboarding_status = serializers.CharField(source="user.onboarding_status", read_only=True)
    enrolled_courses_count = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "student_id_number",
            "full_name",
            "batch_code",
            "college_name",
            "graduation_year",
            "total_points",
            "current_streak_days",
            "email",
            "mobile_number",
            "is_active",
            "onboarding_status",
            "enrolled_courses_count",
            "created_at",
        ]

    def get_enrolled_courses_count(self, obj) -> int:
        return obj.enrollments.filter(status=CourseEnrollment.EnrollmentStatus.ACTIVE).count()


class StudentAdminDetailSerializer(StudentAdminListSerializer):
    enrollments = StudentEnrollmentBriefSerializer(many=True, read_only=True)

    class Meta(StudentAdminListSerializer.Meta):
        fields = StudentAdminListSerializer.Meta.fields + ["avatar_url", "enrollments"]


class StudentAdminUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False)
    batch_code = serializers.CharField(max_length=50, required=False)
    college_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    graduation_year = serializers.IntegerField(required=False, allow_null=True)
    email = serializers.EmailField(required=False, allow_null=True)
    mobile_number = serializers.CharField(max_length=20, required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    onboarding_status = serializers.ChoiceField(
        choices=User.OnboardingStatusChoices.choices, required=False
    )


class AssignCoursesSerializer(serializers.Serializer):
    course_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        help_text="List of course UUIDs to enroll student into",
    )
