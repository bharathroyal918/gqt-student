"""Admin serializers for daily practice tasks and completion audits."""

from rest_framework import serializers

from apps.tasks.models import Task


class TaskAdminListSerializer(serializers.ModelSerializer):
    question_id = serializers.UUIDField(source="question.id", allow_null=True)
    question_title = serializers.CharField(source="question.title", allow_null=True)
    course_id = serializers.UUIDField(source="course.id", allow_null=True)
    course_title = serializers.CharField(source="course.title", allow_null=True)
    assigned_student_id = serializers.UUIDField(
        source="assigned_student.id", allow_null=True
    )
    assigned_student_name = serializers.CharField(
        source="assigned_student.full_name", allow_null=True
    )
    completions_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "scheduled_date",
            "deadline",
            "question_id",
            "question_title",
            "course_id",
            "course_title",
            "assigned_student_id",
            "assigned_student_name",
            "batch_code",
            "points",
            "is_active",
            "completions_count",
            "created_at",
            "updated_at",
        ]

    def get_completions_count(self, obj) -> int:
        return obj.completions.filter(is_completed=True).count()


class TaskAdminDetailSerializer(TaskAdminListSerializer):
    pass


class TaskAdminCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    scheduled_date = serializers.DateField(required=False, allow_null=True)
    deadline = serializers.DateTimeField(required=False, allow_null=True)
    question_id = serializers.UUIDField(required=False, allow_null=True)
    course_id = serializers.UUIDField(required=False, allow_null=True)
    assigned_student_id = serializers.UUIDField(required=False, allow_null=True)
    batch_code = serializers.CharField(
        max_length=50, required=False, allow_blank=True, default=""
    )
    points = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, default=20.00
    )
    is_active = serializers.BooleanField(required=False, default=True)


class TaskAdminUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False)
    scheduled_date = serializers.DateField(required=False, allow_null=True)
    deadline = serializers.DateTimeField(required=False, allow_null=True)
    question_id = serializers.UUIDField(required=False, allow_null=True)
    course_id = serializers.UUIDField(required=False, allow_null=True)
    assigned_student_id = serializers.UUIDField(required=False, allow_null=True)
    batch_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    points = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    is_active = serializers.BooleanField(required=False)


class TaskCompletionAdminSerializer(serializers.Serializer):
    id = serializers.CharField()
    student_id = serializers.CharField()
    student_id_number = serializers.CharField()
    full_name = serializers.CharField()
    avatar_url = serializers.CharField(allow_blank=True, default="")
    email = serializers.EmailField()
    batch_code = serializers.CharField(allow_blank=True)
    is_completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField()
    score_awarded = serializers.FloatField()
    submission_notes = serializers.CharField(allow_blank=True)
