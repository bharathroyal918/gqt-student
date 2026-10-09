from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class CodingQuestion(BaseModel):
    """Core algorithmic challenge belonging to a sequential curriculum module."""

    class DifficultyChoices(models.TextChoices):
        EASY = "EASY", "Easy"
        MEDIUM = "MEDIUM", "Medium"
        HARD = "HARD", "Hard"

    module = models.ForeignKey(
        "modules.Module", on_delete=models.CASCADE, related_name="questions"
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280)
    difficulty = models.CharField(
        max_length=20,
        choices=DifficultyChoices.choices,
        default=DifficultyChoices.EASY,
        db_index=True,
    )
    problem_statement = models.TextField(
        help_text="Markdown formatted problem description"
    )
    allowed_languages = models.JSONField(
        default=list, help_text="e.g. ['python', 'java', 'c', 'cpp', 'javascript']"
    )
    starter_code = models.JSONField(
        default=dict,
        help_text="Keyed by language code, e.g. {'python': 'def solution(): pass'}",
    )
    time_limit_seconds = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("2.00")
    )
    memory_limit_mb = models.PositiveIntegerField(default=128)
    points = models.DecimalField(
        max_digits=7, decimal_places=2, default=Decimal("100.00")
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="authored_questions",
    )

    class Meta:
        verbose_name = "Coding Question"
        verbose_name_plural = "Coding Questions"
        ordering = ["module", "order", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["module", "slug"], name="unique_module_question_slug"
            ),
            models.CheckConstraint(
                condition=models.Q(points__gt=Decimal("0.00")),
                name="positive_question_points",
            ),
        ]
        indexes = [
            models.Index(fields=["module", "difficulty"], name="question_mod_diff_idx"),
            models.Index(fields=["module", "order"], name="question_mod_order_idx"),
        ]

    def __str__(self):
        return (
            f"{self.module.order_index}.{self.order} {self.title} ({self.difficulty})"
        )


class TestCase(BaseModel):
    """Validation test cases against which student code is judged."""

    question = models.ForeignKey(
        CodingQuestion, on_delete=models.CASCADE, related_name="test_cases"
    )
    input_data = models.TextField(help_text="Standard input payload")
    expected_output = models.TextField(help_text="Expected standard output")
    is_visible = models.BooleanField(
        default=True,
        db_index=True,
        help_text="True for public samples, False for hidden grading tests",
    )
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("1.00")
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Test Case"
        verbose_name_plural = "Test Cases"
        ordering = ["question", "-is_visible", "order"]
        indexes = [
            models.Index(fields=["question", "is_visible"], name="testcase_q_vis_idx"),
        ]

    def __str__(self):
        visibility = "Visible" if self.is_visible else "Hidden"
        return f"TestCase #{self.order} for {self.question.title} ({visibility})"


class CodeSubmission(BaseModel):
    """Immutable record of student code execution submission."""

    class SubmissionStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Execution"
        RUNNING = "RUNNING", "Running"
        ACCEPTED = "ACCEPTED", "Accepted"
        WRONG_ANSWER = "WRONG_ANSWER", "Wrong Answer"
        TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED", "Time Limit Exceeded"
        MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED", "Memory Limit Exceeded"
        COMPILATION_ERROR = "COMPILATION_ERROR", "Compilation Error"
        RUNTIME_ERROR = "RUNTIME_ERROR", "Runtime Error"

    class ScoringPolicy(models.TextChoices):
        FULL = "FULL", "Full Credit"
        HALF = "HALF", "Half Credit"
        ZERO = "ZERO", "Zero Credit"

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="code_submissions",
    )
    question = models.ForeignKey(
        CodingQuestion, on_delete=models.CASCADE, related_name="submissions"
    )
    language = models.CharField(max_length=30, db_index=True)
    source_code = models.TextField()
    status = models.CharField(
        max_length=30,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING,
        db_index=True,
    )
    passed_test_cases = models.PositiveIntegerField(default=0)
    total_test_cases = models.PositiveIntegerField(default=0)
    execution_time_ms = models.PositiveIntegerField(null=True, blank=True)
    peak_memory_kb = models.PositiveIntegerField(null=True, blank=True)
    score_awarded = models.DecimalField(
        max_digits=7, decimal_places=2, default=Decimal("0.00")
    )
    scoring_policy = models.CharField(
        max_length=20, choices=ScoringPolicy.choices, default=ScoringPolicy.ZERO
    )
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Code Submission"
        verbose_name_plural = "Code Submissions"
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(
                fields=["student", "question", "-submitted_at"],
                name="subm_student_q_date_idx",
            ),
            models.Index(
                fields=["question", "status"], name="subm_question_status_idx"
            ),
            models.Index(
                fields=["status", "submitted_at"], name="subm_status_date_idx"
            ),
        ]

    def __str__(self):
        return f"Submission {self.id} by {self.student}: {self.status} ({self.score_awarded} pts)"


class ExecutionResult(BaseModel):
    """Detailed per-testcase execution output produced by sandboxed judge."""

    class ResultStatus(models.TextChoices):
        PASSED = "PASSED", "Passed"
        FAILED = "FAILED", "Failed"
        TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED", "Time Limit Exceeded"
        MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED", "Memory Limit Exceeded"
        RUNTIME_ERROR = "RUNTIME_ERROR", "Runtime Error"
        COMPILATION_ERROR = "COMPILATION_ERROR", "Compilation Error"

    submission = models.ForeignKey(
        CodeSubmission, on_delete=models.CASCADE, related_name="execution_results"
    )
    test_case = models.ForeignKey(
        TestCase, on_delete=models.CASCADE, related_name="execution_results"
    )
    status = models.CharField(
        max_length=30, choices=ResultStatus.choices, db_index=True
    )
    stdout = models.TextField(blank=True, default="")
    stderr = models.TextField(blank=True, default="")
    execution_time_seconds = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True
    )
    memory_kb = models.PositiveIntegerField(null=True, blank=True)
    exit_code = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Execution Result"
        verbose_name_plural = "Execution Results"
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "test_case"],
                name="unique_submission_testcase_result",
            )
        ]

    def __str__(self):
        return f"Result for {self.test_case_id} on {self.submission_id}: {self.status}"


class StudentQuestionProgress(BaseModel):
    """Single source of truth for a student's mastery and highest score on a question."""

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="question_progresses",
    )
    question = models.ForeignKey(
        CodingQuestion, on_delete=models.CASCADE, related_name="student_progresses"
    )
    is_solved = models.BooleanField(default=False, db_index=True)
    best_score = models.DecimalField(
        max_digits=7, decimal_places=2, default=Decimal("0.00"), db_index=True
    )
    best_submission = models.ForeignKey(
        CodeSubmission,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    attempts_count = models.PositiveIntegerField(default=0)
    first_solved_at = models.DateTimeField(null=True, blank=True)
    last_submitted_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Student Question Progress"
        verbose_name_plural = "Student Question Progresses"
        indexes = [
            models.Index(
                fields=["student", "is_solved"], name="q_prog_student_solved_idx"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "question"], name="unique_student_question_progress"
            ),
            models.CheckConstraint(
                condition=models.Q(best_score__gte=Decimal("0.00")),
                name="non_negative_question_best_score",
            ),
        ]

    def __str__(self):
        return f"{self.student}: {self.question.title} (Solved: {self.is_solved}, Best: {self.best_score})"
