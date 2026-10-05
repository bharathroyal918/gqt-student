"""Sequential Module Progression and Unlocking Service."""

from typing import Any, Dict, Optional
from django.db.models import Count

from apps.assignments.models import CodingQuestion, StudentQuestionProgress
from apps.courses.models import Course
from apps.modules.models import Module
from apps.students.models import StudentProfile


class StudentCurriculumProgressionService:
    """Calculates sequential module unlocking and progression for coding assignments."""

    @classmethod
    def get_course_modules_unlock_map(
        cls, student_profile: StudentProfile, course: Course
    ) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary mapping module_id -> {
            "module_id": str,
            "order_index": int,
            "title": str,
            "total_questions": int,
            "solved_questions": int,
            "is_locked": bool,
            "is_completed": bool,
            "unlock_requirement": Optional[str],
        }

        Rules:
        - The first sequential module (lowest order_index, e.g. Module 1) is ALWAYS UNLOCKED.
        - For module N (order_index > lowest), module N is unlocked IF AND ONLY IF all preceding modules
          in this course have is_completed == True (all questions in them are solved).
        - If any preceding module is incomplete, module N is LOCKED (is_locked=True) with a friendly requirement.
        """
        modules = list(
            Module.objects.filter(course=course, is_published=True).order_by("order_index", "id")
        )
        if not modules:
            return {}

        # 1. Total questions per module
        q_counts = dict(
            CodingQuestion.objects.filter(module__in=modules, is_active=True)
            .values("module_id")
            .annotate(cnt=Count("id"))
            .values_list("module_id", "cnt")
        )

        # 2. Solved questions by student per module
        solved_counts = dict(
            StudentQuestionProgress.objects.filter(
                student=student_profile,
                question__module__in=modules,
                is_solved=True,
                question__is_active=True,
            )
            .values("question__module_id")
            .annotate(cnt=Count("id"))
            .values_list("question__module_id", "cnt")
        )

        result: Dict[str, Dict[str, Any]] = {}
        all_previous_completed = True
        earliest_incomplete_module: Optional[Module] = None

        for idx, mod in enumerate(modules):
            total_q = q_counts.get(mod.id, 0)
            solved_q = solved_counts.get(mod.id, 0)
            is_completed = total_q > 0 and solved_q >= total_q

            if idx == 0:
                # The very first module is ALWAYS unlocked
                is_locked = False
                unlock_req = None
            else:
                if all_previous_completed:
                    is_locked = False
                    unlock_req = None
                else:
                    is_locked = True
                    prev_name = (
                        earliest_incomplete_module.title
                        if earliest_incomplete_module
                        else f"Module {mod.order_index - 1}"
                    )
                    prev_order = (
                        earliest_incomplete_module.order_index
                        if earliest_incomplete_module
                        else (mod.order_index - 1)
                    )
                    prev_total = (
                        q_counts.get(earliest_incomplete_module.id, 0)
                        if earliest_incomplete_module
                        else 0
                    )
                    prev_solved = (
                        solved_counts.get(earliest_incomplete_module.id, 0)
                        if earliest_incomplete_module
                        else 0
                    )
                    unlock_req = (
                        f"Solve all {prev_total} problems in Module {prev_order} ({prev_name}) "
                        f"to unlock ({prev_solved}/{prev_total} solved)."
                    )

            if not is_completed and all_previous_completed:
                all_previous_completed = False
                earliest_incomplete_module = mod

            result[str(mod.id)] = {
                "module_id": str(mod.id),
                "order_index": mod.order_index,
                "title": mod.title,
                "total_questions": total_q,
                "solved_questions": solved_q,
                "is_locked": is_locked,
                "is_completed": is_completed,
                "unlock_requirement": unlock_req,
            }

        return result
