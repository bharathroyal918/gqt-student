"""Production-Grade Leaderboard Service.

Handles:
- Real-time score aggregation & ranking
- Top 10 leaderboard with Top 3 highlight markers
- Exact rank calculation with deterministic tie-breaking rules
- Current student position lookup & nearby ranks (±2)
- Multi-tier caching with instant invalidation upon score change
- Course & Batch filtering for students and administrators
- Privacy enforcement (no leakage of email, phone, or private student info)
"""

from typing import Any

from django.core.cache import cache
from django.db.models import Count, Q

from apps.courses.models import CourseEnrollment
from apps.students.models import StudentProfile


class LeaderboardService:
    """Core domain service for scalable leaderboard ranking, caching, and analytics."""

    CACHE_KEY_TOP10 = "leaderboard_top10"
    CACHE_KEY_TOP10_BATCH = "leaderboard_top10_batch_{batch}"
    CACHE_KEY_TOP10_COURSE = "leaderboard_top10_course_{course}"
    CACHE_TTL_SECONDS = 600  # 10 minutes (invalidated instantly on score change)

    # --------------------------------------------------------------------------
    # TIE-BREAKING SPECIFICATION
    # --------------------------------------------------------------------------
    # 1. total_points DESC (Primary)
    # 2. solved_questions_count DESC (Secondary: more problems solved)
    # 3. current_streak_days DESC (Tertiary: continuous daily learning streak)
    # 4. created_at ASC (Quaternary: earlier account registration timestamp)
    # --------------------------------------------------------------------------

    @classmethod
    def invalidate_cache(
        cls, batch_code: str | None = None, course_id: str | None = None
    ) -> None:
        """Flushes leaderboard caches whenever scores or enrollments change."""
        cache.delete(cls.CACHE_KEY_TOP10)
        cache.delete("student_leaderboard_top10")
        if batch_code:
            cache.delete(cls.CACHE_KEY_TOP10_BATCH.format(batch=batch_code))
        if course_id:
            cache.delete(cls.CACHE_KEY_TOP10_COURSE.format(course=course_id))

    @classmethod
    def get_base_queryset(
        cls, batch_code: str | None = None, course_id: str | None = None
    ):
        """Returns student profiles annotated with solved questions count and filtered cleanly."""
        qs = (
            StudentProfile.objects.filter(user__is_active=True)
            .select_related("user")
            .annotate(
                solved_questions_count=Count(
                    "question_progresses",
                    filter=Q(question_progresses__is_solved=True),
                    distinct=True,
                )
            )
        )

        if batch_code:
            qs = qs.filter(batch_code=batch_code.strip())

        if course_id:
            qs = qs.filter(
                enrollments__course_id=course_id,
                enrollments__status=CourseEnrollment.EnrollmentStatus.ACTIVE,
            ).distinct()

        return qs.order_by(
            "-total_points",
            "-solved_questions_count",
            "-current_streak_days",
            "created_at",
        )

    @classmethod
    def get_top_performers(
        cls,
        limit: int = 10,
        batch_code: str | None = None,
        course_id: str | None = None,
        current_student: StudentProfile | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieves top N performers formatted safely for student visibility."""
        cache_key = cls.CACHE_KEY_TOP10
        if batch_code:
            cache_key = cls.CACHE_KEY_TOP10_BATCH.format(batch=batch_code)
        elif course_id:
            cache_key = cls.CACHE_KEY_TOP10_COURSE.format(course=course_id)

        cached_data = cache.get(cache_key)
        if cached_data is None:
            qs = cls.get_base_queryset(batch_code=batch_code, course_id=course_id)[
                :limit
            ]
            results = []
            for rank, sp in enumerate(qs, start=1):
                results.append(
                    {
                        "rank": rank,
                        "student_id": str(sp.id),
                        "student_id_number": sp.student_id_number,
                        "full_name": sp.full_name,
                        "avatar_url": sp.avatar_url or "",
                        "batch_code": sp.batch_code,
                        "total_points": float(sp.total_points),
                        "current_streak_days": sp.current_streak_days,
                        "solved_questions_count": getattr(
                            sp, "solved_questions_count", 0
                        ),
                        "is_top_3": rank <= 3,
                    }
                )
            cache.set(cache_key, results, timeout=cls.CACHE_TTL_SECONDS)
            cached_data = results

        # Decorate with is_current_student dynamically
        current_id = str(current_student.id) if current_student else None
        output = []
        for entry in cached_data:
            entry_copy = dict(entry)
            entry_copy["is_current_student"] = entry_copy["student_id"] == current_id
            output.append(entry_copy)

        return output

    @classmethod
    def calculate_exact_student_rank(
        cls,
        student: StudentProfile,
        batch_code: str | None = None,
        course_id: str | None = None,
    ) -> dict[str, Any]:
        """Calculates precise rank for a student following deterministic tie-breaking rules."""
        qs = cls.get_base_queryset(batch_code=batch_code, course_id=course_id)

        # Count how many students rank strictly higher
        # 1. Higher total points
        higher_score_q = Q(total_points__gt=student.total_points)

        # 2. Equal total points, higher solved count
        student_solved = student.question_progresses.filter(is_solved=True).count()
        equal_score_higher_solved_q = Q(
            total_points=student.total_points,
            solved_questions_count__gt=student_solved,
        )

        # 3. Equal score & solved, higher streak
        equal_score_solved_higher_streak_q = Q(
            total_points=student.total_points,
            solved_questions_count=student_solved,
            current_streak_days__gt=student.current_streak_days,
        )

        # 4. Equal score, solved, streak, earlier created_at
        equal_score_solved_streak_earlier_q = Q(
            total_points=student.total_points,
            solved_questions_count=student_solved,
            current_streak_days=student.current_streak_days,
            created_at__lt=student.created_at,
        )

        combined_higher_q = (
            higher_score_q
            | equal_score_higher_solved_q
            | equal_score_solved_higher_streak_q
            | equal_score_solved_streak_earlier_q
        )

        rank = qs.filter(combined_higher_q).count() + 1
        total_participants = qs.count()

        return {
            "rank": rank,
            "student_id": str(student.id),
            "student_id_number": student.student_id_number,
            "full_name": student.full_name,
            "avatar_url": student.avatar_url or "",
            "batch_code": student.batch_code,
            "total_points": float(student.total_points),
            "current_streak_days": student.current_streak_days,
            "solved_questions_count": student_solved,
            "is_current_student": True,
            "is_top_3": rank <= 3,
            "is_in_top_10": rank <= 10,
            "total_participants": total_participants,
        }

    @classmethod
    def get_nearby_students(
        cls,
        student: StudentProfile,
        delta: int = 2,
        batch_code: str | None = None,
        course_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Returns students ranked directly above and below the target student (nearby range)."""
        qs = list(cls.get_base_queryset(batch_code=batch_code, course_id=course_id))
        target_idx = None
        for idx, sp in enumerate(qs):
            if sp.id == student.id:
                target_idx = idx
                break

        if target_idx is None:
            return []

        start_idx = max(0, target_idx - delta)
        end_idx = min(len(qs), target_idx + delta + 1)

        nearby = []
        for idx in range(start_idx, end_idx):
            sp = qs[idx]
            rank = idx + 1
            nearby.append(
                {
                    "rank": rank,
                    "student_id": str(sp.id),
                    "student_id_number": sp.student_id_number,
                    "full_name": sp.full_name,
                    "avatar_url": sp.avatar_url or "",
                    "batch_code": sp.batch_code,
                    "total_points": float(sp.total_points),
                    "current_streak_days": sp.current_streak_days,
                    "solved_questions_count": getattr(sp, "solved_questions_count", 0),
                    "is_current_student": sp.id == student.id,
                    "is_top_3": rank <= 3,
                }
            )

        return nearby

    @classmethod
    def get_full_leaderboard_for_student(
        cls,
        student: StudentProfile,
        batch_code: str | None = None,
        course_id: str | None = None,
    ) -> dict[str, Any]:
        """Assembles top 10, authenticated student's exact rank, and nearby standing."""
        top_10 = cls.get_top_performers(
            limit=10,
            batch_code=batch_code,
            course_id=course_id,
            current_student=student,
        )
        my_standing = cls.calculate_exact_student_rank(
            student=student, batch_code=batch_code, course_id=course_id
        )
        nearby = cls.get_nearby_students(
            student=student, delta=2, batch_code=batch_code, course_id=course_id
        )

        return {
            "top_10": top_10,
            "current_student": my_standing,
            "nearby_students": nearby,
            "total_participants": my_standing["total_participants"],
            "tie_breaking_rules": [
                "1. Total Points (Highest score first)",
                "2. Solved Challenges Count (More problems solved first)",
                "3. Continuous Streak Days (Higher active streak first)",
                "4. Registration Date (Earlier account registration first)",
            ],
        }

    @classmethod
    def get_admin_leaderboard_queryset(
        cls,
        batch_code: str | None = None,
        course_id: str | None = None,
        search: str | None = None,
    ):
        """Admin leaderboard queryset supporting deep filtering and student information."""
        qs = cls.get_base_queryset(batch_code=batch_code, course_id=course_id)

        if search:
            qs = qs.filter(
                Q(full_name__icontains=search)
                | Q(student_id_number__icontains=search)
                | Q(user__email__icontains=search)
            )

        return qs
