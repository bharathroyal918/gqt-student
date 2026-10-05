"""Serializers for Student Coding Practice Platform."""

from rest_framework import serializers

from apps.assignments.models import CodingQuestion, CodeSubmission, TestCase


class StudentTestCaseSerializer(serializers.ModelSerializer):
    """Public sample testcase serializer visible to students."""

    class Meta:
        model = TestCase
        fields = ["id", "input_data", "expected_output", "order"]


class StudentQuestionListSerializer(serializers.ModelSerializer):
    """Overview serializer for practice problem catalog."""

    points = serializers.FloatField(read_only=True)
    module_title = serializers.CharField(source="module.title", read_only=True)
    module_order = serializers.IntegerField(source="module.order_index", read_only=True)
    course_title = serializers.CharField(source="module.course.title", read_only=True)
    is_solved = serializers.BooleanField(default=False, read_only=True)
    best_score = serializers.FloatField(default=0.0, read_only=True)
    attempts_count = serializers.IntegerField(default=0, read_only=True)
    is_module_locked = serializers.BooleanField(default=False, read_only=True)
    module_unlock_requirement = serializers.CharField(default=None, allow_null=True, read_only=True)

    class Meta:
        model = CodingQuestion
        fields = [
            "id",
            "title",
            "slug",
            "difficulty",
            "points",
            "module_id",
            "module_title",
            "module_order",
            "course_title",
            "allowed_languages",
            "is_solved",
            "best_score",
            "attempts_count",
            "is_module_locked",
            "module_unlock_requirement",
        ]


class StudentQuestionDetailSerializer(serializers.ModelSerializer):
    """In-depth algorithmic challenge detail including constraints, starter code, and sample testcases."""

    points = serializers.FloatField(read_only=True)
    time_limit_seconds = serializers.FloatField(read_only=True)
    module_title = serializers.CharField(source="module.title", read_only=True)
    module_order = serializers.IntegerField(source="module.order_index", read_only=True)
    course_title = serializers.CharField(source="module.course.title", read_only=True)
    visible_test_cases = serializers.SerializerMethodField()
    is_solved = serializers.BooleanField(default=False, read_only=True)
    best_score = serializers.FloatField(default=0.0, read_only=True)
    attempts_count = serializers.IntegerField(default=0, read_only=True)
    is_module_locked = serializers.BooleanField(default=False, read_only=True)
    module_unlock_requirement = serializers.CharField(default=None, allow_null=True, read_only=True)
    last_submission_code = serializers.CharField(default=None, allow_null=True, read_only=True)
    last_submission_language = serializers.CharField(default=None, allow_null=True, read_only=True)
    submissions_by_language = serializers.DictField(default=dict, read_only=True)

    class Meta:
        model = CodingQuestion
        fields = [
            "id",
            "title",
            "slug",
            "difficulty",
            "problem_statement",
            "points",
            "module_id",
            "module_title",
            "module_order",
            "course_title",
            "allowed_languages",
            "starter_code",
            "time_limit_seconds",
            "memory_limit_mb",
            "visible_test_cases",
            "is_solved",
            "best_score",
            "attempts_count",
            "is_module_locked",
            "module_unlock_requirement",
            "last_submission_code",
            "last_submission_language",
            "submissions_by_language",
        ]

    def get_visible_test_cases(self, obj):
        # Strict security rule: Only query and expose visible testcases
        visible_qs = obj.test_cases.filter(is_visible=True).order_by("order")
        return StudentTestCaseSerializer(visible_qs, many=True).data


class CodeRunRequestSerializer(serializers.Serializer):
    language = serializers.CharField(max_length=30)
    source_code = serializers.CharField()
    custom_input = serializers.CharField(required=False, allow_blank=True, default=None)


class CodeSubmitRequestSerializer(serializers.Serializer):
    language = serializers.CharField(max_length=30)
    source_code = serializers.CharField()


class StudentSubmissionSerializer(serializers.ModelSerializer):
    question_title = serializers.CharField(source="question.title", read_only=True)

    class Meta:
        model = CodeSubmission
        fields = [
            "id",
            "question_id",
            "question_title",
            "language",
            "status",
            "passed_test_cases",
            "total_test_cases",
            "score_awarded",
            "execution_time_ms",
            "peak_memory_kb",
            "submitted_at",
        ]
