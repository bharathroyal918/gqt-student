from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from apps.assignments.models import (
    CodeSubmission,
    CodingQuestion,
    ExecutionResult,
    StudentQuestionProgress,
)
from apps.assignments.models import TestCase as CodingTestCase
from apps.courses.models import Course
from apps.modules.models import Module
from apps.students.models import StudentProfile

User = get_user_model()


class AssignmentModelTests(TestCase):
    """Test suite for coding assignment models, submissions, and execution results."""

    def setUp(self):
        self.user = User.objects.create_user(email="coder@gqt.local", password="Password123!")
        self.student = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-003",
            full_name="Coding Student",
            batch_code="BATCH-2026-A",
        )
        self.course = Course.objects.create(title="Algorithms", slug="algorithms")
        self.module = Module.objects.create(
            course=self.course,
            title="Loops",
            slug="loops",
            order_index=3,
        )
        self.question = CodingQuestion.objects.create(
            module=self.module,
            title="Sum of Natural Numbers",
            slug="sum-of-natural-numbers",
            difficulty=CodingQuestion.DifficultyChoices.EASY,
            problem_statement="Write a program to compute the sum of N natural numbers.",
            points=Decimal("100.00"),
        )
        self.test_case_1 = CodingTestCase.objects.create(
            question=self.question,
            input_data="5",
            expected_output="15",
            is_visible=True,
            order=1,
        )
        self.test_case_2 = CodingTestCase.objects.create(
            question=self.question,
            input_data="10",
            expected_output="55",
            is_visible=False,
            order=2,
        )

    def test_question_testcases_relationship(self):
        self.assertEqual(self.question.test_cases.count(), 2)
        visible_cases = self.question.test_cases.filter(is_visible=True)
        self.assertEqual(visible_cases.count(), 1)
        self.assertEqual(visible_cases.first(), self.test_case_1)

    def test_submission_and_execution_result(self):
        submission = CodeSubmission.objects.create(
            student=self.student,
            question=self.question,
            language="python",
            source_code="n = int(input())\nprint(n * (n + 1) // 2)",
            status=CodeSubmission.SubmissionStatus.ACCEPTED,
            passed_test_cases=2,
            total_test_cases=2,
            score_awarded=Decimal("100.00"),
            scoring_policy=CodeSubmission.ScoringPolicy.FULL,
        )
        result_1 = ExecutionResult.objects.create(
            submission=submission,
            test_case=self.test_case_1,
            status=ExecutionResult.ResultStatus.PASSED,
            stdout="15\n",
            exit_code=0,
        )
        self.assertEqual(result_1.submission, submission)

        # Unique constraint: cannot have two execution results for same testcase on same submission
        with self.assertRaises(IntegrityError):
            ExecutionResult.objects.create(
                submission=submission,
                test_case=self.test_case_1,
                status=ExecutionResult.ResultStatus.PASSED,
                exit_code=0,
            )

    def test_student_question_progress_unique_constraint(self):
        StudentQuestionProgress.objects.create(
            student=self.student,
            question=self.question,
            is_solved=True,
            best_score=Decimal("100.00"),
        )
        with self.assertRaises(IntegrityError):
            StudentQuestionProgress.objects.create(
                student=self.student,
                question=self.question,
                is_solved=False,
            )
