"""Admin serializers for coding questions and test cases."""

from rest_framework import serializers

from apps.assignments.models import CodingQuestion, TestCase


class TestCaseAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = [
            "id",
            "question_id",
            "input_data",
            "expected_output",
            "is_visible",
            "weight",
            "order",
            "created_at",
            "updated_at",
        ]


class TestCaseCreateSerializer(serializers.Serializer):
    input_data = serializers.CharField(allow_blank=True, default="")
    expected_output = serializers.CharField(allow_blank=True, default="")
    is_visible = serializers.BooleanField(default=True)
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    order = serializers.IntegerField(required=False, min_value=1)


class TestCaseUpdateSerializer(serializers.Serializer):
    input_data = serializers.CharField(required=False, allow_blank=True)
    expected_output = serializers.CharField(required=False, allow_blank=True)
    is_visible = serializers.BooleanField(required=False)
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    order = serializers.IntegerField(required=False, min_value=1)


class CodingQuestionAdminListSerializer(serializers.ModelSerializer):
    module_id = serializers.UUIDField(source="module.id")
    module_title = serializers.CharField(source="module.title")
    course_title = serializers.CharField(source="module.course.title")
    test_cases_count = serializers.SerializerMethodField()

    class Meta:
        model = CodingQuestion
        fields = [
            "id",
            "module_id",
            "module_title",
            "course_title",
            "title",
            "slug",
            "difficulty",
            "points",
            "order",
            "is_active",
            "test_cases_count",
            "created_at",
        ]

    def get_test_cases_count(self, obj) -> int:
        return obj.test_cases.count()


class CodingQuestionAdminDetailSerializer(CodingQuestionAdminListSerializer):
    test_cases = TestCaseAdminSerializer(many=True, read_only=True)

    class Meta(CodingQuestionAdminListSerializer.Meta):
        fields = CodingQuestionAdminListSerializer.Meta.fields + [
            "problem_statement",
            "allowed_languages",
            "starter_code",
            "time_limit_seconds",
            "memory_limit_mb",
            "test_cases",
            "updated_at",
        ]


class CodingQuestionAdminCreateSerializer(serializers.Serializer):
    module_id = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=280, required=False)
    difficulty = serializers.ChoiceField(
        choices=CodingQuestion.DifficultyChoices.choices,
        default=CodingQuestion.DifficultyChoices.EASY,
    )
    problem_statement = serializers.CharField()
    allowed_languages = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=lambda: ["python", "java", "c", "cpp", "javascript"],
    )
    starter_code = serializers.DictField(required=False, default=dict)
    time_limit_seconds = serializers.DecimalField(
        max_digits=4, decimal_places=2, required=False, default=2.00
    )
    memory_limit_mb = serializers.IntegerField(required=False, default=128, min_value=16)
    points = serializers.DecimalField(
        max_digits=7, decimal_places=2, required=False, default=100.00
    )
    order = serializers.IntegerField(required=False, default=0, min_value=0)
    is_active = serializers.BooleanField(required=False, default=True)
    test_cases = serializers.ListField(
        child=TestCaseCreateSerializer(), required=False, default=list
    )


class CodingQuestionAdminUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    slug = serializers.SlugField(max_length=280, required=False)
    difficulty = serializers.ChoiceField(
        choices=CodingQuestion.DifficultyChoices.choices, required=False
    )
    problem_statement = serializers.CharField(required=False)
    allowed_languages = serializers.ListField(child=serializers.CharField(), required=False)
    starter_code = serializers.DictField(required=False)
    time_limit_seconds = serializers.DecimalField(max_digits=4, decimal_places=2, required=False)
    memory_limit_mb = serializers.IntegerField(required=False, min_value=16)
    points = serializers.DecimalField(max_digits=7, decimal_places=2, required=False)
    order = serializers.IntegerField(required=False, min_value=0)
    is_active = serializers.BooleanField(required=False)
