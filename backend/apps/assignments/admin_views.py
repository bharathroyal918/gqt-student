"""Admin views for coding question and test case lifecycle management."""

import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, status
from rest_framework.views import APIView

from apps.assignments.admin_serializers import (
    CodingQuestionAdminCreateSerializer,
    CodingQuestionAdminDetailSerializer,
    CodingQuestionAdminListSerializer,
    CodingQuestionAdminUpdateSerializer,
    TestCaseAdminSerializer,
    TestCaseCreateSerializer,
    TestCaseUpdateSerializer,
)
from apps.assignments.models import CodingQuestion
from apps.assignments.services import AssignmentAdminService
from apps.common.permissions import IsAdmin
from apps.common.responses import api_success
from apps.common.utils import get_client_ip


class QuestionFilter(django_filters.FilterSet):
    module_id = django_filters.UUIDFilter(field_name="module__id")
    difficulty = django_filters.ChoiceFilter(choices=CodingQuestion.DifficultyChoices.choices)
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = CodingQuestion
        fields = ["module_id", "difficulty", "is_active"]


class CodingQuestionAdminListCreateView(generics.ListCreateAPIView):
    """Admin endpoint to list coding questions or create a new algorithmic problem."""

    permission_classes = [IsAdmin]
    serializer_class = CodingQuestionAdminListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = QuestionFilter
    search_fields = ["title", "slug", "problem_statement"]
    ordering_fields = ["order", "points", "created_at", "title"]
    ordering = ["order", "title"]

    def get_queryset(self):
        return (
            CodingQuestion.objects.select_related("module", "module__course")
            .prefetch_related("test_cases")
            .all()
        )

    @extend_schema(
        request=CodingQuestionAdminCreateSerializer,
        responses={201: CodingQuestionAdminDetailSerializer},
        summary="Admin Create Coding Question",
        tags=["Admin Assignment Management"],
    )
    def post(self, request, *args, **kwargs):
        serializer = CodingQuestionAdminCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        question = AssignmentAdminService.create_question(
            admin_user=request.user,
            module_id=str(data["module_id"]),
            title=data["title"],
            problem_statement=data["problem_statement"],
            difficulty=data.get("difficulty", "EASY"),
            allowed_languages=data.get("allowed_languages"),
            starter_code=data.get("starter_code"),
            time_limit_seconds=data.get("time_limit_seconds"),
            memory_limit_mb=data.get("memory_limit_mb"),
            points=data.get("points"),
            order=data.get("order", 0),
            is_active=data.get("is_active", True),
            slug=data.get("slug"),
            test_cases_data=data.get("test_cases"),
            ip_address=ip_address,
        )
        return api_success(
            data=CodingQuestionAdminDetailSerializer(question).data,
            message="Coding question created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class CodingQuestionAdminDetailUpdateDeleteView(APIView):
    """Admin endpoint to retrieve, edit, or archive a coding question."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: CodingQuestionAdminDetailSerializer},
        summary="Admin Retrieve Question Detail",
        tags=["Admin Assignment Management"],
    )
    def get(self, request, pk):
        question = AssignmentAdminService.get_question(str(pk))
        return api_success(
            data=CodingQuestionAdminDetailSerializer(question).data,
            message="Coding question retrieved successfully.",
        )

    @extend_schema(
        request=CodingQuestionAdminUpdateSerializer,
        responses={200: CodingQuestionAdminDetailSerializer},
        summary="Admin Update Question",
        tags=["Admin Assignment Management"],
    )
    def patch(self, request, pk):
        serializer = CodingQuestionAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        question = AssignmentAdminService.update_question(
            question_id=str(pk),
            admin_user=request.user,
            ip_address=ip_address,
            **serializer.validated_data,
        )
        return api_success(
            data=CodingQuestionAdminDetailSerializer(question).data,
            message="Coding question updated successfully.",
        )

    @extend_schema(
        responses={200: CodingQuestionAdminDetailSerializer},
        summary="Admin Archive Question",
        tags=["Admin Assignment Management"],
    )
    def delete(self, request, pk):
        ip_address = get_client_ip(request)
        question = AssignmentAdminService.archive_question(
            question_id=str(pk),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=CodingQuestionAdminDetailSerializer(question).data,
            message="Coding question safely archived.",
        )


class TestCaseAdminCreateView(APIView):
    """Admin endpoint to add a visible or hidden testcase to a question."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=TestCaseCreateSerializer,
        responses={201: TestCaseAdminSerializer},
        summary="Admin Add Test Case",
        tags=["Admin Assignment Management"],
    )
    def post(self, request, pk):
        serializer = TestCaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        ip_address = get_client_ip(request)

        test_case = AssignmentAdminService.add_test_case(
            question_id=str(pk),
            input_data=data.get("input_data", ""),
            expected_output=data.get("expected_output", ""),
            is_visible=data.get("is_visible", True),
            weight=data.get("weight"),
            order=data.get("order"),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data=TestCaseAdminSerializer(test_case).data,
            message="Test case created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class TestCaseAdminDetailUpdateDeleteView(APIView):
    """Admin endpoint to update or delete a specific test case."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=TestCaseUpdateSerializer,
        responses={200: TestCaseAdminSerializer},
        summary="Admin Update Test Case",
        tags=["Admin Assignment Management"],
    )
    def patch(self, request, pk):
        serializer = TestCaseUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip_address = get_client_ip(request)

        test_case = AssignmentAdminService.update_test_case(
            test_case_id=str(pk),
            admin_user=request.user,
            ip_address=ip_address,
            **serializer.validated_data,
        )
        return api_success(
            data=TestCaseAdminSerializer(test_case).data,
            message="Test case updated successfully.",
        )

    @extend_schema(
        summary="Admin Delete Test Case",
        tags=["Admin Assignment Management"],
    )
    def delete(self, request, pk):
        ip_address = get_client_ip(request)
        AssignmentAdminService.delete_test_case(
            test_case_id=str(pk),
            admin_user=request.user,
            ip_address=ip_address,
        )
        return api_success(
            data={},
            message="Test case deleted successfully.",
        )
