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

        from apps.courses.models import Course, CourseEnrollment

        # Determine target course for the student to prevent cross-course question duplicates
        course_id = request.query_params.get("course_id")
        target_course = None

        if course_id:
            target_course = Course.objects.filter(id=course_id, is_published=True, is_deleted=False).first()

        if not target_course:
            # Check student active enrollment
            enrollment = (
                CourseEnrollment.objects.filter(student=student, status="ACTIVE")
                .select_related("course")
                .first()
            )
            if enrollment and enrollment.course and enrollment.course.is_published and not enrollment.course.is_deleted:
                target_course = enrollment.course

        if not target_course:
            # Fallback to the primary active published course
            target_course = Course.objects.filter(is_published=True, is_deleted=False).order_by("order", "id").first()

        qs = CodingQuestion.objects.filter(is_active=True).select_related("module", "module__course")

        if target_course:
            qs = qs.filter(module__course=target_course)

        module_id = request.query_params.get("module_id")
        if module_id:
            qs = qs.filter(module_id=module_id)

        difficulty = request.query_params.get("difficulty")
        if difficulty:
            qs = qs.filter(difficulty=difficulty.upper())

        search = request.query_params.get("search")
        if search:
            qs = qs.filter(title__icontains=search)

        from apps.assignments.progression import StudentCurriculumProgressionService

        # Calculate live sequential module progression for this student and course
        unlock_map = (
            StudentCurriculumProgressionService.get_course_modules_unlock_map(student, target_course)
            if target_course
            else {}
        )

        # Prefetch student progress
        progress_map = {
            p.question_id: p
            for p in StudentQuestionProgress.objects.filter(student=student)
        }

        # Deduplicate to strictly prevent any repeated questions by (module_order, title)
        seen_keys = set()
        results = []
        for q in qs.order_by("module__order_index", "order", "id"):
            dedup_key = (q.module.order_index, q.title.strip().lower())
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            prog = progress_map.get(q.id)
            mod_status = unlock_map.get(str(q.module_id), {})
            setattr(q, "is_solved", prog.is_solved if prog else False)
            setattr(q, "best_score", float(prog.best_score) if prog else 0.0)
            setattr(q, "attempts_count", prog.attempts_count if prog else 0)
            setattr(q, "is_module_locked", mod_status.get("is_locked", False))
            setattr(q, "module_unlock_requirement", mod_status.get("unlock_requirement", None))
            results.append(q)

        serializer = StudentQuestionListSerializer(results, many=True)
        return api_success(
            data={
                "questions": serializer.data,
                "modules_progress": list(unlock_map.values()),
                "target_course": {
                    "id": str(target_course.id),
                    "title": target_course.title,
                }
                if target_course
                else None,
            },
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

        from apps.assignments.progression import StudentCurriculumProgressionService
        unlock_map = (
            StudentCurriculumProgressionService.get_course_modules_unlock_map(student, question.module.course)
            if question.module.course
            else {}
        )
        mod_status = unlock_map.get(str(question.module_id), {})
        is_locked = mod_status.get("is_locked", False)
        unlock_req = mod_status.get("unlock_requirement", None)

        prog = StudentQuestionProgress.objects.filter(student=student, question=question).first()
        setattr(question, "is_solved", prog.is_solved if prog else False)
        setattr(question, "best_score", float(prog.best_score) if prog else 0.0)
        setattr(question, "attempts_count", prog.attempts_count if prog else 0)
        setattr(question, "is_module_locked", is_locked)
        setattr(question, "module_unlock_requirement", unlock_req)

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

        from apps.assignments.progression import StudentCurriculumProgressionService
        if question.module.course:
            unlock_map = StudentCurriculumProgressionService.get_course_modules_unlock_map(student, question.module.course)
            mod_status = unlock_map.get(str(question.module_id), {})
            if mod_status.get("is_locked", False):
                return api_error(
                    code="MODULE_LOCKED",
                    message=mod_status.get("unlock_requirement") or "This module is locked. Solve all problems in the previous module to unlock.",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

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

        from apps.assignments.progression import StudentCurriculumProgressionService
        if question.module.course:
            unlock_map = StudentCurriculumProgressionService.get_course_modules_unlock_map(student, question.module.course)
            mod_status = unlock_map.get(str(question.module_id), {})
            if mod_status.get("is_locked", False):
                return api_error(
                    code="MODULE_LOCKED",
                    message=mod_status.get("unlock_requirement") or "This module is locked. Solve all problems in the previous module to unlock.",
                    status_code=status.HTTP_403_FORBIDDEN,
                )

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
