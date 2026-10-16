"""Production-grade sandboxed code execution provider powered by Judge0 Open Source Engine.

Supports both direct HTTP JSON API (primary, high-performance, resilient) and
Python SDK (judge0 client), with language mapping, Java entrypoint normalization,
and granular status/error mapping.
"""

import logging
import re
from typing import Any, ClassVar

from django.conf import settings

from apps.assignments.execution.interfaces import BaseExecutionProvider, ExecutionOutput
from apps.assignments.models import CodeSubmission

logger = logging.getLogger(__name__)


class Judge0ExecutionProvider(BaseExecutionProvider):
    """Judge0 sandboxed execution provider using Judge0 CE / self-hosted / RapidAPI."""

    # Default Judge0 CE Language IDs (queried and verified on https://ce.judge0.com/languages)
    LANGUAGE_IDS: ClassVar[dict[str, int]] = {
        "python": 109,      # Python (3.13.2) [also compatible with 92: Python 3.11, 71: Python 3.8]
        "javascript": 102,  # JavaScript (Node.js 22.08.0) [also compatible with 97: Node 20, 93: Node 18]
        "java": 91,         # Java (JDK 17.0.6)
        "cpp": 105,         # C++ (GCC 14.1.0)
        "c": 103,           # C (GCC 14.1.0)
    }

    NORMALIZE_LANG_MAP: ClassVar[dict[str, str]] = {
        "python": "python",
        "py": "python",
        "python3": "python",
        "javascript": "javascript",
        "js": "javascript",
        "node": "javascript",
        "nodejs": "javascript",
        "java": "java",
        "cpp": "cpp",
        "c++": "cpp",
        "c": "c",
    }

    # Status ID mappings from Judge0 documentation
    STATUS_MAP: ClassVar[dict[int, str]] = {
        1: CodeSubmission.SubmissionStatus.PENDING,
        2: CodeSubmission.SubmissionStatus.RUNNING,
        3: CodeSubmission.SubmissionStatus.ACCEPTED,
        4: CodeSubmission.SubmissionStatus.WRONG_ANSWER,
        5: CodeSubmission.SubmissionStatus.TIME_LIMIT_EXCEEDED,
        6: CodeSubmission.SubmissionStatus.COMPILATION_ERROR,
        7: CodeSubmission.SubmissionStatus.RUNTIME_ERROR,   # SIGSEGV
        8: CodeSubmission.SubmissionStatus.RUNTIME_ERROR,   # SIGXFSZ
        9: CodeSubmission.SubmissionStatus.RUNTIME_ERROR,   # SIGFPE
        10: CodeSubmission.SubmissionStatus.RUNTIME_ERROR,  # SIGABRT
        11: CodeSubmission.SubmissionStatus.RUNTIME_ERROR,  # NZEC
        12: CodeSubmission.SubmissionStatus.RUNTIME_ERROR,  # Other
        13: CodeSubmission.SubmissionStatus.RUNTIME_ERROR,  # Internal Error
        14: CodeSubmission.SubmissionStatus.RUNTIME_ERROR,  # Exec Format Error
    }

    def __init__(
        self,
        endpoint: str | None = None,
        api_key: str | None = None,
        api_host: str | None = None,
        use_sdk: bool | None = None,
    ):
        self.endpoint = (
            endpoint
            or getattr(settings, "JUDGE0_ENDPOINT", "https://ce.judge0.com")
        ).rstrip("/")
        self.api_key = api_key or getattr(settings, "JUDGE0_API_KEY", "")
        self.api_host = api_host or getattr(settings, "JUDGE0_API_HOST", "")
        self.use_sdk = (
            use_sdk
            if use_sdk is not None
            else getattr(settings, "JUDGE0_USE_SDK", False)
        )

        self._http_client = None

    def _get_http_client(self):
        if self._http_client is None:
            import httpx

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "GQT-Student-Portal/1.0 (Judge0-Engine)",
            }
            if self.api_key:
                headers["X-Auth-Token"] = self.api_key
                headers["X-RapidAPI-Key"] = self.api_key
            if self.api_host:
                headers["X-RapidAPI-Host"] = self.api_host

            # Connect timeout 5s, read timeout 25s for compiling & executing student solutions
            self._http_client = httpx.Client(
                headers=headers,
                timeout=httpx.Timeout(connect=5.0, read=25.0, write=10.0, pool=10.0),
            )
        return self._http_client

    def _prepare_source_code(self, norm_lang: str, source_code: str) -> str:
        """Sanitizes source code and adapts language-specific entry points (e.g. Java class name)."""
        clean_code = source_code
        if norm_lang == "java":
            # Judge0 compiles Java inside 'Main.java'. If the student defines 'public class Solution'
            # or any class name other than Main, rewrite to 'public class Main' to prevent javac filename error.
            clean_code = re.sub(
                r"\bpublic\s+class\s+(?!Main\b)\w+", "public class Main", clean_code
            )
        return clean_code

    def _execute_via_sdk(
        self,
        norm_lang: str,
        source_code: str,
        stdin: str,
        time_limit_seconds: float,
        memory_limit_mb: int,
    ) -> ExecutionOutput | None:
        """Executes code via the official judge0 Python SDK."""
        try:
            import judge0

            judge0.suppress_preview_warning = True

            sdk_lang_map = {
                "python": judge0.PYTHON,
                "javascript": judge0.JAVASCRIPT,
                "java": judge0.JAVA,
                "cpp": judge0.CPP,
                "c": judge0.C,
            }
            target_lang = sdk_lang_map.get(norm_lang)
            if not target_lang:
                return None

            cpu_limit = max(0.5, float(time_limit_seconds))
            mem_limit_kb = max(16384, int(memory_limit_mb) * 1024)

            res = judge0.run(
                source_code=source_code,
                stdin=stdin or "",
                language=target_lang,
                cpu_time_limit=cpu_limit,
                memory_limit=mem_limit_kb,
            )

            status_val = getattr(res.status, "value", 3)
            status_str = self.STATUS_MAP.get(
                status_val, CodeSubmission.SubmissionStatus.RUNTIME_ERROR
            )

            stdout = res.stdout or ""
            stderr = res.stderr or ""
            compile_output = res.compile_output or ""
            message = getattr(res, "message", None) or ""

            if not stderr and compile_output:
                stderr = compile_output
            if not stderr and message:
                stderr = message

            exec_time = float(res.time or 0.0)
            mem_kb = int(res.memory or 0)
            exit_code = res.exit_code

            return ExecutionOutput(
                status=status_str,
                stdout=stdout,
                stderr=stderr,
                execution_time_seconds=exec_time,
                memory_kb=mem_kb,
                exit_code=exit_code,
                compilation_output=compile_output,
            )
        except Exception as exc:
            logger.warning(
                "Judge0 Python SDK execution failed, falling back to HTTP JSON API: %s",
                exc,
            )
            return None

    def _execute_via_http(
        self,
        norm_lang: str,
        source_code: str,
        stdin: str,
        time_limit_seconds: float,
        memory_limit_mb: int,
        expected_output: str | None = None,
    ) -> ExecutionOutput:
        """Executes code directly via Judge0 HTTP JSON API (submissions?wait=true)."""
        lang_id = self.LANGUAGE_IDS.get(norm_lang)
        if not lang_id:
            return ExecutionOutput(
                status=CodeSubmission.SubmissionStatus.COMPILATION_ERROR,
                stderr=f"No Judge0 language ID configured for language '{norm_lang}'.",
                exit_code=1,
            )

        client = self._get_http_client()
        url = f"{self.endpoint}/submissions?wait=true"

        payload: dict[str, Any] = {
            "language_id": lang_id,
            "source_code": source_code,
            "stdin": stdin or "",
            "cpu_time_limit": max(0.5, float(time_limit_seconds)),
            "memory_limit": max(16384, int(memory_limit_mb) * 1024),
        }
        if expected_output is not None:
            payload["expected_output"] = expected_output

        try:
            resp = client.post(url, json=payload)
            if resp.status_code not in (200, 201):
                err_msg = f"Judge0 API returned HTTP {resp.status_code}: {resp.text[:250]}"
                logger.error("Judge0 API error: %s", err_msg)
                return ExecutionOutput(
                    status=CodeSubmission.SubmissionStatus.RUNTIME_ERROR,
                    stderr=err_msg,
                    exit_code=1,
                )

            data = resp.json()
            status_obj = data.get("status") or {}
            status_id = status_obj.get("id", 0)

            status_str = self.STATUS_MAP.get(
                status_id,
                CodeSubmission.SubmissionStatus.ACCEPTED
                if data.get("exit_code") == 0
                else CodeSubmission.SubmissionStatus.RUNTIME_ERROR,
            )

            raw_stdout = data.get("stdout") or ""
            raw_stderr = data.get("stderr") or ""
            compile_output = data.get("compile_output") or ""
            message = data.get("message") or ""

            stderr_out = raw_stderr
            if not stderr_out and compile_output:
                stderr_out = compile_output
            if not stderr_out and message:
                stderr_out = message

            exec_time = float(data.get("time") or 0.0)
            mem_kb = int(data.get("memory") or 0)
            exit_code = data.get("exit_code")

            return ExecutionOutput(
                status=status_str,
                stdout=raw_stdout,
                stderr=stderr_out,
                execution_time_seconds=exec_time,
                memory_kb=mem_kb,
                exit_code=exit_code,
                compilation_output=compile_output,
            )
        except Exception as exc:
            logger.exception("Judge0 HTTP connection failed: %s", exc)
            return ExecutionOutput(
                status=CodeSubmission.SubmissionStatus.RUNTIME_ERROR,
                stderr=f"Sandboxed execution service connection error: {str(exc)}",
                exit_code=1,
            )

    def execute(
        self,
        language: str,
        source_code: str,
        stdin: str = "",
        time_limit_seconds: float = 2.0,
        memory_limit_mb: int = 128,
        expected_output: str | None = None,
    ) -> ExecutionOutput:
        """Executes student code on Judge0 sandboxed environment."""
        raw_lang = language.strip().lower()
        norm_lang = self.NORMALIZE_LANG_MAP.get(raw_lang)
        if not norm_lang or norm_lang not in self.LANGUAGE_IDS:
            return ExecutionOutput(
                status=CodeSubmission.SubmissionStatus.COMPILATION_ERROR,
                stderr=f"Unsupported language '{language}'. Supported: {sorted(self.LANGUAGE_IDS.keys())}",
                exit_code=1,
            )

        clean_code = self._prepare_source_code(norm_lang, source_code)

        # 1. If SDK execution is explicitly configured, attempt via SDK first
        if self.use_sdk:
            result = self._execute_via_sdk(
                norm_lang=norm_lang,
                source_code=clean_code,
                stdin=stdin,
                time_limit_seconds=time_limit_seconds,
                memory_limit_mb=memory_limit_mb,
            )
            if result is not None:
                return result

        # 2. Primary / Default: High-reliability direct HTTP JSON API
        return self._execute_via_http(
            norm_lang=norm_lang,
            source_code=clean_code,
            stdin=stdin,
            time_limit_seconds=time_limit_seconds,
            memory_limit_mb=memory_limit_mb,
            expected_output=expected_output,
        )
