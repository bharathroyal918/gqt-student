"""Core Domain Service for Sandboxed Code Execution and Assessment Grading."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.assignments.execution.interfaces import BaseExecutionProvider, ExecutionOutput
from apps.assignments.execution.mock_provider import MockExecutionProvider
from apps.assignments.models import (
    CodingQuestion,
    CodeSubmission,
    ExecutionResult,
    StudentQuestionProgress,
    TestCase,
)
from apps.common.exceptions import DomainException
from apps.scoring.models import ScoreRecord
from apps.students.models import StudentProfile


class CodeExecutionService:
    """Provider-agnostic service orchestrating student code execution, sandboxing, and assessment."""

    SUPPORTED_LANGUAGES = ["python", "java", "c", "cpp", "javascript"]
    MAX_SOURCE_CODE_BYTES = 65536  # 64 KB limit
    RATE_LIMIT_COOLDOWN_SECONDS = 3  # Minimum seconds between executions
    RATE_LIMIT_MAX_PER_MINUTE = 20  # Max executions per minute

    _provider: BaseExecutionProvider = MockExecutionProvider()

    @classmethod
    def set_provider(cls, provider: BaseExecutionProvider) -> None:
        """Dynamically inject an execution provider (e.g. for testing or production Judge0)."""
        cls._provider = provider

    @classmethod
    def get_provider(cls) -> BaseExecutionProvider:
        return cls._provider

    @classmethod
    def _validate_submission_request(
        cls,
        student_id: str,
        question: CodingQuestion,
        language: str,
        source_code: str,
    ) -> str:
        """Enforces security boundaries, size constraints, rate limiting, and language validation."""
        # 1. Source code size check
        if not source_code or not source_code.strip():
            raise DomainException("Source code cannot be empty.", code="EMPTY_SOURCE_CODE", status_code=400)

        byte_len = len(source_code.encode("utf-8"))
        if byte_len > cls.MAX_SOURCE_CODE_BYTES:
            raise DomainException(
                f"Source code exceeds maximum allowed size of 64KB ({byte_len} bytes submitted).",
                code="OVERSIZED_SOURCE_CODE",
                status_code=400,
            )

        # 2. Language validation
        norm_lang = language.strip().lower()
        if norm_lang not in cls.SUPPORTED_LANGUAGES:
            raise DomainException(
                f"Unsupported language '{language}'. Supported: {cls.SUPPORTED_LANGUAGES}",
                code="UNSUPPORTED_LANGUAGE",
                status_code=400,
            )

        if question.allowed_languages and norm_lang not in [l.lower() for l in question.allowed_languages]:
            raise DomainException(
                f"Language '{language}' is not permitted for this specific question.",
                code="LANGUAGE_NOT_ALLOWED_FOR_QUESTION",
                status_code=400,
            )

        # 3. Rate limiting & flood prevention
        cooldown_key = f"code_exec_cooldown:{student_id}"
        if cache.get(cooldown_key):
            raise DomainException(
                "Please wait a few seconds before executing or submitting code again.",
                code="RATE_LIMIT_COOLDOWN",
                status_code=429,
            )
        cache.set(cooldown_key, True, timeout=cls.RATE_LIMIT_COOLDOWN_SECONDS)

        rate_limit_key = f"code_exec_rate:{student_id}"
        current_count = cache.get(rate_limit_key, 0)
        if current_count >= cls.RATE_LIMIT_MAX_PER_MINUTE:
            raise DomainException(
                "Too many code execution requests. Please wait a minute before trying again.",
                code="RATE_LIMIT_EXCEEDED",
                status_code=429,
            )
        cache.set(rate_limit_key, current_count + 1, timeout=60)

        return norm_lang

    @classmethod
    def run_code(
        cls,
        student_profile: StudentProfile,
        question_id: str,
        language: str,
        source_code: str,
        custom_input: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Runs student code against visible sample test cases or custom input without grading."""
        question = get_object_or_404(CodingQuestion, id=question_id, is_active=True)
        norm_lang = cls._validate_submission_request(
            str(student_profile.id), question, language, source_code
        )

        time_limit = float(question.time_limit_seconds)
        memory_limit = int(question.memory_limit_mb)
        provider = cls.get_provider()

        # Mode A: Custom input execution
        if custom_input is not None:
            output = provider.execute(
                language=norm_lang,
                source_code=source_code,
                stdin=custom_input,
                time_limit_seconds=time_limit,
                memory_limit_mb=memory_limit,
            )
            return {
                "mode": "CUSTOM_INPUT",
                "status": output.status,
                "stdout": output.stdout,
                "stderr": output.stderr,
                "execution_time_ms": int(output.execution_time_seconds * 1000),
                "peak_memory_kb": output.memory_kb,
                "exit_code": output.exit_code,
            }

        # Mode B: Visible sample test cases execution
        visible_testcases = list(
            question.test_cases.filter(is_visible=True).order_by("order")
        )
        if not visible_testcases:
            # Create a default sample run if no test cases exist
            output = provider.execute(
                language=norm_lang,
                source_code=source_code,
                stdin="",
                time_limit_seconds=time_limit,
                memory_limit_mb=memory_limit,
            )
            return {
                "mode": "SAMPLE_TEST_CASES",
                "overall_status": output.status,
                "test_results": [
                    {
                        "order": 1,
                        "input_data": "",
                        "expected_output": "",
                        "actual_output": output.stdout,
                        "status": output.status,
                        "stderr": output.stderr,
                        "execution_time_ms": int(output.execution_time_seconds * 1000),
                        "memory_kb": output.memory_kb,
                    }
                ],
            }

        test_results = []
        overall_status = CodeSubmission.SubmissionStatus.ACCEPTED

        for idx, tc in enumerate(visible_testcases):
            output = provider.execute(
                language=norm_lang,
                source_code=source_code,
                stdin=tc.input_data,
                time_limit_seconds=time_limit,
                memory_limit_mb=memory_limit,
                expected_output=tc.expected_output,
            )

            tc_status = output.status
            if tc_status == CodeSubmission.SubmissionStatus.ACCEPTED:
                # Check actual stdout against expected
                if output.stdout.strip() != tc.expected_output.strip():
                    tc_status = CodeSubmission.SubmissionStatus.WRONG_ANSWER

            if tc_status != CodeSubmission.SubmissionStatus.ACCEPTED and overall_status == CodeSubmission.SubmissionStatus.ACCEPTED:
                overall_status = tc_status

            test_results.append(
                {
                    "order": tc.order or (idx + 1),
                    "input_data": tc.input_data,
                    "expected_output": tc.expected_output,
                    "actual_output": output.stdout,
                    "status": tc_status,
                    "stderr": output.stderr,
                    "execution_time_ms": int(output.execution_time_seconds * 1000),
                    "memory_kb": output.memory_kb,
                }
            )

        return {
            "mode": "SAMPLE_TEST_CASES",
            "overall_status": overall_status,
            "test_results": test_results,
        }

    @classmethod
    @transaction.atomic
    def submit_code(
        cls,
        student_profile: StudentProfile,
        question_id: str,
        language: str,
        source_code: str,
    ) -> Dict[str, Any]:
        """Atomically evaluates student solution against ALL visible & hidden test cases, records progress, and awards scores."""
        question = get_object_or_404(
            CodingQuestion.objects.select_related("module"), id=question_id, is_active=True
        )
        norm_lang = cls._validate_submission_request(
            str(student_profile.id), question, language, source_code
        )

        all_testcases = list(question.test_cases.all().order_by("order"))
        if not all_testcases:
            raise DomainException(
                "Cannot submit solution: No test cases are configured for this question.",
                code="NO_TEST_CASES",
                status_code=400,
            )

        # Initialize pending submission row
        submission = CodeSubmission.objects.create(
            student=student_profile,
            question=question,
            language=norm_lang,
            source_code=source_code,
            status=CodeSubmission.SubmissionStatus.RUNNING,
            total_test_cases=len(all_testcases),
        )

        provider = cls.get_provider()
        time_limit = float(question.time_limit_seconds)
        memory_limit = int(question.memory_limit_mb)

        passed_count = 0
        total_time_ms = 0
        peak_memory_kb = 0
        overall_status = CodeSubmission.SubmissionStatus.ACCEPTED
        sanitized_results = []
        execution_results_to_create = []

        for idx, tc in enumerate(all_testcases):
            output = provider.execute(
                language=norm_lang,
                source_code=source_code,
                stdin=tc.input_data,
                time_limit_seconds=time_limit,
                memory_limit_mb=memory_limit,
                expected_output=tc.expected_output,
            )

            tc_exec_time_ms = int(output.execution_time_seconds * 1000)
            total_time_ms += tc_exec_time_ms
            peak_memory_kb = max(peak_memory_kb, output.memory_kb)

            # Determine test case result status
            if output.status != CodeSubmission.SubmissionStatus.ACCEPTED:
                result_status = output.status
            elif output.stdout.strip() == tc.expected_output.strip():
                result_status = ExecutionResult.ResultStatus.PASSED
                passed_count += 1
            else:
                result_status = ExecutionResult.ResultStatus.FAILED

            if result_status != ExecutionResult.ResultStatus.PASSED and overall_status == CodeSubmission.SubmissionStatus.ACCEPTED:
                if result_status == ExecutionResult.ResultStatus.FAILED:
                    overall_status = CodeSubmission.SubmissionStatus.WRONG_ANSWER
                else:
                    overall_status = result_status

            # Map to ExecutionResult model status
            er_status = (
                ExecutionResult.ResultStatus.PASSED
                if result_status == ExecutionResult.ResultStatus.PASSED
                else ExecutionResult.ResultStatus.FAILED
                if result_status == CodeSubmission.SubmissionStatus.WRONG_ANSWER
                else result_status
            )

            execution_results_to_create.append(
                ExecutionResult(
                    submission=submission,
                    test_case=tc,
                    status=er_status,
                    stdout=output.stdout,
                    stderr=output.stderr,
                    execution_time_seconds=Decimal(str(round(output.execution_time_seconds, 4))),
                    memory_kb=output.memory_kb,
                    exit_code=output.exit_code,
                )
            )

            # Sanitized output for student frontend (CRITICAL: Do NOT expose hidden test cases!)
            if tc.is_visible:
                sanitized_results.append(
                    {
                        "order": tc.order or (idx + 1),
                        "is_visible": True,
                        "status": "PASSED" if result_status == ExecutionResult.ResultStatus.PASSED else "FAILED",
                        "input_data": tc.input_data,
                        "expected_output": tc.expected_output,
                        "actual_output": output.stdout,
                        "stderr": output.stderr,
                        "execution_time_ms": tc_exec_time_ms,
                        "memory_kb": output.memory_kb,
                    }
                )
            else:
                sanitized_results.append(
                    {
                        "order": tc.order or (idx + 1),
                        "is_visible": False,
                        "status": "PASSED" if result_status == ExecutionResult.ResultStatus.PASSED else "FAILED",
                        "execution_time_ms": tc_exec_time_ms,
                        # No input_data, expected_output, stdout, or stderr exposed
                    }
                )

        # Bulk create execution results
        ExecutionResult.objects.bulk_create(execution_results_to_create)

        # Delegate score calculation, event emission, points persistence, and leaderboard update to Centralized ScoringService
        from apps.scoring.services import ScoringService

        total_tc = len(all_testcases)
        is_all_passed = passed_count == total_tc

        score_eval = ScoringService.evaluate_assignment_submission(
            student=student_profile,
            question_id=str(question.id),
            question_title=question.title,
            passed_test_cases=passed_count,
            total_test_cases=total_tc,
            max_points=question.points,
        )
        score_awarded = Decimal(str(score_eval["points"]))
        scoring_policy = score_eval["policy_applied"]

        if is_all_passed:
            submission_status = CodeSubmission.SubmissionStatus.ACCEPTED
        else:
            submission_status = overall_status if overall_status != CodeSubmission.SubmissionStatus.ACCEPTED else CodeSubmission.SubmissionStatus.WRONG_ANSWER

        avg_time_ms = int(total_time_ms / total_tc) if total_tc > 0 else 0

        submission.status = submission_status
        submission.passed_test_cases = passed_count
        submission.total_test_cases = total_tc
        submission.execution_time_ms = avg_time_ms
        submission.peak_memory_kb = peak_memory_kb
        submission.score_awarded = score_awarded
        submission.scoring_policy = scoring_policy
        submission.save()

        # Update StudentQuestionProgress
        prog, _ = StudentQuestionProgress.objects.select_for_update().get_or_create(
            student=student_profile,
            question=question,
            defaults={"best_score": Decimal("0.00"), "attempts_count": 0},
        )
        prog.attempts_count += 1
        if score_awarded >= prog.best_score:
            prog.best_score = score_awarded
            prog.best_submission = submission

        if is_all_passed and not prog.is_solved:
            prog.is_solved = True
            prog.first_solved_at = timezone.now()

        prog.save()

        return {
            "submission_id": str(submission.id),
            "status": submission.status,
            "passed_test_cases": passed_count,
            "total_test_cases": total_tc,
            "score_awarded": float(score_awarded),
            "max_points": float(question.points),
            "execution_time_ms": avg_time_ms,
            "peak_memory_kb": peak_memory_kb,
            "is_solved": prog.is_solved,
            "best_score": float(prog.best_score),
            "submitted_at": submission.submitted_at.isoformat(),
            "results": sanitized_results,
        }

    @classmethod
    def get_execution_result(cls, submission_id: str, student_profile: StudentProfile) -> Dict[str, Any]:
        """Retrieves a past submission's sanitized execution results."""
        submission = get_object_or_404(
            CodeSubmission.objects.select_related("question"),
            id=submission_id,
            student=student_profile,
        )

        results = []
        for er in submission.execution_results.select_related("test_case").order_by("test_case__order"):
            tc = er.test_case
            if tc.is_visible:
                results.append(
                    {
                        "order": tc.order,
                        "is_visible": True,
                        "status": er.status,
                        "input_data": tc.input_data,
                        "expected_output": tc.expected_output,
                        "actual_output": er.stdout,
                        "stderr": er.stderr,
                        "execution_time_ms": int((er.execution_time_seconds or 0) * 1000),
                        "memory_kb": er.memory_kb,
                    }
                )
            else:
                results.append(
                    {
                        "order": tc.order,
                        "is_visible": False,
                        "status": er.status,
                        "execution_time_ms": int((er.execution_time_seconds or 0) * 1000),
                    }
                )

        return {
            "submission_id": str(submission.id),
            "question_id": str(submission.question.id),
            "question_title": submission.question.title,
            "language": submission.language,
            "status": submission.status,
            "passed_test_cases": submission.passed_test_cases,
            "total_test_cases": submission.total_test_cases,
            "score_awarded": float(submission.score_awarded),
            "execution_time_ms": submission.execution_time_ms,
            "peak_memory_kb": submission.peak_memory_kb,
            "submitted_at": submission.submitted_at.isoformat(),
            "results": results,
        }
