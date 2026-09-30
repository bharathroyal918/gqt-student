"""Admin serializers for course management."""

from rest_framework import serializers

from apps.courses.models import Course, CourseEnrollment


class CourseAdminSerializer(serializers.ModelSerializer):
    modules_count = serializers.SerializerMethodField()
    enrolled_students_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "thumbnail_url",
            "is_published",
            "is_deleted",
            "order",
            "modules_count",
            "enrolled_students_count",
            "created_at",
            "updated_at",
        ]

    def get_modules_count(self, obj) -> int:
        return obj.modules.count()

    def get_enrolled_students_count(self, obj) -> int:
        return obj.enrollments.filter(status=CourseEnrollment.EnrollmentStatus.ACTIVE).count()


class CourseAdminCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=220, required=False)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    thumbnail_url = serializers.URLField(
        max_length=500, required=False, allow_blank=True, default=""
    )
    is_published = serializers.BooleanField(required=False, default=False)
    order = serializers.IntegerField(required=False, default=0, min_value=0)


class CourseAdminUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    slug = serializers.SlugField(max_length=220, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    thumbnail_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    is_published = serializers.BooleanField(required=False)
    order = serializers.IntegerField(required=False, min_value=0)


class CoursePublishSerializer(serializers.Serializer):
    is_published = serializers.BooleanField()
