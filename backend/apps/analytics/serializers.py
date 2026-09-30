"""Serializers for Admin Analytics, KPI Dashboards, and Asynchronous Report Exports."""

from rest_framework import serializers

from apps.analytics.models import ExportJob


class ExportJobCreateSerializer(serializers.Serializer):
    """Payload serializer for initiating asynchronous report exports."""

    report_type = serializers.ChoiceField(choices=ExportJob.ReportType.choices)
    format = serializers.ChoiceField(
        choices=ExportJob.ExportFormat.choices, default=ExportJob.ExportFormat.CSV
    )
    filters = serializers.DictField(required=False, default=dict)


class ExportJobSerializer(serializers.ModelSerializer):
    """Serializer for tracking export job status, size, and download link."""

    download_url = serializers.SerializerMethodField()
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = ExportJob
        fields = [
            "id",
            "user_email",
            "report_type",
            "format",
            "status",
            "filters",
            "file_name",
            "file_size_bytes",
            "row_count",
            "error_message",
            "created_at",
            "completed_at",
            "download_url",
        ]
        read_only_fields = fields

    def get_download_url(self, obj) -> str:
        if obj.status == ExportJob.JobStatus.COMPLETED and obj.file_path:
            return f"/api/v1/admin/reports/exports/{obj.id}/download/"
        return ""
