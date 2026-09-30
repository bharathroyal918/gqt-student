"""Vendor-agnostic interfaces for sandboxed code execution."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from apps.assignments.models import CodeSubmission, ExecutionResult


@dataclass
class ExecutionOutput:
    """Standardized output returned by any execution provider."""

    status: str  # CodeSubmission.SubmissionStatus
    stdout: str = ""
    stderr: str = ""
    execution_time_seconds: float = 0.0
    memory_kb: int = 0
    exit_code: Optional[int] = 0
    compilation_output: str = ""


class BaseExecutionProvider(ABC):
    """Abstract contract for sandboxed judge providers (e.g. Judge0, Piston, Isolated Docker, Mock)."""

    @abstractmethod
    def execute(
        self,
        language: str,
        source_code: str,
        stdin: str = "",
        time_limit_seconds: float = 2.0,
        memory_limit_mb: int = 128,
        expected_output: Optional[str] = None,
    ) -> ExecutionOutput:
        """Execute a single snippet of code against standard input."""
        pass
