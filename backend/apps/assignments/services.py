"""Domain services for administrative coding challenge and test case management."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.text import slugify

from apps.accounts.models import AuditLog, User
from apps.assignments.models import CodingQuestion, TestCase
from apps.common.exceptions import DomainException
from apps.modules.models import Module


class AssignmentAdminService:
    """Service managing algorithmic challenges, testcase suites, and sandbox configurations."""

    @classmethod
    def get_question(cls, question_id: str) -> CodingQuestion:
        return get_object_or_404(
            CodingQuestion.objects.select_related("module", "module__course").prefetch_related(
                "test_cases"
            ),
            id=question_id,
        )

    @classmethod
    @transaction.atomic
    def create_question(
        cls,
        admin_user: User,
        module_id: str,
        title: str,
        problem_statement: str,
        difficulty: str = CodingQuestion.DifficultyChoices.EASY,
        allowed_languages: Optional[List[str]] = None,
        starter_code: Optional[Dict[str, str]] = None,
        time_limit_seconds: Decimal = Decimal("2.00"),
        memory_limit_mb: int = 128,
        points: Decimal = Decimal("100.00"),
        order: int = 0,
        is_active: bool = True,
        slug: Optional[str] = None,
        test_cases_data: Optional[List[Dict[str, Any]]] = None,
        ip_address: Optional[str] = None,
    ) -> CodingQuestion:
        module = get_object_or_404(Module, id=module_id)

        q_slug = slug.strip().lower() if slug else slugify(title)
        if CodingQuestion.objects.filter(module=module, slug=q_slug).exists():
            raise DomainException("A question with this slug already exists in this module.")

        if difficulty not in CodingQuestion.DifficultyChoices.values:
            raise DomainException(
                f"Invalid difficulty. Allowed choices: {CodingQuestion.DifficultyChoices.values}"
            )

        languages = allowed_languages or ["python", "java", "c", "cpp", "javascript"]
        templates = starter_code or {}

        question = CodingQuestion.objects.create(
            module=module,
            title=title.strip(),
            slug=q_slug,
            difficulty=difficulty,
            problem_statement=problem_statement.strip(),
            allowed_languages=languages,
            starter_code=templates,
            time_limit_seconds=time_limit_seconds,
            memory_limit_mb=memory_limit_mb,
            points=points,
            order=order,
            is_active=is_active,
            created_by=admin_user,
        )

        if test_cases_data:
            for idx, tc in enumerate(test_cases_data):
                TestCase.objects.create(
                    question=question,
                    input_data=tc.get("input_data", "").strip(),
                    expected_output=tc.get("expected_output", "").strip(),
                    is_visible=tc.get("is_visible", True),
                    weight=tc.get("weight", Decimal("1.00")),
                    order=tc.get("order", idx + 1),
                )

        AuditLog.objects.create(
            actor=admin_user,
            action="QUESTION_CREATED",
            target_model="CodingQuestion",
            target_id=str(question.id),
            ip_address=ip_address,
            payload={
                "module_id": str(module.id),
                "title": question.title,
                "difficulty": difficulty,
            },
        )
        return question

    @classmethod
    @transaction.atomic
    def update_question(
        cls,
        question_id: str,
        admin_user: User,
        title: Optional[str] = None,
        slug: Optional[str] = None,
        difficulty: Optional[str] = None,
        problem_statement: Optional[str] = None,
        allowed_languages: Optional[List[str]] = None,
        starter_code: Optional[Dict[str, str]] = None,
        time_limit_seconds: Optional[Decimal] = None,
        memory_limit_mb: Optional[int] = None,
        points: Optional[Decimal] = None,
        order: Optional[int] = None,
        is_active: Optional[bool] = None,
        ip_address: Optional[str] = None,
    ) -> CodingQuestion:
        question = cls.get_question(question_id)
        update_fields = ["updated_at"]

        if title is not None:
            question.title = title.strip()
            update_fields.append("title")

        if slug is not None:
            q_slug = slug.strip().lower()
            if (
                CodingQuestion.objects.filter(module=question.module, slug=q_slug)
                .exclude(id=question.id)
                .exists()
            ):
                raise DomainException("A question with this slug already exists in this module.")
            question.slug = q_slug
            update_fields.append("slug")

        if difficulty is not None:
            if difficulty not in CodingQuestion.DifficultyChoices.values:
                raise DomainException("Invalid difficulty specified.")
            question.difficulty = difficulty
            update_fields.append("difficulty")

        if problem_statement is not None:
            question.problem_statement = problem_statement.strip()
            update_fields.append("problem_statement")

        if allowed_languages is not None:
            question.allowed_languages = allowed_languages
            update_fields.append("allowed_languages")

        if starter_code is not None:
            question.starter_code = starter_code
            update_fields.append("starter_code")

        if time_limit_seconds is not None:
            question.time_limit_seconds = time_limit_seconds
            update_fields.append("time_limit_seconds")

        if memory_limit_mb is not None:
            question.memory_limit_mb = memory_limit_mb
            update_fields.append("memory_limit_mb")

        if points is not None:
            question.points = points
            update_fields.append("points")

        if order is not None:
            question.order = order
            update_fields.append("order")

        if is_active is not None:
            question.is_active = is_active
            update_fields.append("is_active")

        question.save(update_fields=update_fields)

        AuditLog.objects.create(
            actor=admin_user,
            action="QUESTION_UPDATED",
            target_model="CodingQuestion",
            target_id=str(question.id),
            ip_address=ip_address,
            payload={"updated_fields": update_fields},
        )
        return question

    @classmethod
    @transaction.atomic
    def archive_question(
        cls, question_id: str, admin_user: User, ip_address: Optional[str] = None
    ) -> CodingQuestion:
        question = cls.get_question(question_id)
        question.is_active = False
        question.save(update_fields=["is_active", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="QUESTION_ARCHIVED",
            target_model="CodingQuestion",
            target_id=str(question.id),
            ip_address=ip_address,
        )
        return question

    @classmethod
    @transaction.atomic
    def add_test_case(
        cls,
        question_id: str,
        input_data: str,
        expected_output: str,
        is_visible: bool,
        admin_user: User,
        weight: Decimal = Decimal("1.00"),
        order: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> TestCase:
        question = cls.get_question(question_id)

        if order is None:
            max_order = question.test_cases.count()
            order = max_order + 1

        test_case = TestCase.objects.create(
            question=question,
            input_data=input_data.strip(),
            expected_output=expected_output.strip(),
            is_visible=is_visible,
            weight=weight,
            order=order,
        )

        AuditLog.objects.create(
            actor=admin_user,
            action="TESTCASE_CREATED",
            target_model="TestCase",
            target_id=str(test_case.id),
            ip_address=ip_address,
            payload={"question_id": str(question.id), "is_visible": is_visible},
        )
        return test_case

    @classmethod
    @transaction.atomic
    def update_test_case(
        cls,
        test_case_id: str,
        admin_user: User,
        input_data: Optional[str] = None,
        expected_output: Optional[str] = None,
        is_visible: Optional[bool] = None,
        weight: Optional[Decimal] = None,
        order: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> TestCase:
        test_case = get_object_or_404(TestCase.objects.select_related("question"), id=test_case_id)
        update_fields = ["updated_at"]

        if input_data is not None:
            test_case.input_data = input_data.strip()
            update_fields.append("input_data")

        if expected_output is not None:
            test_case.expected_output = expected_output.strip()
            update_fields.append("expected_output")

        if is_visible is not None:
            test_case.is_visible = is_visible
            update_fields.append("is_visible")

        if weight is not None:
            test_case.weight = weight
            update_fields.append("weight")

        if order is not None:
            test_case.order = order
            update_fields.append("order")

        test_case.save(update_fields=update_fields)

        AuditLog.objects.create(
            actor=admin_user,
            action="TESTCASE_UPDATED",
            target_model="TestCase",
            target_id=str(test_case.id),
            ip_address=ip_address,
            payload={"updated_fields": update_fields},
        )
        return test_case

    @classmethod
    @transaction.atomic
    def delete_test_case(
        cls, test_case_id: str, admin_user: User, ip_address: Optional[str] = None
    ) -> None:
        test_case = get_object_or_404(TestCase, id=test_case_id)
        q_id = str(test_case.question_id)
        test_case.delete()

        AuditLog.objects.create(
            actor=admin_user,
            action="TESTCASE_DELETED",
            target_model="TestCase",
            target_id=test_case_id,
            ip_address=ip_address,
            payload={"question_id": q_id},
        )
