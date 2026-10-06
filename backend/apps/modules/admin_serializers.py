"""Admin serializers for curriculum module management."""

from rest_framework import serializers

from apps.modules.models import Module, ModulePrerequisite


class PrerequisiteBriefSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="prerequisite_module.id")
    title = serializers.CharField(source="prerequisite_module.title")
    order_index = serializers.IntegerField(source="prerequisite_module.order_index")

    class Meta:
        model = ModulePrerequisite
        fields = ["id", "title", "order_index"]


class ModuleAdminSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(source="course.id")
    course_title = serializers.CharField(source="course.title")
    questions_count = serializers.SerializerMethodField()
    prerequisites = PrerequisiteBriefSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = [
            "id",
            "course_id",
            "course_title",
            "title",
            "slug",
            "order_index",
            "summary",
            "lecture_content",
            "passing_percentage",
            "is_published",
            "questions_count",
            "videos_count",
            "prerequisites",
            "created_at",
            "updated_at",
        ]

    def get_questions_count(self, obj) -> int:
        return obj.questions.count()

    def get_videos_count(self, obj) -> int:
        return obj.recorded_classes.count()


class ModuleAdminCreateSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    title = serializers.CharField(max_length=150)
    slug = serializers.SlugField(max_length=180, required=False)
    order_index = serializers.IntegerField(required=False, min_value=1)
    summary = serializers.CharField(required=False, allow_blank=True, default="")
    lecture_content = serializers.CharField(required=False, allow_blank=True, default="")
    passing_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, default=80.00
    )
    is_published = serializers.BooleanField(required=False, default=True)
    prerequisite_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )


class ModuleAdminUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=150, required=False)
    slug = serializers.SlugField(max_length=180, required=False)
    order_index = serializers.IntegerField(required=False, min_value=1)
    summary = serializers.CharField(required=False, allow_blank=True)
    lecture_content = serializers.CharField(required=False, allow_blank=True)
    passing_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    is_published = serializers.BooleanField(required=False)
    prerequisite_ids = serializers.ListField(child=serializers.UUIDField(), required=False)


class ModuleReorderItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    order_index = serializers.IntegerField(min_value=1)


class ModuleReorderSerializer(serializers.Serializer):
    course_id = serializers.UUIDField()
    orders = serializers.ListField(child=ModuleReorderItemSerializer(), allow_empty=False)


class ModulePublishSerializer(serializers.Serializer):
    is_published = serializers.BooleanField()
