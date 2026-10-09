"""Deterministic, sandboxed Mock Execution Provider for tests and offline evaluation."""

from typing import ClassVar

from apps.assignments.execution.interfaces import BaseExecutionProvider, ExecutionOutput
from apps.assignments.models import CodeSubmission


class MockExecutionProvider(BaseExecutionProvider):
    """Safe, mock execution provider that guarantees zero untrusted execution on the host Django process."""

    SUPPORTED_LANGUAGES: ClassVar[set[str]] = {
        "python",
        "java",
        "c",
        "cpp",
        "javascript",
    }

    def execute(
        self,
        language: str,
        source_code: str,
        stdin: str = "",
        time_limit_seconds: float = 2.0,
        memory_limit_mb: int = 128,
        expected_output: str | None = None,
    ) -> ExecutionOutput:
        lang = language.strip().lower()
        if lang not in self.SUPPORTED_LANGUAGES:
            return ExecutionOutput(
                status=CodeSubmission.SubmissionStatus.COMPILATION_ERROR,
                stderr=f"Unsupported language '{language}'. Supported: {sorted(self.SUPPORTED_LANGUAGES)}",
                exit_code=1,
            )

        code_upper = source_code.upper()

        # Simulated Compilation Error
        if "ERROR: COMPILE" in code_upper or "SYNTAX_ERROR" in code_upper:
            return ExecutionOutput(
                status=CodeSubmission.SubmissionStatus.COMPILATION_ERROR,
                stderr=f"SyntaxError: invalid syntax on line 1 in {language} source.",
                compilation_output="Compilation failed with exit code 1",
                exit_code=1,
            )

        # Simulated Runtime Error
        if (
            "ERROR: RUNTIME" in code_upper
            or "EXCEPTION" in code_upper
            or "DIVISION_BY_ZERO" in code_upper
        ):
            return ExecutionOutput(
                status=CodeSubmission.SubmissionStatus.RUNTIME_ERROR,
                stderr="ZeroDivisionError: integer division or modulo by zero\n  File 'solution', line 4",
                execution_time_seconds=0.012,
                memory_kb=12400,
                exit_code=1,
            )

        # Simulated Timeout (Time Limit Exceeded)
        if (
            "ERROR: TIMEOUT" in code_upper
            or "INFINITE_LOOP" in code_upper
            or "WHILE TRUE" in code_upper
        ):
            return ExecutionOutput(
                status=CodeSubmission.SubmissionStatus.TIME_LIMIT_EXCEEDED,
                stderr=f"Time limit exceeded ({time_limit_seconds}s limit)",
                execution_time_seconds=time_limit_seconds + 0.1,
                memory_kb=18600,
                exit_code=137,
            )

        # Simulated Memory Exceeded
        if "ERROR: MEMORY" in code_upper or "OUT_OF_MEMORY" in code_upper:
            return ExecutionOutput(
                status=CodeSubmission.SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
                stderr=f"Memory limit exceeded (exceeded {memory_limit_mb}MB limit)",
                execution_time_seconds=0.150,
                memory_kb=(memory_limit_mb * 1024) + 5000,
                exit_code=137,
            )

        # Simulated Wrong Answer
        if "ERROR: WRONG" in code_upper or "WRONG_ANSWER" in code_upper:
            return ExecutionOutput(
                status=CodeSubmission.SubmissionStatus.WRONG_ANSWER,
                stdout="[-1, -1]",
                execution_time_seconds=0.025,
                memory_kb=14200,
                exit_code=0,
            )

        # Simulated Partial Failure for specific test input
        if (
            "FAIL_ON_EVEN" in code_upper
            and stdin.strip().isdigit()
            and int(stdin.strip()) % 2 == 0
        ):
            return ExecutionOutput(
                status=CodeSubmission.SubmissionStatus.WRONG_ANSWER,
                stdout="False",
                execution_time_seconds=0.018,
                memory_kb=13100,
                exit_code=0,
            )

        # Default deterministic successful mock execution output
        if expected_output is not None:
            simulated_stdout = expected_output
        else:
            clean_stdin = stdin.strip()
            simulated_stdout = clean_stdin if clean_stdin else "Success Output"

        return ExecutionOutput(
            status=CodeSubmission.SubmissionStatus.ACCEPTED,
            stdout=simulated_stdout,
            stderr="",
            execution_time_seconds=0.035,
            memory_kb=15600,
            exit_code=0,
        )
