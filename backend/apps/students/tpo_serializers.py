"""TPO Serializers for profile, college summary, roster, and student performance."""

from rest_framework import serializers

from apps.accounts.models import TPOProfile
from apps.students.models import College, StudentProfile


class TPOCollegeBriefSerializer(serializers.ModelSerializer):
    """Minimal college details for TPO profile and dashboard context."""

    class Meta:
        model = College
        fields = ["id", "name", "code", "city", "state", "is_active"]
        read_only_fields = fields


class TPOProfileDetailSerializer(serializers.ModelSerializer):
    """Detailed TPO profile representation including linked college and user info."""

    email = serializers.EmailField(source="user.email", read_only=True)
    mobile_number = serializers.CharField(source="user.mobile_number", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)
    college = TPOCollegeBriefSerializer(read_only=True)

    class Meta:
        model = TPOProfile
        fields = [
            "id",
            "email",
            "mobile_number",
            "role",
            "full_name",
            "designation",
            "department",
            "phone_number",
            "bio",
            "avatar_url",
            "is_active",
            "college",
            "assigned_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "email",
            "mobile_number",
            "role",
            "is_active",
            "college",
            "assigned_at",
            "created_at",
            "updated_at",
        ]


class TPOProfileUpdateSerializer(serializers.ModelSerializer):
    """Strict serializer allowlisting only editable TPO profile fields.

    SECURITY RULE:
    TPOs are strictly prohibited from changing user, role, email, college,
    is_active status, or administrative assignment metadata.
    """

    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    designation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    bio = serializers.CharField(required=False, allow_blank=True)
    avatar_url = serializers.CharField(max_length=500, required=False, allow_blank=True)

    class Meta:
        model = TPOProfile
        fields = [
            "full_name",
            "designation",
            "department",
            "phone_number",
            "bio",
            "avatar_url",
        ]


class TPOLoginSerializer(serializers.Serializer):
    """Authentication payload for TPO Portal login."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class TPOStudentRosterSerializer(serializers.ModelSerializer):
    """Read-only serializer for college-scoped student roster list view."""

    email = serializers.EmailField(source="user.email", read_only=True)
    mobile_number = serializers.CharField(source="user.mobile_number", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    college_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "student_id_number",
            "full_name",
            "email",
            "mobile_number",
            "batch_code",
            "college_id",
            "college_name",
            "branch",
            "course_opted",
            "attendance_percentage",
            "total_points",
            "current_streak_days",
            "highest_streak_days",
            "avatar_url",
            "is_active",
            "created_at",
        ]
        read_only_fields = fields

    def get_college_name(self, obj):
        return obj.college.name if obj.college else obj.college_name


class TPOCollegeSummaryPerformerSerializer(serializers.Serializer):
    id = serializers.CharField()
    student_id_number = serializers.CharField()
    full_name = serializers.CharField()
    total_points = serializers.FloatField()
    batch_code = serializers.CharField()
    branch = serializers.CharField()
    attendance_percentage = serializers.FloatField()
    avatar_url = serializers.CharField(allow_blank=True)


class TPOCollegeSummaryDistributionSerializer(serializers.Serializer):
    name = serializers.CharField()
    count = serializers.IntegerField()


class TPOCollegeSummaryBatchSerializer(serializers.Serializer):
    batch_code = serializers.CharField()
    count = serializers.IntegerField()


class TPOCollegeSummarySerializer(serializers.Serializer):
    """Aggregated dashboard telemetry serializer for the TPO's assigned college."""

    college = TPOCollegeBriefSerializer()
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    inactive_students = serializers.IntegerField()
    average_attendance_percentage = serializers.FloatField()
    students_above_75_attendance = serializers.IntegerField()
    total_submissions = serializers.IntegerField()
    accepted_submissions = serializers.IntegerField()
    technology_distribution = TPOCollegeSummaryDistributionSerializer(many=True)
    branch_distribution = TPOCollegeSummaryDistributionSerializer(many=True)
    batch_distribution = TPOCollegeSummaryBatchSerializer(many=True)
    top_performers = TPOCollegeSummaryPerformerSerializer(many=True)


class TPOStudentEnrollmentSerializer(serializers.Serializer):
    id = serializers.CharField()
    course_id = serializers.CharField()
    course_title = serializers.CharField()
    status = serializers.CharField()
    enrolled_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField(allow_null=True)


class TPOStudentSubmissionSerializer(serializers.Serializer):
    id = serializers.CharField()
    question_id = serializers.CharField(allow_null=True)
    question_title = serializers.CharField()
    language = serializers.CharField()
    status = serializers.CharField()
    score_awarded = serializers.FloatField()
    passed_test_cases = serializers.IntegerField()
    total_test_cases = serializers.IntegerField()
    submitted_at = serializers.DateTimeField()


class TPOStudentAttendanceRecordSerializer(serializers.Serializer):
    id = serializers.CharField()
    date = serializers.DateField()
    session_title = serializers.CharField()
    technology = serializers.CharField()
    status = serializers.CharField()
    remarks = serializers.CharField(allow_blank=True)


class TPOStudentDetailSerializer(serializers.Serializer):
    """Detailed read-only student academic and performance profile for TPO inspection."""

    id = serializers.CharField()
    user_id = serializers.CharField(allow_null=True)
    student_id_number = serializers.CharField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    batch_code = serializers.CharField()
    college_id = serializers.CharField(allow_null=True)
    college_name = serializers.CharField()
    branch = serializers.CharField()
    graduation_year = serializers.IntegerField(allow_null=True)
    course_opted = serializers.CharField()
    bio = serializers.CharField(allow_blank=True)
    github_url = serializers.CharField(allow_blank=True)
    linkedin_url = serializers.CharField(allow_blank=True)
    attendance_percentage = serializers.FloatField()
    total_classes = serializers.IntegerField()
    attended_classes = serializers.IntegerField()
    current_streak_days = serializers.IntegerField()
    highest_streak_days = serializers.IntegerField()
    total_points = serializers.FloatField()
    avatar_url = serializers.CharField(allow_blank=True)
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    enrollments = TPOStudentEnrollmentSerializer(many=True)
    recent_submissions = TPOStudentSubmissionSerializer(many=True)
    score_breakdown = serializers.DictField(child=serializers.FloatField())
    recent_attendance = TPOStudentAttendanceRecordSerializer(many=True)


# --- Phase 5 Analytics Serializers ---


class TPOCourseProgressionSummarySerializer(serializers.Serializer):
    course_id = serializers.CharField()
    course_title = serializers.CharField()
    enrolled_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    in_progress_count = serializers.IntegerField()


class TPOModuleCompletionSummarySerializer(serializers.Serializer):
    module_id = serializers.CharField()
    module_title = serializers.CharField()
    course_title = serializers.CharField()
    order_index = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    in_progress_count = serializers.IntegerField()


class TPOStudentProgressItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    student_id_number = serializers.CharField()
    full_name = serializers.CharField()
    batch_code = serializers.CharField()
    branch = serializers.CharField()
    course_opted = serializers.CharField()
    completed_modules = serializers.IntegerField()
    total_modules = serializers.IntegerField()
    progress_percentage = serializers.FloatField()
    status = serializers.CharField()


class TPOLearningProgressResponseSerializer(serializers.Serializer):
    total_students = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    total_modules = serializers.IntegerField()
    course_progression = TPOCourseProgressionSummarySerializer(many=True)
    module_completion = TPOModuleCompletionSummarySerializer(many=True)
    student_progress = TPOStudentProgressItemSerializer(many=True)


class TPOLanguageStatSerializer(serializers.Serializer):
    language = serializers.CharField()
    total_submissions = serializers.IntegerField()
    accepted_submissions = serializers.IntegerField()
    pass_rate = serializers.FloatField()


class TPORecentSubmissionTimelineItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    student_id = serializers.CharField()
    student_name = serializers.CharField()
    student_id_number = serializers.CharField()
    question_title = serializers.CharField()
    language = serializers.CharField()
    status = serializers.CharField()
    score_awarded = serializers.FloatField()
    passed_test_cases = serializers.IntegerField()
    total_test_cases = serializers.IntegerField()
    submitted_at = serializers.DateTimeField()


class TPOAssignmentsLabsResponseSerializer(serializers.Serializer):
    total_students = serializers.IntegerField()
    participating_students = serializers.IntegerField()
    unattempted_students = serializers.IntegerField()
    total_attempts = serializers.IntegerField()
    unique_questions_attempted = serializers.IntegerField()
    accepted_submissions = serializers.IntegerField()
    rejected_submissions = serializers.IntegerField()
    pending_submissions = serializers.IntegerField()
    pass_rate_percentage = serializers.FloatField()
    verdict_breakdown = serializers.DictField(child=serializers.IntegerField())
    language_stats = TPOLanguageStatSerializer(many=True)
    recent_timeline = TPORecentSubmissionTimelineItemSerializer(many=True)


class TPOAttendanceBandStatSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class TPOAttendanceDistributionBandsSerializer(serializers.Serializer):
    excellent_gte_85 = TPOAttendanceBandStatSerializer()
    satisfactory_75_to_84 = TPOAttendanceBandStatSerializer()
    critical_below_75 = TPOAttendanceBandStatSerializer()


class TPOAttendanceBatchBreakdownSerializer(serializers.Serializer):
    batch_code = serializers.CharField()
    student_count = serializers.IntegerField()
    average_attendance = serializers.FloatField()


class TPOCriticalAttendanceStudentSerializer(serializers.Serializer):
    id = serializers.CharField()
    student_id_number = serializers.CharField()
    full_name = serializers.CharField()
    batch_code = serializers.CharField()
    branch = serializers.CharField()
    attendance_percentage = serializers.FloatField()
    attended_classes = serializers.IntegerField()
    total_classes = serializers.IntegerField()


class TPOAttendanceAnalyticsResponseSerializer(serializers.Serializer):
    total_students = serializers.IntegerField()
    college_average_attendance = serializers.FloatField()
    policy_threshold_percentage = serializers.FloatField()
    distribution_bands = TPOAttendanceDistributionBandsSerializer()
    batch_breakdown = TPOAttendanceBatchBreakdownSerializer(many=True)
    critical_students = TPOCriticalAttendanceStudentSerializer(many=True)
    has_session_records = serializers.BooleanField()


class TPOMonthlyScoreTrendSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_points = serializers.FloatField()
    awards_count = serializers.IntegerField()


class TPOMonthlySubmissionTrendSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_submissions = serializers.IntegerField()
    accepted_submissions = serializers.IntegerField()
    pass_rate = serializers.FloatField()


class TPOPerformanceTrendsResponseSerializer(serializers.Serializer):
    has_sufficient_history = serializers.BooleanField()
    unavailable_reason = serializers.CharField(allow_blank=True)
    monthly_score_trends = TPOMonthlyScoreTrendSerializer(many=True)
    monthly_submission_trends = TPOMonthlySubmissionTrendSerializer(many=True)


class TPOSupportReasonSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    severity = serializers.CharField()
    detail = serializers.CharField()


class TPOStudentNeedingSupportSerializer(serializers.Serializer):
    id = serializers.CharField()
    student_id_number = serializers.CharField()
    full_name = serializers.CharField()
    batch_code = serializers.CharField()
    branch = serializers.CharField()
    course_opted = serializers.CharField()
    attendance_percentage = serializers.FloatField()
    total_points = serializers.FloatField()
    submissions_count = serializers.IntegerField()
    accepted_submissions_count = serializers.IntegerField()
    reasons = TPOSupportReasonSerializer(many=True)


class TPOLeaderboardItemSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    id = serializers.CharField()
    student_id_number = serializers.CharField()
    full_name = serializers.CharField()
    batch_code = serializers.CharField()
    branch = serializers.CharField()
    course_opted = serializers.CharField()
    total_points = serializers.FloatField()
    attendance_percentage = serializers.FloatField()
    current_streak_days = serializers.IntegerField()
    avatar_url = serializers.CharField(allow_blank=True)


# --- Phase 6 Report & Export Serializers ---


class TPOReportTypeSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    supported_formats = serializers.ListField(child=serializers.CharField())
    supported_filters = serializers.ListField(child=serializers.CharField())


class TPOReportPreviewRequestSerializer(serializers.Serializer):
    report_type = serializers.CharField(required=True)
    filters = serializers.DictField(required=False, default=dict)


class TPOReportPreviewResponseSerializer(serializers.Serializer):
    report_type = serializers.CharField()
    college = TPOCollegeBriefSerializer()
    total_rows = serializers.IntegerField()
    columns = serializers.ListField(child=serializers.CharField())
    preview_rows = serializers.ListField(child=serializers.ListField())
    generated_at = serializers.CharField()


class TPOReportExportRequestSerializer(serializers.Serializer):
    report_type = serializers.CharField(required=True)
    format = serializers.ChoiceField(choices=["CSV", "JSON", "csv", "json"], default="CSV")
    filters = serializers.DictField(required=False, default=dict)


