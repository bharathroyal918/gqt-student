from rest_framework import serializers
from apps.accounts.models import User, AdminProfile
from apps.students.models import StudentProfile


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RequestOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=20)


class VerifyOTPSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=20)
    otp = serializers.CharField(min_length=6, max_length=6)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=10, write_only=True)


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
