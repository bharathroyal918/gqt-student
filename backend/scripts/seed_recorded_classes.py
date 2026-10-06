import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
import django
django.setup()

from apps.accounts.models import User
from apps.courses.models import Course, CourseEnrollment, RecordedClass
from apps.modules.models import Module
from apps.students.models import StudentProfile

def seed_recorded_classes():
    admin = User.objects.filter(role="ADMIN").first()
    student = StudentProfile.objects.first()

    # 1. Java Full Stack Course
    java_course, _ = Course.objects.get_or_create(
        slug="java-full-stack-development",
        defaults={
            "title": "Java Full Stack Development",
            "description": "Master Core Java, Advanced Java, Spring Boot, Hibernate, and React frontend integration from scratch.",
            "is_published": True,
            "order": 1,
            "created_by": admin,
        }
    )
    java_course.is_published = True
    java_course.save()

    # Create Module Folders / Components for Java Course
    java_mod1, _ = Module.objects.get_or_create(
        course=java_course,
        slug="java-core-fundamentals",
        defaults={
            "title": "01 - Core Java Fundamentals & OOP",
            "order_index": 1,
            "summary": "Master Java architecture, data types, control flow, and object-oriented programming foundations.",
            "is_published": True,
        }
    )
    java_mod2, _ = Module.objects.get_or_create(
        course=java_course,
        slug="java-advanced-frameworks",
        defaults={
            "title": "02 - Advanced Java, Concurrency & Spring Boot",
            "order_index": 2,
            "summary": "Inheritance, collections framework, exception handling, multi-threading, and Spring Boot REST APIs.",
            "is_published": True,
        }
    )

    # Create 8 sequential recorded videos for Java course partitioned into modules
    java_lessons = [
        ("Lec-01: Introduction to Java & JVM Architecture", "https://www.youtube.com/watch?v=eIrMbAQSU34", "38:45", "Overview of JVM, JRE, JDK, bytecode compilation and memory areas.", java_mod1),
        ("Lec-02: Java Variables, Data Types & Operators", "https://www.youtube.com/watch?v=eIrMbAQSU34", "45:10", "Primitive vs reference types, type casting, arithmetic and logical operators.", java_mod1),
        ("Lec-03: Control Flow Statements & Loops", "https://www.youtube.com/watch?v=eIrMbAQSU34", "42:30", "If-else conditions, switch expressions, for/while/do-while loops and break/continue.", java_mod1),
        ("Lec-04: Object-Oriented Programming: Classes & Objects", "https://www.youtube.com/watch?v=eIrMbAQSU34", "52:15", "Constructors, instance variables, methods, encapsulation and access modifiers.", java_mod1),
        ("Lec-05: Inheritance, Polymorphism & Interfaces", "https://www.youtube.com/watch?v=eIrMbAQSU34", "49:20", "Method overriding, super keyword, abstract classes, and multiple inheritance via interfaces.", java_mod2),
        ("Lec-06: Java Collections Framework & Generics", "https://www.youtube.com/watch?v=eIrMbAQSU34", "58:00", "ArrayList, LinkedList, HashSet, HashMap, Iterators, and generic type constraints.", java_mod2),
        ("Lec-07: Exception Handling & Multi-Threading", "https://www.youtube.com/watch?v=eIrMbAQSU34", "54:40", "Try-catch-finally, custom exceptions, Thread class, Runnable interface and synchronization.", java_mod2),
        ("Lec-08: Spring Boot REST APIs & CRUD Operations", "https://www.youtube.com/watch?v=eIrMbAQSU34", "65:00", "Building RESTful controllers, service layer, Spring Data JPA repositories, and MySQL connectivity.", java_mod2),
    ]

    for idx, (title, yt_url, duration, notes, mod_obj) in enumerate(java_lessons, start=1):
        slug = f"java-lesson-{idx:02d}"
        rec, _ = RecordedClass.objects.update_or_create(
            course=java_course,
            slug=slug,
            defaults={
                "module": mod_obj,
                "title": title,
                "order_index": idx,
                "video_source_type": RecordedClass.VideoSourceType.YOUTUBE,
                "youtube_url": yt_url,
                "duration_formatted": duration,
                "duration_seconds": 2400,
                "notes": notes,
                "is_published": True,
                "is_preview": bool(idx <= 5),
                "created_by": admin,
            }
        )

    # 2. Python & AI Full Stack Course
    python_course, _ = Course.objects.get_or_create(
        slug="python-ai-fullstack-mastery",
        defaults={
            "title": "Python & AI Full Stack Mastery",
            "description": "Complete Python programming, Django REST framework, PostgreSQL, and AI model integration.",
            "is_published": True,
            "order": 2,
            "created_by": admin,
        }
    )
    python_course.is_published = True
    python_course.save()

    # Create Module Folders / Components for Python Course
    py_mod1, _ = Module.objects.get_or_create(
        course=python_course,
        slug="py-core-basics",
        defaults={
            "title": "01 - Python Foundations & Data Structures",
            "order_index": 1,
            "summary": "Core syntax, data types, collections, functions and OOP with Python.",
            "is_published": True,
        }
    )
    py_mod2, _ = Module.objects.get_or_create(
        course=python_course,
        slug="py-backend-ai",
        defaults={
            "title": "02 - Django Web APIs & AI Integration",
            "order_index": 2,
            "summary": "File I/O, Django REST APIs, AI LLMs, and agentic workflows.",
            "is_published": True,
        }
    )

    python_lessons = [
        ("Lec-01: Python Environment Setup & Basic Syntax", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "30:00", "Installing Python, virtual environments, variables, data types, and input/output.", py_mod1),
        ("Lec-02: Python Data Structures: Lists, Tuples & Dictionaries", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "44:20", "List comprehensions, dictionary methods, sets, and immutability concepts.", py_mod1),
        ("Lec-03: Functions, Lambdas & Modular Programming", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "40:15", "Args/kwargs, lambda functions, map/filter/reduce, and custom modules.", py_mod1),
        ("Lec-04: Object-Oriented Python & Dunder Methods", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "50:00", "Classes, inheritance, polymorphism, magic methods (__init__, __str__, __repr__).", py_mod1),
        ("Lec-05: File I/O, JSON & Error Handling", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "42:00", "Context managers with statement, exception hierarchies, reading and writing CSV/JSON.", py_mod2),
        ("Lec-06: Django Web Framework & REST API Building", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "60:00", "Django apps, models, ORM migrations, DRF serializers, and viewsets.", py_mod2),
        ("Lec-07: Integrating AI APIs & LLMs with Python", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "55:00", "Building intelligent assistants using Gemini/OpenAI APIs and vector embeddings.", py_mod2),
    ]

    for idx, (title, yt_url, duration, notes, mod_obj) in enumerate(python_lessons, start=1):
        slug = f"python-lesson-{idx:02d}"
        rec, _ = RecordedClass.objects.update_or_create(
            course=python_course,
            slug=slug,
            defaults={
                "module": mod_obj,
                "title": title,
                "order_index": idx,
                "video_source_type": RecordedClass.VideoSourceType.YOUTUBE,
                "youtube_url": yt_url,
                "duration_formatted": duration,
                "duration_seconds": 2400,
                "notes": notes,
                "is_published": True,
                "is_preview": bool(idx <= 5),
                "created_by": admin,
            }
        )

    # Enroll student in Java course only (so Python course demonstrates the locked video #6+ preview logic!)
    if student:
        CourseEnrollment.objects.get_or_create(
            student=student,
            course=java_course,
            defaults={"status": CourseEnrollment.EnrollmentStatus.ACTIVE}
        )

    print(">>> Demo Recorded Classes with Folder Components successfully seeded! <<<")
    print(f"Java Course: {RecordedClass.objects.filter(course=java_course).count()} lessons across {Module.objects.filter(course=java_course).count()} folders")
    print(f"Python Course: {RecordedClass.objects.filter(course=python_course).count()} lessons across {Module.objects.filter(course=python_course).count()} folders")

if __name__ == "__main__":
    seed_recorded_classes()
