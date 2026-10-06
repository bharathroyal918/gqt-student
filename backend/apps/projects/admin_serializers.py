"""Admin serializers for capstone projects, submissions, and reviews."""

from rest_framework import serializers

from apps.projects.models import Project, ProjectFeedback, ProjectFile, ProjectSubmission


class ProjectFileAdminSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectFile
        fields = ["id", "file_name", "file_size_bytes", "mime_type", "download_url", "uploaded_at"]

    def get_download_url(self, obj) -> str:
        return f"/api/v1/projects/files/{obj.id}/download/"


class ProjectFeedbackAdminSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source="reviewer.email", default="")

    class Meta:
        model = ProjectFeedback
        fields = [
            "id",
            "reviewer_name",
            "feedback_text",
            "suggested_changes",
            "rating",
            "created_at",
        ]


class ProjectAdminSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(source="course.id", allow_null=True)
    course_title = serializers.CharField(source="course.title", allow_null=True)
    submissions_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "deliverables_instructions",
            "course_id",
            "course_title",
            "max_score",
            "due_date",
            "is_active",
            "submissions_count",
            "created_at",
            "updated_at",
        ]

    def get_submissions_count(self, obj) -> int:
        return obj.submissions.count()


class ProjectAdminCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    slug = serializers.SlugField(max_length=220, required=False)
    description = serializers.CharField()
    deliverables_instructions = serializers.CharField()
    course_id = serializers.UUIDField(required=False, allow_null=True)
    max_score = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, default=100.00
    )
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)


class ProjectAdminUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False)
    slug = serializers.SlugField(max_length=220, required=False)
    description = serializers.CharField(required=False)
    deliverables_instructions = serializers.CharField(required=False)
    course_id = serializers.UUIDField(required=False, allow_null=True)
    max_score = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    due_date = serializers.DateTimeField(required=False, allow_null=True)
    is_active = serializers.BooleanField(required=False)


class ProjectSubmissionAdminListSerializer(serializers.ModelSerializer):
    project_id = serializers.UUIDField(source="project.id")
    project_title = serializers.CharField(source="project.title")
    max_score = serializers.DecimalField(source="project.max_score", max_digits=6, decimal_places=2)
    student_id = serializers.UUIDField(source="student.id")
    student_name = serializers.CharField(source="student.full_name")
    student_id_number = serializers.CharField(source="student.student_id_number")
    student_avatar_url = serializers.CharField(source="student.avatar_url", read_only=True, default="")

    class Meta:
        model = ProjectSubmission
        fields = [
            "id",
            "project_id",
            "project_title",
            "student_id",
            "student_name",
            "student_id_number",
            "student_avatar_url",
            "status",
            "score",
            "max_score",
            "github_repository_url",
            "live_demo_url",
            "submitted_at",
            "reviewed_at",
        ]


class ProjectSubmissionAdminDetailSerializer(ProjectSubmissionAdminListSerializer):
    files = ProjectFileAdminSerializer(many=True, read_only=True)
    feedbacks = ProjectFeedbackAdminSerializer(many=True, read_only=True)
    reviewed_by_email = serializers.EmailField(source="reviewed_by.email", allow_null=True)

    class Meta(ProjectSubmissionAdminListSerializer.Meta):
        fields = ProjectSubmissionAdminListSerializer.Meta.fields + [
            "notes",
            "files",
            "feedbacks",
            "reviewed_by_email",
        ]


class ProjectReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ProjectSubmission.SubmissionStatus.choices)
    score = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=False, allow_null=True
    )
    feedback_text = serializers.CharField(required=False, allow_blank=True, default="")
    suggested_changes = serializers.CharField(required=False, allow_blank=True, default="")
    rating = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=5)
