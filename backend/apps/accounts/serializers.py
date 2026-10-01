from rest_framework import serializers
from apps.accounts.models import User, AdminProfile
from apps.students.models import StudentProfile


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class StudentLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class StudentRegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    mobile_number = serializers.CharField(max_length=20)
    password = serializers.CharField(min_length=8, write_only=True)
    student_id_number = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    college_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    batch_code = serializers.CharField(max_length=50, required=False, allow_blank=True, default="BATCH-2026-A")
    graduation_year = serializers.IntegerField(required=False, allow_null=True, default=2026)


class RequestOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=20)


class VerifyOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=20)
    otp = serializers.CharField(min_length=6, max_length=6)


class ForgotPasswordOTPRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        max_length=255,
        help_text="Registered email address or mobile number",
    )


class ForgotPasswordOTPVerifySerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=255)
    otp = serializers.CharField(min_length=6, max_length=6)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=255)


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(required=False, allow_blank=True, default="")
    identifier = serializers.CharField(required=False, allow_blank=True, default="")
    otp = serializers.CharField(required=False, allow_blank=True, default="")
    new_password = serializers.CharField(min_length=8, write_only=True)


class StudentProfileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "student_id_number",
            "full_name",
            "batch_code",
            "college_name",
            "graduation_year",
            "dob",
            "branch",
            "bio",
            "github_url",
            "linkedin_url",
            "course_opted",
            "attendance_percentage",
            "total_classes",
            "attended_classes",
            "current_streak_days",
            "highest_streak_days",
            "total_points",
            "avatar_url",
        ]


class AdminProfileNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminProfile
        fields = [
            "id",
            "department",
            "can_review_projects",
            "can_manage_curriculum",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileNestedSerializer(read_only=True)
    admin_profile = AdminProfileNestedSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "mobile_number",
            "role",
            "is_active",
            "onboarding_status",
            "student_profile",
            "admin_profile",
        ]


class StudentProvisionSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    student_id_number = serializers.CharField(max_length=50)
    batch_code = serializers.CharField(max_length=50)
    email = serializers.EmailField(required=False, allow_null=True)
    mobile_number = serializers.CharField(max_length=20, required=False, allow_null=True)
    password = serializers.CharField(min_length=8, required=False, allow_null=True, write_only=True)
    college_name = serializers.CharField(max_length=255, required=False, default="")
    graduation_year = serializers.IntegerField(required=False, allow_null=True)
    onboarding_status = serializers.ChoiceField(
        choices=User.OnboardingStatusChoices.choices, default=User.OnboardingStatusChoices.ACTIVE
    )


class StudentStatusUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=False, allow_null=True)
    onboarding_status = serializers.ChoiceField(
        choices=User.OnboardingStatusChoices.choices, required=False, allow_null=True
    )
    reason = serializers.CharField(max_length=255, required=False, default="")
