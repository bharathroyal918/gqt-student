"""Student API Views for Coding Practice Platform."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.assignments.execution.service import CodeExecutionService
from apps.assignments.models import CodingQuestion, CodeSubmission, StudentQuestionProgress
from apps.assignments.student_serializers import (
    CodeRunRequestSerializer,
    CodeSubmitRequestSerializer,
    StudentQuestionDetailSerializer,
    StudentQuestionListSerializer,
    StudentSubmissionSerializer,
)
from apps.common.responses import api_error, api_success
from apps.students.models import StudentProfile


class StudentQuestionListView(APIView):
    """List practice coding challenges with student mastery and progress indicators."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Student Practice Questions",
        tags=["Student Coding Platform"],
    )
    def get(self, request):
        if not hasattr(request.user, "student_profile") and not StudentProfile.objects.filter(user=request.user).exists():
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="User does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        student = request.user.student_profile
        if not CodingQuestion.objects.filter(is_active=True).exists():
            from apps.assignments.seeds import seed_coding_questions
            seed_coding_questions()

        qs = CodingQuestion.objects.filter(is_active=True).select_related("module", "module__course")

        module_id = request.query_params.get("module_id")
        if module_id:
            qs = qs.filter(module_id=module_id)

        difficulty = request.query_params.get("difficulty")
        if difficulty:
            qs = qs.filter(difficulty=difficulty.upper())

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(title__icontains=search)

        # Prefetch student progress
        progress_map = {
            p.question_id: p
            for p in StudentQuestionProgress.objects.filter(student=student)
        }

        results = []
        for q in qs.order_by("module__order_index", "order", "title"):
            prog = progress_map.get(q.id)
            setattr(q, "is_solved", prog.is_solved if prog else False)
            setattr(q, "best_score", float(prog.best_score) if prog else 0.0)
            setattr(q, "attempts_count", prog.attempts_count if prog else 0)
            results.append(q)

        serializer = StudentQuestionListSerializer(results, many=True)
        return api_success(
            data={"questions": serializer.data},
            message="Coding practice questions retrieved successfully.",
        )


class StudentQuestionDetailView(APIView):
    """Retrieve question description, constraints, input/output format, and sample testcases."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Practice Question Detail",
        tags=["Student Coding Platform"],
    )
    def get(self, request, question_id):
        if not hasattr(request.user, "student_profile") and not StudentProfile.objects.filter(user=request.user).exists():
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="User does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        student = request.user.student_profile
        try:
            question = CodingQuestion.objects.select_related("module", "module__course").get(
                id=question_id, is_active=True
            )
        except CodingQuestion.DoesNotExist:
            return api_error(
                code="QUESTION_NOT_FOUND",
                message="Coding challenge does not exist or is inactive.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        prog = StudentQuestionProgress.objects.filter(student=student, question=question).first()
        setattr(question, "is_solved", prog.is_solved if prog else False)
        setattr(question, "best_score", float(prog.best_score) if prog else 0.0)
        setattr(question, "attempts_count", prog.attempts_count if prog else 0)

        serializer = StudentQuestionDetailSerializer(question)
        return api_success(
            data=serializer.data,
            message="Question details retrieved successfully.",
        )


class StudentCodeRunView(APIView):
    """Run code against sample visible test cases or custom standard input."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CodeRunRequestSerializer,
        summary="Run Code in Sandbox",
        tags=["Student Coding Platform"],
    )
    def post(self, request, question_id):
        if not hasattr(request.user, "student_profile") and not StudentProfile.objects.filter(user=request.user).exists():
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="User does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = CodeRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = request.user.student_profile
        result = CodeExecutionService.run_code(
            student_profile=student,
            question_id=str(question_id),
            language=serializer.validated_data["language"],
            source_code=serializer.validated_data["source_code"],
            custom_input=serializer.validated_data.get("custom_input"),
        )
        return api_success(
            data=result,
            message="Code execution completed.",
        )


class StudentCodeSubmitView(APIView):
    """Submit code for full automated grading across visible and hidden test suites."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CodeSubmitRequestSerializer,
        summary="Submit Code for Official Evaluation",
        tags=["Student Coding Platform"],
    )
    def post(self, request, question_id):
        if not hasattr(request.user, "student_profile") and not StudentProfile.objects.filter(user=request.user).exists():
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="User does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = CodeSubmitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student = request.user.student_profile
        result = CodeExecutionService.submit_code(
            student_profile=student,
            question_id=str(question_id),
            language=serializer.validated_data["language"],
            source_code=serializer.validated_data["source_code"],
        )
        return api_success(
            data=result,
            message="Code submission graded successfully.",
            status_code=status.HTTP_201_CREATED,
        )


class StudentSubmissionHistoryView(APIView):
    """View personal submission history for a coding question."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Personal Submission History",
        tags=["Student Coding Platform"],
    )
    def get(self, request, question_id):
        if not hasattr(request.user, "student_profile") and not StudentProfile.objects.filter(user=request.user).exists():
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="User does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        student = request.user.student_profile
        submissions = CodeSubmission.objects.filter(
            student=student, question_id=question_id
        ).select_related("question").order_by("-submitted_at")

        serializer = StudentSubmissionSerializer(submissions, many=True)
        return api_success(
            data={"submissions": serializer.data},
            message="Submission history retrieved successfully.",
        )


class StudentSubmissionDetailView(APIView):
    """Retrieve detailed execution breakdown for a past submission."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve Submission Execution Detail",
        tags=["Student Coding Platform"],
    )
    def get(self, request, submission_id):
        if not hasattr(request.user, "student_profile") and not StudentProfile.objects.filter(user=request.user).exists():
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="User does not possess an active student profile.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        student = request.user.student_profile
        result = CodeExecutionService.get_execution_result(
            submission_id=str(submission_id), student_profile=student
        )
        return api_success(
            data=result,
            message="Submission details retrieved.",
        )
