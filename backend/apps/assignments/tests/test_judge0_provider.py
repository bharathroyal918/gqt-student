"""Unit and Mock Integration tests for Judge0ExecutionProvider."""

import json
from unittest.mock import MagicMock, patch
from django.test import TestCase

from apps.assignments.execution.judge0_provider import Judge0ExecutionProvider
from apps.assignments.models import CodeSubmission


class Judge0ExecutionProviderTests(TestCase):
    """Test suite validating Judge0 provider behavior and error handling."""

    def setUp(self):
        self.provider = Judge0ExecutionProvider(
            endpoint="https://ce.judge0.com",
            api_key="test-api-key",
            api_host="test-api-host",
            use_sdk=False,
        )

    def test_unsupported_language_returns_compilation_error(self):
        output = self.provider.execute(
            language="ruby",
            source_code="puts 'hello'",
            stdin="",
        )
        self.assertEqual(output.status, CodeSubmission.SubmissionStatus.COMPILATION_ERROR)
        self.assertIn("Unsupported language", output.stderr)

    def test_java_public_class_rewritten_to_main(self):
        """Judge0 compiles inside Main.java; public class Solution must be adapted to Main."""
        raw_code = (
            "import java.util.*;\n"
            "public class Solution {\n"
            "    public static void main(String[] args) {}\n"
            "}"
        )
        prepared = self.provider._prepare_source_code("java", raw_code)
        self.assertIn("public class Main", prepared)
        self.assertNotIn("public class Solution", prepared)

    def test_java_main_not_double_rewritten(self):
        raw_code = "public class Main { public static void main(String[] args) {} }"
        prepared = self.provider._prepare_source_code("java", raw_code)
        self.assertEqual(prepared, raw_code)

    @patch("httpx.Client.post")
    def test_successful_http_execution(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": {"id": 3, "description": "Accepted"},
            "stdout": "0 1\n",
            "stderr": None,
            "compile_output": None,
            "message": None,
            "time": "0.045",
            "memory": 15200,
            "exit_code": 0,
        }
        mock_post.return_value = mock_resp

        output = self.provider.execute(
            language="python",
            source_code="print('0 1')",
            stdin="",
            time_limit_seconds=2.0,
            memory_limit_mb=128,
            expected_output="0 1",
        )

        self.assertEqual(output.status, CodeSubmission.SubmissionStatus.ACCEPTED)
        self.assertEqual(output.stdout, "0 1\n")
        self.assertEqual(output.stderr, "")
        self.assertEqual(output.execution_time_seconds, 0.045)
        self.assertEqual(output.memory_kb, 15200)

        # Verify correct language ID for Python (109)
        call_kwargs = mock_post.call_args[1]
        self.assertEqual(call_kwargs["json"]["language_id"], 109)
        self.assertEqual(call_kwargs["json"]["cpu_time_limit"], 2.0)
        self.assertEqual(call_kwargs["json"]["memory_limit"], 128 * 1024)

    @patch("httpx.Client.post")
    def test_compilation_error_http_execution(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": {"id": 6, "description": "Compilation Error"},
            "stdout": None,
            "stderr": None,
            "compile_output": "main.cpp: In function 'int main()': syntax error on line 4",
            "message": None,
            "time": None,
            "memory": None,
            "exit_code": 1,
        }
        mock_post.return_value = mock_resp

        output = self.provider.execute(
            language="cpp",
            source_code="int main() { bad code }",
            stdin="",
        )

        self.assertEqual(output.status, CodeSubmission.SubmissionStatus.COMPILATION_ERROR)
        self.assertIn("syntax error", output.stderr)
        self.assertIn("syntax error", output.compilation_output)

    @patch("httpx.Client.post")
    def test_runtime_error_http_execution(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": {"id": 11, "description": "Runtime Error (NZEC)"},
            "stdout": None,
            "stderr": "ZeroDivisionError: division by zero",
            "compile_output": None,
            "message": None,
            "time": "0.012",
            "memory": 12000,
            "exit_code": 1,
        }
        mock_post.return_value = mock_resp

        output = self.provider.execute(
            language="python",
            source_code="print(1/0)",
            stdin="",
        )

        self.assertEqual(output.status, CodeSubmission.SubmissionStatus.RUNTIME_ERROR)
        self.assertIn("ZeroDivisionError", output.stderr)

    @patch("httpx.Client.post")
    def test_timeout_http_execution(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": {"id": 5, "description": "Time Limit Exceeded"},
            "stdout": None,
            "stderr": "Time limit exceeded",
            "compile_output": None,
            "message": None,
            "time": "2.100",
            "memory": 18000,
            "exit_code": 137,
        }
        mock_post.return_value = mock_resp

        output = self.provider.execute(
            language="python",
            source_code="while True: pass",
            stdin="",
        )

        self.assertEqual(output.status, CodeSubmission.SubmissionStatus.TIME_LIMIT_EXCEEDED)

    @patch("httpx.Client.post")
    def test_network_connection_failure_handled_gracefully(self, mock_post):
        mock_post.side_effect = Exception("Connection refused to judge0 server")

        output = self.provider.execute(
            language="python",
            source_code="print('test')",
            stdin="",
        )

        self.assertEqual(output.status, CodeSubmission.SubmissionStatus.RUNTIME_ERROR)
        self.assertIn("connection error", output.stderr)
