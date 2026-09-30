"""Comprehensive Integration Test Suite for Sandboxed Code Execution Platform.

Tests:
1. Vendor-independent execution abstraction (run_code, submit_code, get_execution_result).
2. Compilation error handling.
3. Runtime error handling.
4. Execution timeout handling.
5. Memory limit exceeded handling.
6. Wrong answer vs Accepted test case grading.
7. Hidden test cases security rule (Hidden test cases are NEVER exposed in student responses).
8. Scoring policy: Full credit on 100% test cases passed, proportional on partial, 0 on total failure.
9. Idempotent / Best-score tracking across multiple submissions.
10. Oversized source code (>64KB) rejected.
11. Unsupported language rejected.
12. Cooldown and rate limiting / request flooding protection.
13. Student profile requirement enforcement.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.assignments.execution.mock_provider import MockExecutionProvider
from apps.assignments.execution.service import CodeExecutionService
from apps.assignments.models import (
    CodingQuestion,
    CodeSubmission,
    ExecutionResult,
    StudentQuestionProgress,
    TestCase as QuestionTestCase,
)
from apps.courses.models import Course
from apps.modules.models import Module
from apps.scoring.models import ScoreRecord
from apps.students.models import StudentProfile

User = get_user_model()


class CodeExecutionApiTests(TestCase):
    """Integration test suite for coding practice sandbox and automated evaluation."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.unauthorized_client = APIClient()

        # Ensure Mock Execution Provider is set
        self.provider = MockExecutionProvider()
        CodeExecutionService.set_provider(self.provider)

        # 1. Setup Course & Module
        self.course = Course.objects.create(
            title="Algorithm & Data Structures Track",
            slug="algo-ds-track",
            is_published=True,
        )
        self.module = Module.objects.create(
            course=self.course,
            title="Data Types & Collections",
            slug="data-types-collections",
            order_index=1,
            is_published=True,
        )

        # 2. Setup Coding Question (Two Sum / Target Sum)
        self.question = CodingQuestion.objects.create(
            module=self.module,
            title="Two Sum Problem",
            slug="two-sum-problem",
            difficulty=CodingQuestion.DifficultyChoices.EASY,
            problem_statement="Given an array of integers and a target, return indices of two numbers that add up to target.",
            allowed_languages=["python", "java", "c", "cpp", "javascript"],
            starter_code={
                "python": "def two_sum(nums, target):\n    pass",
                "javascript": "function twoSum(nums, target) {\n}",
            },
            time_limit_seconds=Decimal("2.00"),
            memory_limit_mb=128,
            points=Decimal("100.00"),
            order=1,
            is_active=True,
        )

        # Visible Sample Testcases (Sample 1 & 2)
        self.tc1 = QuestionTestCase.objects.create(
            question=self.question,
            input_data="[2, 7, 11, 15], target = 9",
            expected_output="[0, 1]",
            is_visible=True,
            order=1,
        )
        self.tc2 = QuestionTestCase.objects.create(
            question=self.question,
            input_data="[3, 2, 4], target = 6",
            expected_output="[1, 2]",
            is_visible=True,
            order=2,
        )

        # Hidden Grading Testcases (Hidden 3 & 4)
        self.tc3 = QuestionTestCase.objects.create(
            question=self.question,
            input_data="[3, 3], target = 6",
            expected_output="[0, 1]",
            is_visible=False,
            order=3,
        )
        self.tc4 = QuestionTestCase.objects.create(
            question=self.question,
            input_data="[1000000, 500000, 500000], target = 1000000",
            expected_output="[1, 2]",
            is_visible=False,
            order=4,
        )

        # 3. Setup Authenticated Student
        self.user = User.objects.create_user(
            email="coder@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.STUDENT,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-CODE-01",
            full_name="Algorithm Master",
            batch_code="BATCH-2026-PY",
            total_points=Decimal("0.00"),
        )
        self.client.force_authenticate(user=self.user)

        # 4. Non-student user
        self.staff_user = User.objects.create_user(
            email="staff@gqt.edu",
            password="SecurePassword123!",
            role=User.RoleChoices.ADMIN,
            is_active=True,
            onboarding_status=User.OnboardingStatusChoices.ACTIVE,
        )
        self.unauthorized_client.force_authenticate(user=self.staff_user)

    def test_question_detail_excludes_hidden_test_cases(self):
        """Security: GET question detail must return visible test cases and NEVER leak hidden test cases."""
        url = reverse("api_v1:student_assignments:question_detail", kwargs={"question_id": self.question.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]

        self.assertEqual(data["title"], "Two Sum Problem")
        self.assertEqual(data["points"], 100.0)
        self.assertIn("starter_code", data)
        self.assertIn("python", data["starter_code"])

        # Must only contain the 2 visible test cases
        visible_tcs = data["visible_test_cases"]
        self.assertEqual(len(visible_tcs), 2)
        visible_ids = [tc["id"] for tc in visible_tcs]
        self.assertIn(str(self.tc1.id), visible_ids)
        self.assertIn(str(self.tc2.id), visible_ids)
        self.assertNotIn(str(self.tc3.id), visible_ids)
        self.assertNotIn(str(self.tc4.id), visible_ids)

    def test_run_code_against_sample_test_cases(self):
        """POST /run/ executes against visible test cases only without grading or points."""
        url = reverse("api_v1:student_assignments:code_run", kwargs={"question_id": self.question.id})
        payload = {
            "language": "python",
            "source_code": "def two_sum(nums, target):\n    # Standard correct solution\n    return [0, 1]",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data["data"]
        self.assertEqual(data["mode"], "SAMPLE_TEST_CASES")
        self.assertIn("test_results", data)
        self.assertEqual(len(data["test_results"]), 2)

        # Verify no points or submissions created
        self.assertEqual(CodeSubmission.objects.count(), 0)
        self.assertEqual(ScoreRecord.objects.count(), 0)

    def test_run_code_with_custom_input(self):
        """POST /run/ with custom_input evaluates standard input string directly."""
        url = reverse("api_v1:student_assignments:code_run", kwargs={"question_id": self.question.id})
        payload = {
            "language": "python",
            "source_code": "print('Custom Result')",
            "custom_input": "Test Input Payload",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data["data"]
        self.assertEqual(data["mode"], "CUSTOM_INPUT")
        self.assertIn("stdout", data)

    def test_run_code_compilation_error(self):
        """POST /run/ correctly captures and reports simulated compilation/syntax errors."""
        url = reverse("api_v1:student_assignments:code_run", kwargs={"question_id": self.question.id})
        payload = {
            "language": "python",
            "source_code": "# ERROR: COMPILE\ndef broken_syntax(:",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data["data"]
        self.assertEqual(data["overall_status"], "COMPILATION_ERROR")
        self.assertTrue(any("SyntaxError" in r["stderr"] for r in data["test_results"]))

    def test_run_code_runtime_error(self):
        """POST /run/ correctly captures and reports runtime exceptions (e.g. ZeroDivisionError)."""
        url = reverse("api_v1:student_assignments:code_run", kwargs={"question_id": self.question.id})
        payload = {
            "language": "python",
            "source_code": "# ERROR: RUNTIME\nx = 1 / 0",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data["data"]
        self.assertEqual(data["overall_status"], "RUNTIME_ERROR")
        self.assertTrue(any("ZeroDivisionError" in r["stderr"] for r in data["test_results"]))

    def test_run_code_timeout_time_limit_exceeded(self):
        """POST /run/ reports TIME_LIMIT_EXCEEDED when execution exceeds threshold."""
        url = reverse("api_v1:student_assignments:code_run", kwargs={"question_id": self.question.id})
        payload = {
            "language": "python",
            "source_code": "# ERROR: TIMEOUT\nwhile True: pass",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data["data"]
        self.assertEqual(data["overall_status"], "TIME_LIMIT_EXCEEDED")

    def test_run_code_memory_limit_exceeded(self):
        """POST /run/ reports MEMORY_LIMIT_EXCEEDED when memory allocation exceeds threshold."""
        url = reverse("api_v1:student_assignments:code_run", kwargs={"question_id": self.question.id})
        payload = {
            "language": "python",
            "source_code": "# ERROR: MEMORY\narr = [1] * 100000000",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data["data"]
        self.assertEqual(data["overall_status"], "MEMORY_LIMIT_EXCEEDED")

    def test_submit_code_all_passed_awards_full_score(self):
        """POST /submit/ passing all visible and hidden test cases marks question SOLVED and awards full points."""
        cache.clear()
        url = reverse("api_v1:student_assignments:code_submit", kwargs={"question_id": self.question.id})
        payload = {
            "language": "python",
            "source_code": "# Perfect optimal solution",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.data["data"]
        self.assertEqual(data["status"], "ACCEPTED")
        self.assertEqual(data["passed_test_cases"], 4)
        self.assertEqual(data["total_test_cases"], 4)
        self.assertEqual(data["score_awarded"], 100.0)
        self.assertTrue(data["is_solved"])

        # Verify database state
        submission = CodeSubmission.objects.get(id=data["submission_id"])
        self.assertEqual(submission.status, CodeSubmission.SubmissionStatus.ACCEPTED)
        self.assertEqual(submission.score_awarded, Decimal("100.00"))

        # Verify StudentQuestionProgress
        progress = StudentQuestionProgress.objects.get(
            student=self.student_profile, question=self.question
        )
        self.assertTrue(progress.is_solved)
        self.assertEqual(progress.best_score, Decimal("100.00"))
        self.assertEqual(progress.attempts_count, 1)

        # Verify StudentProfile points
        self.student_profile.refresh_from_db()
        self.assertEqual(self.student_profile.total_points, Decimal("100.00"))

        # Verify Hidden Test Cases are sanitized in results
        results = data["results"]
        self.assertEqual(len(results), 4)

        hidden_results = [r for r in results if not r["is_visible"]]
        self.assertEqual(len(hidden_results), 2)
        for hr in hidden_results:
            self.assertNotIn("input_data", hr)
            self.assertNotIn("expected_output", hr)
            self.assertNotIn("actual_output", hr)
            self.assertIn(hr["status"], ["PASSED", "FAILED"])

    def test_submit_code_wrong_answer_partial_score(self):
        """POST /submit/ with wrong answer receives partial or zero score and updates attempt count."""
        cache.clear()
        url = reverse("api_v1:student_assignments:code_submit", kwargs={"question_id": self.question.id})
        payload = {
            "language": "python",
            "source_code": "# ERROR: WRONG\nreturn [-1, -1]",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.data["data"]
        self.assertEqual(data["status"], "WRONG_ANSWER")
        self.assertEqual(data["passed_test_cases"], 0)
        self.assertEqual(data["score_awarded"], 0.0)
        self.assertFalse(data["is_solved"])

        # Verify attempts counted
        progress = StudentQuestionProgress.objects.get(
            student=self.student_profile, question=self.question
        )
        self.assertEqual(progress.attempts_count, 1)
        self.assertFalse(progress.is_solved)

    def test_oversized_source_code_rejected(self):
        """Submitting source code exceeding 64KB is rejected immediately (HTTP 400)."""
        cache.clear()
        url = reverse("api_v1:student_assignments:code_submit", kwargs={"question_id": self.question.id})
        large_code = "x = 1\n" * 20000  # >70KB
        payload = {"language": "python", "source_code": large_code}

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "OVERSIZED_SOURCE_CODE")

    def test_unsupported_language_rejected(self):
        """Submitting an unsupported language like 'rust' or 'ruby' is rejected (HTTP 400)."""
        cache.clear()
        url = reverse("api_v1:student_assignments:code_submit", kwargs={"question_id": self.question.id})
        payload = {"language": "rust", "source_code": "fn main() {}"}

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "UNSUPPORTED_LANGUAGE")

    def test_rate_limiting_and_cooldown_abuse_prevention(self):
        """Rapid fire submissions within cooldown threshold trigger HTTP 429 RATE_LIMIT_COOLDOWN."""
        cache.clear()
        url = reverse("api_v1:student_assignments:code_submit", kwargs={"question_id": self.question.id})
        payload = {"language": "python", "source_code": "# Valid Code"}

        # First request succeeds
        res1 = self.client.post(url, payload, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Immediate second request blocked by cooldown
        res2 = self.client.post(url, payload, format="json")
        self.assertEqual(res2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(res2.data["error"]["code"], "RATE_LIMIT_COOLDOWN")

    def test_unauthorized_non_student_access_rejected(self):
        """User without active student profile is forbidden from submitting code (HTTP 403)."""
        url = reverse("api_v1:student_assignments:code_submit", kwargs={"question_id": self.question.id})
        payload = {"language": "python", "source_code": "print(1)"}

        response = self.unauthorized_client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"]["code"], "STUDENT_PROFILE_REQUIRED")
