"""Domain services for administrative curriculum module management and sequential ordering."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.db import models, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import AuditLog, User
from apps.common.exceptions import DomainException
from apps.courses.models import Course, CourseEnrollment
from apps.modules.models import Module, ModulePrerequisite, StudentModuleProgress
from apps.scoring.models import ScoreRecord
from apps.students.models import StudentProfile


class ModuleAdminService:
    """Service managing learning units, prerequisite graph integrity, and curriculum ordering."""

    @classmethod
    def get_module(cls, module_id: str) -> Module:
        return get_object_or_404(
            Module.objects.select_related("course").prefetch_related(
                "prerequisites__prerequisite_module"
            ),
            id=module_id,
        )

    @classmethod
    @transaction.atomic
    def create_module(
        cls,
        admin_user: User,
        course_id: str,
        title: str,
        summary: str = "",
        lecture_content: str = "",
        slug: Optional[str] = None,
        order_index: Optional[int] = None,
        passing_percentage: Decimal = Decimal("80.00"),
        is_published: bool = True,
        prerequisite_ids: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
    ) -> Module:
        course = get_object_or_404(Course, id=course_id, is_deleted=False)

        if order_index is None or order_index <= 0:
            max_order = (
                Module.objects.filter(course=course).aggregate(max_order=models.Max("order_index"))[
                    "max_order"
                ]
                or 0
            )
            order_index = max_order + 1
        elif Module.objects.filter(course=course, order_index=order_index).exists():
            max_order = (
                Module.objects.filter(course=course).aggregate(max_order=models.Max("order_index"))[
                    "max_order"
                ]
                or 0
            )
            order_index = max_order + 1

        module_slug = slug.strip().lower() if slug else slugify(f"{course.slug}-{order_index}-{title[:40]}")
        base_slug = module_slug
        counter = 1
        while Module.objects.filter(course=course, slug=module_slug).exists():
            module_slug = f"{base_slug}-{counter}"
            counter += 1

        module = Module.objects.create(
            course=course,
            title=title.strip(),
            slug=module_slug,
            order_index=order_index,
            summary=summary.strip(),
            lecture_content=lecture_content.strip(),
            passing_percentage=passing_percentage,
            is_published=is_published,
        )

        if prerequisite_ids:
            cls.set_prerequisites(str(module.id), prerequisite_ids, admin_user)

        AuditLog.objects.create(
            actor=admin_user,
            action="MODULE_CREATED",
            target_model="Module",
            target_id=str(module.id),
            ip_address=ip_address,
            payload={
                "course_id": str(course.id),
                "title": module.title,
                "order_index": module.order_index,
            },
        )
        return module

    @classmethod
    @transaction.atomic
    def delete_module(
        cls, module_id: str, admin_user: User, ip_address: Optional[str] = None
    ) -> None:
        module = cls.get_module(module_id)
        module_id_str = str(module.id)
        title = module.title
        course_id = str(module.course_id)
        module.delete()

        AuditLog.objects.create(
            actor=admin_user,
            action="MODULE_DELETED",
            target_model="Module",
            target_id=module_id_str,
            ip_address=ip_address,
            payload={"title": title, "course_id": course_id},
        )

    @classmethod
    @transaction.atomic
    def update_module(
        cls,
        module_id: str,
        admin_user: User,
        title: Optional[str] = None,
        slug: Optional[str] = None,
        order_index: Optional[int] = None,
        summary: Optional[str] = None,
        lecture_content: Optional[str] = None,
        passing_percentage: Optional[Decimal] = None,
        is_published: Optional[bool] = None,
        prerequisite_ids: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
    ) -> Module:
        module = cls.get_module(module_id)
        update_fields = ["updated_at"]

        if title is not None:
            module.title = title.strip()
            update_fields.append("title")

        if slug is not None:
            module_slug = slug.strip().lower()
            if (
                Module.objects.filter(course=module.course, slug=module_slug)
                .exclude(id=module.id)
                .exists()
            ):
                raise DomainException("A module with this slug already exists in this course.")
            module.slug = module_slug
            update_fields.append("slug")

        if order_index is not None and order_index != module.order_index:
            if (
                Module.objects.filter(course=module.course, order_index=order_index)
                .exclude(id=module.id)
                .exists()
            ):
                raise DomainException(
                    f"A module with order index {order_index} already exists in this course."
                )
            module.order_index = order_index
            update_fields.append("order_index")

        if summary is not None:
            module.summary = summary.strip()
            update_fields.append("summary")

        if lecture_content is not None:
            module.lecture_content = lecture_content.strip()
            update_fields.append("lecture_content")

        if passing_percentage is not None:
            module.passing_percentage = passing_percentage
            update_fields.append("passing_percentage")

        if is_published is not None:
            module.is_published = is_published
            update_fields.append("is_published")

        module.save(update_fields=update_fields)

        if prerequisite_ids is not None:
            cls.set_prerequisites(str(module.id), prerequisite_ids, admin_user)

        AuditLog.objects.create(
            actor=admin_user,
            action="MODULE_UPDATED",
            target_model="Module",
            target_id=str(module.id),
            ip_address=ip_address,
            payload={"updated_fields": update_fields},
        )
        return module

    @classmethod
    @transaction.atomic
    def reorder_modules(
        cls,
        course_id: str,
        order_mappings: List[Dict[str, Any]],
        admin_user: User,
        ip_address: Optional[str] = None,
    ) -> List[Module]:
        """Atomically reorders modules in a course.
        order_mappings: [{'id': '<uuid>', 'order_index': 1}, ...]
        """
        course = get_object_or_404(Course, id=course_id, is_deleted=False)
        module_ids = [m["id"] for m in order_mappings]
        modules = {str(m.id): m for m in Module.objects.filter(course=course, id__in=module_ids)}

        if len(modules) != len(order_mappings):
            raise DomainException("One or more modules do not belong to the specified course.")

        # To avoid temporary unique constraint violation on (course, order_index), offset first
        for i, mapping in enumerate(order_mappings):
            mod = modules[str(mapping["id"])]
            mod.order_index = 10000 + i
            mod.save(update_fields=["order_index", "updated_at"])

        updated_modules = []
        for mapping in order_mappings:
            mod = modules[str(mapping["id"])]
            mod.order_index = mapping["order_index"]
            mod.save(update_fields=["order_index", "updated_at"])
            updated_modules.append(mod)

        AuditLog.objects.create(
            actor=admin_user,
            action="MODULES_REORDERED",
            target_model="Course",
            target_id=str(course.id),
            ip_address=ip_address,
            payload={"order_mappings": order_mappings},
        )
        return sorted(updated_modules, key=lambda m: m.order_index)

    @classmethod
    @transaction.atomic
    def set_prerequisites(
        cls, module_id: str, prerequisite_ids: List[str], admin_user: User
    ) -> None:
        module = cls.get_module(module_id)
        # Clear existing
        ModulePrerequisite.objects.filter(module=module).delete()

        prereqs = Module.objects.filter(id__in=prerequisite_ids, course=module.course)
        for prereq in prereqs:
            if prereq.id == module.id:
                raise DomainException("A module cannot be a prerequisite of itself.")
            if prereq.order_index >= module.order_index:
                raise DomainException(
                    f"Prerequisite '{prereq.title}' (order {prereq.order_index}) "
                    f"must precede '{module.title}' (order {module.order_index})."
                )
            ModulePrerequisite.objects.create(module=module, prerequisite_module=prereq)

    @classmethod
    @transaction.atomic
    def set_publish_status(
        cls, module_id: str, is_published: bool, admin_user: User, ip_address: Optional[str] = None
    ) -> Module:
        module = cls.get_module(module_id)
        module.is_published = is_published
        module.save(update_fields=["is_published", "updated_at"])

        AuditLog.objects.create(
            actor=admin_user,
            action="MODULE_PUBLISH_STATUS_CHANGED",
            target_model="Module",
            target_id=str(module.id),
            ip_address=ip_address,
            payload={"is_published": is_published},
        )
        return module


CURRICULUM_17_MODULES = [
    {
        "order_index": 1,
        "title": "Data Types",
        "slug": "data-types",
        "summary": "Core primitive and complex data representations in modern programming.",
        "lecture_content": "# Data Types in Python\n\nVariables in Python do not require explicit type declaration. Key primitive types include:\n- `int`: Arbitrary-precision integers\n- `float`: Double-precision IEEE 754 floating-point numbers\n- `bool`: Subclass of int representing True or False\n- `complex`: Numbers with real and imaginary parts (e.g. `2 + 3j`)\n\n### Type Casting\nUse built-in functions `int()`, `float()`, `str()`, and `bool()` to explicitly cast data between compatible types.",
    },
    {
        "order_index": 2,
        "title": "If-Else",
        "slug": "if-else",
        "summary": "Conditional branching and logical decision making structures.",
        "lecture_content": "# Conditional Branching (If-Else)\n\nControl flow is directed through boolean predicates evaluated with `if`, `elif`, and `else` blocks.\n\n```python\nif score >= 90:\n    grade = 'A'\nelif score >= 75:\n    grade = 'B'\nelse:\n    grade = 'C'\n```\n\nAlways adhere to PEP 8 indentation standards with 4 spaces per nesting level.",
    },
    {
        "order_index": 3,
        "title": "Loops",
        "slug": "loops",
        "summary": "Iterative constructs with for, while, break, continue, and loop comprehensions.",
        "lecture_content": "# Iterative Constructs (Loops)\n\nIterate over collections, generators, and ranges using `for` and `while` loops.\n\n```python\n# Bounded range traversal\nfor i in range(5):\n    if i == 2:\n        continue\n    print(i)\n```\n\nUse `break` for premature loop termination and the `for...else` construct to detect uninterrupted iterations.",
    },
    {
        "order_index": 4,
        "title": "Strings",
        "slug": "strings",
        "summary": "String manipulation, slicing, formatting, and unicode encoding.",
        "lecture_content": "# String Operations\n\nStrings in Python are immutable sequences of Unicode characters.\n\n### Core Operations:\n- Slicing: `text[start:stop:step]`\n- Interpolation: Formatted strings `f'Welcome, {user.name}!'`\n- Methods: `.strip()`, `.split()`, `.join()`, `.replace()`, `.find()`.",
    },
    {
        "order_index": 5,
        "title": "Lists",
        "slug": "lists",
        "summary": "Dynamic mutable sequence structures, memory arrays, and list comprehension.",
        "lecture_content": "# Lists & Dynamic Arrays\n\nLists provide ordered, mutable element collections with dynamic resizing.\n\n```python\n# List comprehension for high-performance transformations\nsquares = [x**2 for x in range(10) if x % 2 == 0]\n```\n\nSupports O(1) amortized append and O(1) indexed reads.",
    },
    {
        "order_index": 6,
        "title": "Tuple",
        "slug": "tuple",
        "summary": "Immutable ordered sequences, packing, unpacking, and hashable structures.",
        "lecture_content": "# Tuples\n\nTuples are immutable sequences commonly utilized for read-only records and dictionary keys:\n\n```python\npoint = (10, 20)\nx, y = point  # Tuple unpacking\n```\n\nMemory overhead is lower than lists, and tuples are hashable when their elements are immutable.",
    },
    {
        "order_index": 7,
        "title": "Set",
        "slug": "set",
        "summary": "Unordered unique element collections, mathematical set theory operations.",
        "lecture_content": "# Sets & Hash Sets\n\nSets are mutable, unordered collections of unique, hashable objects.\n\n```python\na = {1, 2, 3}\nb = {3, 4, 5}\nunion = a | b\nintersection = a & b\ndifference = a - b\n```\n\nAverage O(1) time complexity for membership testing (`x in s`).",
    },
    {
        "order_index": 8,
        "title": "Dictionary",
        "slug": "dictionary",
        "summary": "Key-value associative mappings, hash table internals, and lookups.",
        "lecture_content": "# Dictionaries & Hash Maps\n\nAssociative array mapping unique keys to values with O(1) average lookup.\n\n```python\nprofile = {'id': 101, 'name': 'Dev'}\nprofile['role'] = 'Software Engineer'\n```\n\nKeys must be hashable. Dictionaries maintain insertion order as of Python 3.7+.",
    },
    {
        "order_index": 9,
        "title": "Merging Collections",
        "slug": "merging-collections",
        "summary": "Advanced collection combinations, dictionary unpacking, zip, and itertools.",
        "lecture_content": "# Merging Collections\n\nTechniques for combining multiple data structures:\n- Dictionary merge operator: `combined = dict_a | dict_b`\n- Double-splat unpacking: `{**dict_a, **dict_b}`\n- Parallel iteration with `zip(list_a, list_b)`\n- Chained sequences via `itertools.chain(seq1, seq2)`.",
    },
    {
        "order_index": 10,
        "title": "Functions",
        "slug": "functions",
        "summary": "Procedural abstraction, parameter passing, return semantics, and scopes.",
        "lecture_content": "# Modular Functions\n\nReusable procedural logic encapsulated with clear interfaces:\n\n```python\ndef calculate_score(points: float, multiplier: float = 1.0, *bonuses, **metadata) -> float:\n    total = points * multiplier + sum(bonuses)\n    return total\n```\n\nSupports default arguments, variable positional args (`*args`), and keyword arguments (`**kwargs`).",
    },
    {
        "order_index": 11,
        "title": "Lambda Functions",
        "slug": "lambda-functions",
        "summary": "Anonymous inline functions, first-class functions, and functional programming.",
        "lecture_content": "# Lambda Expressions\n\nSingle-expression anonymous functions for higher-order callbacks:\n\n```python\nsort_by_score = sorted(candidates, key=lambda c: c['score'], reverse=True)\neven_numbers = list(filter(lambda x: x % 2 == 0, numbers))\n```",
    },
    {
        "order_index": 12,
        "title": "OOP Concepts",
        "slug": "oop-concepts",
        "summary": "Object-oriented paradigm fundamentals: classes, objects, states, and behaviors.",
        "lecture_content": "# Object-Oriented Programming Fundamentals\n\nClass blueprints combine state (attributes) and behavior (methods):\n\n```python\nclass Student:\n    def __init__(self, name: str, student_id: str):\n        self.name = name\n        self.student_id = student_id\n\n    def get_summary(self) -> str:\n        return f'{self.name} ({self.student_id})'\n```",
    },
    {
        "order_index": 13,
        "title": "Encapsulation",
        "slug": "encapsulation",
        "summary": "Data hiding, access modifiers, public, protected, private attributes, and getters/setters.",
        "lecture_content": "# Encapsulation & Data Hiding\n\nEncapsulate internal representation by controlling member visibility:\n- Public: `self.name`\n- Protected: `self._grade` (convention only)\n- Private: `self.__password` (name-mangled to `_ClassName__password`)\n\nUse `@property` and `@setter` to implement managed attributes.",
    },
    {
        "order_index": 14,
        "title": "Inheritance",
        "slug": "inheritance",
        "summary": "Hierarchical code reuse, single, multiple, multilevel inheritance, and super().",
        "lecture_content": "# Class Inheritance\n\nDeriving specialized subclasses from parent classes:\n\n```python\nclass Admin(User):\n    def __init__(self, email: str, department: str):\n        super().__init__(email=email)\n        self.department = department\n```\n\nPython resolves multiple inheritance hierarchies via the C3 Linearization Method Resolution Order (MRO).",
    },
    {
        "order_index": 15,
        "title": "Polymorphism",
        "slug": "polymorphism",
        "summary": "Method overriding, duck typing, and dynamic operator overloading.",
        "lecture_content": "# Polymorphism\n\nPermitting different classes to be treated through a uniform interface.\n- Duck Typing: 'If it walks like a duck and quacks like a duck, it is a duck.'\n- Method Overriding: Specialized child implementation of a parent method.\n- Operator Overloading: Implementing dunder methods like `__add__` and `__eq__`.",
    },
    {
        "order_index": 16,
        "title": "Abstraction",
        "slug": "abstraction",
        "summary": "Hiding implementation complexity using abstract base classes (ABC) and @abstractmethod.",
        "lecture_content": "# Abstract Base Classes (ABC)\n\nDefine rigorous contracts that derived classes must implement:\n\n```python\nfrom abc import ABC, abstractmethod\n\nclass PaymentGateway(ABC):\n    @abstractmethod\n    def process_payment(self, amount: float) -> bool:\n        pass\n```\n\nAbstract base classes cannot be instantiated directly without implementing all abstract methods.",
    },
    {
        "order_index": 17,
        "title": "Interface",
        "slug": "interface",
        "summary": "Formal interface design, protocol classes, multiple abstract interfaces, and contracts.",
        "lecture_content": "# Interfaces & Protocol Contracts\n\nIn modern Python (3.8+), structural subtyping (static duck typing) is achieved with `typing.Protocol`:\n\n```python\nfrom typing import Protocol\n\nclass Renderable(Protocol):\n    def render(self) -> str:\n        ...\n```\n\nClasses that implement `render(self) -> str` automatically satisfy the `Renderable` protocol without explicit subclassing.",
    },
]


class StudentModuleService:
    """Service governing student sequential curriculum unlocking, completion, and course progression."""

    @classmethod
    def ensure_default_curriculum(cls, course: Course) -> List[Module]:
        """Seeds or ensures all 17 sequential curriculum modules exist for a course."""
        created_modules = []
        for item in CURRICULUM_17_MODULES:
            mod, _ = Module.objects.get_or_create(
                course=course,
                order_index=item["order_index"],
                defaults={
                    "title": item["title"],
                    "slug": item["slug"],
                    "summary": item["summary"],
                    "lecture_content": item["lecture_content"],
                    "passing_percentage": Decimal("80.00"),
                    "is_published": True,
                },
            )
            created_modules.append(mod)
        return sorted(created_modules, key=lambda m: m.order_index)

    @classmethod
    def get_student_courses(cls, student_profile: StudentProfile) -> List[Dict[str, Any]]:
        """List all courses with student-specific enrollment status, progress, and continue pointers."""
        courses = Course.objects.filter(is_deleted=False, is_published=True).order_by("order", "title")
        results = []

        enrollments_by_course = {
            e.course_id: e
            for e in CourseEnrollment.objects.filter(student=student_profile).select_related("course")
        }

        for course in courses:
            enrollment = enrollments_by_course.get(course.id)
            is_enrolled = bool(enrollment and enrollment.status == CourseEnrollment.EnrollmentStatus.ACTIVE)

            total_modules = Module.objects.filter(course=course, is_published=True).count()
            completed_modules = (
                StudentModuleProgress.objects.filter(
                    student=student_profile,
                    module__course=course,
                    status=StudentModuleProgress.ModuleStatus.COMPLETED,
                ).count()
                if is_enrolled
                else 0
            )

            progress_percentage = (
                round((completed_modules / total_modules) * 100, 1) if total_modules > 0 else 0.0
            )

            # Find continue module
            continue_module_id = None
            if is_enrolled:
                active_prog = (
                    StudentModuleProgress.objects.filter(
                        student=student_profile,
                        module__course=course,
                        status__in=[
                            StudentModuleProgress.ModuleStatus.UNLOCKED,
                            StudentModuleProgress.ModuleStatus.IN_PROGRESS,
                        ],
                    )
                    .select_related("module")
                    .order_by("module__order_index")
                    .first()
                )
                if active_prog:
                    continue_module_id = str(active_prog.module.id)
                else:
                    first_mod = (
                        Module.objects.filter(course=course, is_published=True)
                        .order_by("order_index")
                        .first()
                    )
                    if first_mod:
                        continue_module_id = str(first_mod.id)

            results.append(
                {
                    "id": str(course.id),
                    "title": course.title,
                    "slug": course.slug,
                    "description": course.description,
                    "thumbnail_url": course.thumbnail_url,
                    "is_enrolled": is_enrolled,
                    "enrollment_status": enrollment.status if enrollment else None,
                    "completed_modules": completed_modules,
                    "total_modules": total_modules,
                    "progress_percentage": progress_percentage,
                    "continue_module_id": continue_module_id,
                }
            )

        return results

    @classmethod
    def get_student_course_detail(
        cls, student_profile: StudentProfile, course_id: str
    ) -> Dict[str, Any]:
        """Retrieve course details along with the full sequential roadmap of modules and their access states."""
        course = get_object_or_404(Course, id=course_id, is_deleted=False)

        enrollment = CourseEnrollment.objects.filter(
            student=student_profile, course=course
        ).first()

        if not enrollment or enrollment.status != CourseEnrollment.EnrollmentStatus.ACTIVE:
            raise DomainException(
                "You are not actively enrolled in this course.", code="NOT_ENROLLED", status_code=403
            )

        # Ensure default curriculum if course has 0 modules
        modules = list(Module.objects.filter(course=course, is_published=True).order_by("order_index"))
        if not modules:
            modules = cls.ensure_default_curriculum(course)

        # Unlock the very first module if not unlocked yet
        first_module = modules[0]
        first_prog, _ = StudentModuleProgress.objects.get_or_create(
            student=student_profile,
            module=first_module,
            defaults={
                "status": StudentModuleProgress.ModuleStatus.UNLOCKED,
                "unlocked_at": timezone.now(),
            },
        )
        if first_prog.status == StudentModuleProgress.ModuleStatus.LOCKED:
            first_prog.status = StudentModuleProgress.ModuleStatus.UNLOCKED
            first_prog.unlocked_at = timezone.now()
            first_prog.save(update_fields=["status", "unlocked_at", "updated_at"])

        # Fetch all existing progress records for fast lookup
        progress_map = {
            p.module_id: p
            for p in StudentModuleProgress.objects.filter(
                student=student_profile, module__course=course
            )
        }

        module_items = []
        completed_count = 0
        continue_module_id = None

        for idx, mod in enumerate(modules):
            prog = progress_map.get(mod.id)
            prev_mod = modules[idx - 1] if idx > 0 else None
            prev_prog = progress_map.get(prev_mod.id) if prev_mod else None

            # Determine module state based on strict sequential rules
            if prog and prog.status == StudentModuleProgress.ModuleStatus.COMPLETED:
                mod_status = StudentModuleProgress.ModuleStatus.COMPLETED
                completed_count += 1
            elif prog and prog.unlocked_by_override:
                mod_status = prog.status or StudentModuleProgress.ModuleStatus.UNLOCKED
            elif idx == 0:
                mod_status = prog.status if prog else StudentModuleProgress.ModuleStatus.UNLOCKED
            else:
                # Strictly requires preceding module to be COMPLETED
                is_prev_completed = bool(
                    prev_prog and prev_prog.status == StudentModuleProgress.ModuleStatus.COMPLETED
                )
                if is_prev_completed:
                    if not prog:
                        # Auto-initialize unlocked record for convenience
                        prog = StudentModuleProgress.objects.create(
                            student=student_profile,
                            module=mod,
                            status=StudentModuleProgress.ModuleStatus.UNLOCKED,
                            unlocked_at=timezone.now(),
                        )
                        progress_map[mod.id] = prog
                    mod_status = prog.status
                else:
                    mod_status = StudentModuleProgress.ModuleStatus.LOCKED

            is_accessible = mod_status in [
                StudentModuleProgress.ModuleStatus.UNLOCKED,
                StudentModuleProgress.ModuleStatus.IN_PROGRESS,
                StudentModuleProgress.ModuleStatus.COMPLETED,
            ]

            if is_accessible and mod_status != StudentModuleProgress.ModuleStatus.COMPLETED and not continue_module_id:
                continue_module_id = str(mod.id)

            module_items.append(
                {
                    "id": str(mod.id),
                    "order_index": mod.order_index,
                    "title": mod.title,
                    "slug": mod.slug,
                    "summary": mod.summary,
                    "passing_percentage": float(mod.passing_percentage),
                    "status": mod_status,
                    "is_accessible": is_accessible,
                    "score_percentage": float(prog.score_percentage) if prog else 0.0,
                    "completed_at": prog.completed_at.isoformat() if prog and prog.completed_at else None,
                }
            )

        if not continue_module_id and modules:
            continue_module_id = str(modules[0].id)

        total_modules = len(modules)
        progress_percentage = (
            round((completed_count / total_modules) * 100, 1) if total_modules > 0 else 0.0
        )

        return {
            "course": {
                "id": str(course.id),
                "title": course.title,
                "slug": course.slug,
                "description": course.description,
                "thumbnail_url": course.thumbnail_url,
                "total_modules": total_modules,
                "completed_modules": completed_count,
                "progress_percentage": progress_percentage,
                "continue_module_id": continue_module_id,
            },
            "modules": module_items,
        }

    @classmethod
    def get_student_module_detail(
        cls, student_profile: StudentProfile, module_id: str
    ) -> Dict[str, Any]:
        """Fetch individual module lecture notes and assessment details with backend sequential lock enforcement."""
        module = get_object_or_404(
            Module.objects.select_related("course"), id=module_id, is_published=True
        )

        # Check course enrollment
        enrollment = CourseEnrollment.objects.filter(
            student=student_profile, course=module.course
        ).first()

        if not enrollment or enrollment.status != CourseEnrollment.EnrollmentStatus.ACTIVE:
            raise DomainException(
                "You are not actively enrolled in this course.", code="NOT_ENROLLED", status_code=403
            )

        # Sequential authorization check
        is_first = not Module.objects.filter(
            course=module.course, is_published=True, order_index__lt=module.order_index
        ).exists()

        prog = StudentModuleProgress.objects.filter(
            student=student_profile, module=module
        ).first()

        if not is_first:
            prev_mod = (
                Module.objects.filter(
                    course=module.course, is_published=True, order_index__lt=module.order_index
                )
                .order_by("-order_index")
                .first()
            )
            prev_prog = (
                StudentModuleProgress.objects.filter(
                    student=student_profile, module=prev_mod
                ).first()
                if prev_mod
                else None
            )

            is_prev_completed = bool(
                prev_prog and prev_prog.status == StudentModuleProgress.ModuleStatus.COMPLETED
            )
            is_unlocked_or_override = bool(
                prog
                and (
                    prog.status
                    in [
                        StudentModuleProgress.ModuleStatus.UNLOCKED,
                        StudentModuleProgress.ModuleStatus.IN_PROGRESS,
                        StudentModuleProgress.ModuleStatus.COMPLETED,
                    ]
                    or prog.unlocked_by_override
                )
            )

            if not is_prev_completed and not is_unlocked_or_override:
                raise DomainException(
                    f"Module {module.order_index} is locked. You must complete Module {prev_mod.order_index} ({prev_mod.title}) first.",
                    code="MODULE_LOCKED",
                    status_code=403,
                )

        # Ensure progress record is created and transitioned to IN_PROGRESS
        if not prog:
            prog = StudentModuleProgress.objects.create(
                student=student_profile,
                module=module,
                status=StudentModuleProgress.ModuleStatus.IN_PROGRESS,
                unlocked_at=timezone.now(),
            )
        elif prog.status == StudentModuleProgress.ModuleStatus.UNLOCKED:
            prog.status = StudentModuleProgress.ModuleStatus.IN_PROGRESS
            prog.save(update_fields=["status", "updated_at"])

        # Navigation helpers
        prev_module = (
            Module.objects.filter(
                course=module.course, is_published=True, order_index__lt=module.order_index
            )
            .order_by("-order_index")
            .first()
        )
        next_module = (
            Module.objects.filter(
                course=module.course, is_published=True, order_index__gt=module.order_index
            )
            .order_by("order_index")
            .first()
        )

        next_prog = (
            StudentModuleProgress.objects.filter(
                student=student_profile, module=next_module
            ).first()
            if next_module
            else None
        )
        is_next_unlocked = bool(
            next_prog
            and (
                next_prog.status
                in [
                    StudentModuleProgress.ModuleStatus.UNLOCKED,
                    StudentModuleProgress.ModuleStatus.IN_PROGRESS,
                    StudentModuleProgress.ModuleStatus.COMPLETED,
                ]
                or next_prog.unlocked_by_override
            )
        )

        return {
            "id": str(module.id),
            "course_id": str(module.course.id),
            "course_title": module.course.title,
            "order_index": module.order_index,
            "title": module.title,
            "slug": module.slug,
            "summary": module.summary,
            "lecture_content": module.lecture_content,
            "passing_percentage": float(module.passing_percentage),
            "status": prog.status,
            "score_percentage": float(prog.score_percentage),
            "completed_at": prog.completed_at.isoformat() if prog.completed_at else None,
            "prev_module_id": str(prev_module.id) if prev_module else None,
            "next_module_id": str(next_module.id) if next_module else None,
            "is_next_unlocked": is_next_unlocked,
        }

    @classmethod
    @transaction.atomic
    def complete_module(
        cls, student_profile: StudentProfile, module_id: str, score_percentage: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Atomically complete a module, sequentially unlock the next module, and recalculate course progress.
        
        Concurrency Safety:
        Uses select_for_update() on StudentModuleProgress to avoid race conditions.
        Repeated completions are idempotent.
        """
        module = get_object_or_404(
            Module.objects.select_related("course"), id=module_id, is_published=True
        )

        enrollment = CourseEnrollment.objects.filter(
            student=student_profile, course=module.course
        ).first()

        if not enrollment or enrollment.status != CourseEnrollment.EnrollmentStatus.ACTIVE:
            raise DomainException(
                "You are not actively enrolled in this course.", code="NOT_ENROLLED", status_code=403
            )

        # Sequential check: Cannot complete a locked module
        is_first = not Module.objects.filter(
            course=module.course, is_published=True, order_index__lt=module.order_index
        ).exists()

        if not is_first:
            prev_mod = (
                Module.objects.filter(
                    course=module.course, is_published=True, order_index__lt=module.order_index
                )
                .order_by("-order_index")
                .first()
            )
            prev_prog = (
                StudentModuleProgress.objects.filter(
                    student=student_profile, module=prev_mod
                ).first()
                if prev_mod
                else None
            )
            is_prev_completed = bool(
                prev_prog and prev_prog.status == StudentModuleProgress.ModuleStatus.COMPLETED
            )
            prog_check = StudentModuleProgress.objects.filter(
                student=student_profile, module=module
            ).first()
            is_unlocked = bool(
                prog_check
                and (
                    prog_check.status
                    in [
                        StudentModuleProgress.ModuleStatus.UNLOCKED,
                        StudentModuleProgress.ModuleStatus.IN_PROGRESS,
                        StudentModuleProgress.ModuleStatus.COMPLETED,
                    ]
                    or prog_check.unlocked_by_override
                )
            )

            if not is_prev_completed and not is_unlocked:
                raise DomainException(
                    "Cannot complete a locked module. Complete the preceding module first.",
                    code="MODULE_LOCKED",
                    status_code=403,
                )

        # Lock progress record for update
        progress, created = StudentModuleProgress.objects.select_for_update().get_or_create(
            student=student_profile,
            module=module,
            defaults={
                "status": StudentModuleProgress.ModuleStatus.UNLOCKED,
                "unlocked_at": timezone.now(),
            },
        )

        # Idempotent: If already completed, return without double-counting points
        already_completed = progress.status == StudentModuleProgress.ModuleStatus.COMPLETED
        if not already_completed:
            progress.status = StudentModuleProgress.ModuleStatus.COMPLETED
            progress.completed_at = timezone.now()
            progress.score_percentage = score_percentage or Decimal("100.00")
            progress.save(update_fields=["status", "completed_at", "score_percentage", "updated_at"])

            # Award module completion points
            completion_pts = Decimal("50.00")
            ScoreRecord.objects.create(
                student=student_profile,
                source_type=ScoreRecord.SourceType.ASSIGNMENT,
                source_id=module.id,
                points=completion_pts,
                policy_applied=ScoreRecord.ScoringPolicy.FULL,
            )
            student_profile.total_points += completion_pts
            student_profile.save(update_fields=["total_points", "updated_at"])

        # Sequentially unlock the next module
        next_module = (
            Module.objects.filter(
                course=module.course, is_published=True, order_index__gt=module.order_index
            )
            .order_by("order_index")
            .first()
        )

        if next_module:
            next_prog, _ = StudentModuleProgress.objects.select_for_update().get_or_create(
                student=student_profile,
                module=next_module,
                defaults={
                    "status": StudentModuleProgress.ModuleStatus.UNLOCKED,
                    "unlocked_at": timezone.now(),
                },
            )
            if next_prog.status == StudentModuleProgress.ModuleStatus.LOCKED:
                next_prog.status = StudentModuleProgress.ModuleStatus.UNLOCKED
                next_prog.unlocked_at = timezone.now()
                next_prog.save(update_fields=["status", "unlocked_at", "updated_at"])

        # Recalculate course completion percentage
        total_published = Module.objects.filter(course=module.course, is_published=True).count()
        completed_count = StudentModuleProgress.objects.filter(
            student=student_profile,
            module__course=module.course,
            status=StudentModuleProgress.ModuleStatus.COMPLETED,
        ).count()

        course_progress_percentage = (
            round((completed_count / total_published) * 100, 1) if total_published > 0 else 0.0
        )

        if completed_count == total_published and total_published > 0:
            CourseEnrollment.objects.filter(student=student_profile, course=module.course).update(
                status=CourseEnrollment.EnrollmentStatus.COMPLETED,
                completed_at=timezone.now(),
            )

        return {
            "module_id": str(module.id),
            "order_index": module.order_index,
            "title": module.title,
            "status": progress.status,
            "score_percentage": float(progress.score_percentage),
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
            "course_id": str(module.course.id),
            "course_progress_percentage": course_progress_percentage,
            "completed_modules_count": completed_count,
            "total_modules_count": total_published,
            "next_module": {
                "id": str(next_module.id),
                "order_index": next_module.order_index,
                "title": next_module.title,
                "status": "UNLOCKED",
            }
            if next_module
            else None,
        }

