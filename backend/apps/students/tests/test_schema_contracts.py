"""Regression tests for drf-spectacular schema generation and API contracts."""

from django.core.management import call_command
from django.test import TestCase
from drf_spectacular.drainage import GENERATOR_STATS
from drf_spectacular.settings import spectacular_settings

from apps.students.admin_serializers import CollegeAdminSerializer
from apps.students.models import College, StudentProfile
from apps.students.tpo_serializers import (
    TPOStudentRosterSerializer,
    TPORegisterSerializer,
    TPOLoginSerializer,
    TPOReportExportRequestSerializer,
)


class SpectacularSchemaContractsTests(TestCase):
    """Verify OpenAPI schema generation integrity and absence of warnings/collisions."""

    def test_deploy_check_clean(self):
        """Verify drf-spectacular deploy system check identifies 0 issues and 0 warnings."""
        from drf_spectacular.checks import schema_check

        issues = schema_check(None)
        self.assertEqual(issues, [], f"Unexpected schema check issues: {issues}")

    def test_openapi_schema_generation_without_warnings(self):
        """Verify spectacular generator runs public schema generation with zero warnings and zero errors."""
        with GENERATOR_STATS.silence():
            generator = spectacular_settings.DEFAULT_GENERATOR_CLASS()
            schema = generator.get_schema(request=None, public=True)

        self.assertIsNotNone(schema)
        self.assertEqual(len(GENERATOR_STATS._warn_cache), 0, f"Unexpected warnings: {GENERATOR_STATS._warn_cache}")
        self.assertEqual(len(GENERATOR_STATS._error_cache), 0, f"Unexpected errors: {GENERATOR_STATS._error_cache}")

    def test_college_admin_serializer_student_count_schema(self):
        """Verify CollegeAdminSerializer defines student_count with integer type."""
        generator = spectacular_settings.DEFAULT_GENERATOR_CLASS()
        schema = generator.get_schema(request=None, public=True)
        college_schema = schema["components"]["schemas"].get("CollegeAdmin")
        self.assertIsNotNone(college_schema)
        self.assertIn("student_count", college_schema["properties"])
        self.assertEqual(college_schema["properties"]["student_count"]["type"], "integer")

    def test_tpo_student_roster_serializer_college_name_schema(self):
        """Verify TPOStudentRosterSerializer defines college_name as nullable string."""
        generator = spectacular_settings.DEFAULT_GENERATOR_CLASS()
        schema = generator.get_schema(request=None, public=True)
        roster_schema = schema["components"]["schemas"].get("TPOStudentRoster")
        self.assertIsNotNone(roster_schema)
        self.assertIn("college_name", roster_schema["properties"])
        prop = roster_schema["properties"]["college_name"]
        self.assertEqual(prop.get("type"), "string")
        self.assertTrue(prop.get("nullable", False))

    def test_format_enum_naming_no_collision(self):
        """Verify enum naming collision for format is resolved with stable overrides."""
        generator = spectacular_settings.DEFAULT_GENERATOR_CLASS()
        schema = generator.get_schema(request=None, public=True)
        components = schema["components"]["schemas"]

        # Ensure no mangled hash enum like Format241Enum exists
        mangled_enums = [k for k in components.keys() if k.startswith("Format") and "Enum" in k]
        self.assertEqual(mangled_enums, [], f"Encountered collision-mangled format enum: {mangled_enums}")

        # Ensure stable, semantic enums exist
        self.assertIn("ExportJobFormatEnum", components)
        self.assertIn("TPOReportExportRequestFormatEnum", components)
        self.assertEqual(components["ExportJobFormatEnum"]["enum"], ["CSV", "JSON"])
        self.assertEqual(
            components["TPOReportExportRequestFormatEnum"]["enum"],
            ["CSV", "JSON", "csv", "json"],
        )

    def test_tpo_auth_and_report_export_views_schema(self):
        """Verify TPOLoginView, TPORegisterView, and TPOReportExportView paths in schema."""
        generator = spectacular_settings.DEFAULT_GENERATOR_CLASS()
        schema = generator.get_schema(request=None, public=True)
        paths = schema.get("paths", {})

        # 1. TPO Register endpoint
        register_path = paths.get("/api/v1/tpo/auth/register/")
        self.assertIsNotNone(register_path)
        self.assertIn("post", register_path)
        reg_post = register_path["post"]
        self.assertIn("201", reg_post["responses"])
        reg_201_schema = reg_post["responses"]["201"]["content"]["application/json"]["schema"]
        self.assertIn("$ref", reg_201_schema)
        self.assertTrue(reg_201_schema["$ref"].endswith("TPORegisterResponse"))

        # 2. TPO Login endpoint
        login_path = paths.get("/api/v1/tpo/auth/login/")
        self.assertIsNotNone(login_path)
        self.assertIn("post", login_path)
        login_post = login_path["post"]
        self.assertIn("200", login_post["responses"])
        login_200_schema = login_post["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertIn("$ref", login_200_schema)
        self.assertTrue(login_200_schema["$ref"].endswith("TPOLoginResponse"))

        # 3. TPO Report Export endpoint
        export_path = paths.get("/api/v1/tpo/reports/export/")
        self.assertIsNotNone(export_path)
        self.assertIn("post", export_path)
        export_post = export_path["post"]
        self.assertIn("200", export_post["responses"])
        export_200_content = export_post["responses"]["200"]["content"]
        self.assertIn("text/csv", export_200_content)
        self.assertIn("application/json", export_200_content)
        self.assertEqual(export_200_content["text/csv"]["schema"]["format"], "binary")
        self.assertEqual(export_200_content["application/json"]["schema"]["format"], "binary")
