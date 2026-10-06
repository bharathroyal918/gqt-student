"""Admin serializers for course management."""

from rest_framework import serializers

from apps.courses.models import Course, CourseEnrollment, RecordedClass


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


class RecordedClassAdminSerializer(serializers.ModelSerializer):
    video_file_url = serializers.SerializerMethodField()
    module_title = serializers.SerializerMethodField()
    is_free_preview = serializers.BooleanField(read_only=True)

    class Meta:
        model = RecordedClass
        fields = [
            "id",
            "course",
            "module",
            "module_title",
            "title",
            "slug",
            "description",
            "order_index",
            "video_source_type",
            "youtube_url",
            "youtube_video_id",
            "video_file",
            "video_file_url",
            "video_url",
            "duration_seconds",
            "duration_formatted",
            "thumbnail_url",
            "is_preview",
            "is_free_preview",
            "is_published",
            "notes",
            "resources_url",
            "created_at",
            "updated_at",
        ]

    def get_video_file_url(self, obj) -> str:
        return obj.video_file.url if obj.video_file else ""

    def get_module_title(self, obj) -> str:
        return obj.module.title if obj.module else ""


class RecordedClassAdminCreateUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    slug = serializers.SlugField(max_length=280, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    order_index = serializers.IntegerField(required=False, min_value=1)
    video_source_type = serializers.ChoiceField(
        choices=RecordedClass.VideoSourceType.choices,
        default=RecordedClass.VideoSourceType.YOUTUBE,
    )
    youtube_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default="")
    video_file = serializers.FileField(required=False, allow_null=True)
    video_url = serializers.URLField(max_length=1000, required=False, allow_blank=True, default="")
    duration_seconds = serializers.IntegerField(required=False, default=0, min_value=0)
    duration_formatted = serializers.CharField(max_length=20, required=False, allow_blank=True, default="00:00")
    thumbnail_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default="")
    is_preview = serializers.BooleanField(required=False, default=False)
    is_published = serializers.BooleanField(required=False, default=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    resources_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default="")
    module_id = serializers.UUIDField(required=False, allow_null=True)


class RecordedClassesReorderSerializer(serializers.Serializer):
    order_items = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
    )


class CourseEnrollmentAdminSerializer(serializers.ModelSerializer):
    student_id = serializers.CharField(source="student.id", read_only=True)
    student_id_number = serializers.CharField(source="student.student_id_number", read_only=True)
    full_name = serializers.CharField(source="student.full_name", read_only=True)
    email = serializers.CharField(source="student.user.email", read_only=True)
    batch_code = serializers.CharField(source="student.batch_code", read_only=True)
    avatar_url = serializers.CharField(source="student.avatar_url", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = [
            "id",
            "student_id",
            "student_id_number",
            "full_name",
            "email",
            "batch_code",
            "avatar_url",
            "course",
            "course_title",
            "status",
            "enrolled_at",
            "completed_at",
        ]


class CourseEnrollmentAllocateSerializer(serializers.Serializer):
    student_id = serializers.UUIDField(required=True)
    status = serializers.ChoiceField(
        choices=CourseEnrollment.EnrollmentStatus.choices,
        default=CourseEnrollment.EnrollmentStatus.ACTIVE,
    )

