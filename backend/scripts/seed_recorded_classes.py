import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
import django
django.setup()

from apps.accounts.models import User
from apps.courses.models import Course, CourseEnrollment, RecordedClass
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

    # Create 8 sequential recorded videos for Java course
    java_lessons = [
        ("01 - Introduction to Java & JVM Architecture", "https://www.youtube.com/watch?v=eIrMbAQSU34", "38:45", "Overview of JVM, JRE, JDK, bytecode compilation and memory areas."),
        ("02 - Java Variables, Data Types & Operators", "https://www.youtube.com/watch?v=eIrMbAQSU34", "45:10", "Primitive vs reference types, type casting, arithmetic and logical operators."),
        ("03 - Control Flow Statements & Loops", "https://www.youtube.com/watch?v=eIrMbAQSU34", "42:30", "If-else conditions, switch expressions, for/while/do-while loops and break/continue."),
        ("04 - Object-Oriented Programming: Classes & Objects", "https://www.youtube.com/watch?v=eIrMbAQSU34", "52:15", "Constructors, instance variables, methods, encapsulation and access modifiers."),
        ("05 - Inheritance, Polymorphism & Interfaces", "https://www.youtube.com/watch?v=eIrMbAQSU34", "49:20", "Method overriding, super keyword, abstract classes, and multiple inheritance via interfaces."),
        ("06 - Java Collections Framework & Generics", "https://www.youtube.com/watch?v=eIrMbAQSU34", "58:00", "ArrayList, LinkedList, HashSet, HashMap, Iterators, and generic type constraints."),
        ("07 - Exception Handling & Multi-Threading", "https://www.youtube.com/watch?v=eIrMbAQSU34", "54:40", "Try-catch-finally, custom exceptions, Thread class, Runnable interface and synchronization."),
        ("08 - Spring Boot REST APIs & CRUD Operations", "https://www.youtube.com/watch?v=eIrMbAQSU34", "65:00", "Building RESTful controllers, service layer, Spring Data JPA repositories, and MySQL connectivity."),
    ]

    for idx, (title, yt_url, duration, notes) in enumerate(java_lessons, start=1):
        slug = f"java-lesson-{idx:02d}"
        rec, _ = RecordedClass.objects.update_or_create(
            course=java_course,
            slug=slug,
            defaults={
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

    python_lessons = [
        ("01 - Python Environment Setup & Basic Syntax", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "30:00", "Installing Python, virtual environments, variables, data types, and input/output."),
        ("02 - Python Data Structures: Lists, Tuples & Dictionaries", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "44:20", "List comprehensions, dictionary methods, sets, and immutability concepts."),
        ("03 - Functions, Lambdas & Modular Programming", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "40:15", "Args/kwargs, lambda functions, map/filter/reduce, and custom modules."),
        ("04 - Object-Oriented Python & Dunder Methods", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "50:00", "Classes, inheritance, polymorphism, magic methods (__init__, __str__, __repr__)."),
        ("05 - File I/O, JSON & Error Handling", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "42:00", "Context managers with statement, exception hierarchies, reading and writing CSV/JSON."),
        ("06 - Django Web Framework & REST API Building", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "60:00", "Django apps, models, ORM migrations, DRF serializers, and viewsets."),
        ("07 - Integrating AI APIs & LLMs with Python", "https://www.youtube.com/watch?v=kqtD5dpn9C8", "55:00", "Building intelligent assistants using Gemini/OpenAI APIs and vector embeddings."),
    ]

    for idx, (title, yt_url, duration, notes) in enumerate(python_lessons, start=1):
        slug = f"python-lesson-{idx:02d}"
        rec, _ = RecordedClass.objects.update_or_create(
            course=python_course,
            slug=slug,
            defaults={
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

    print(">>> Demo Recorded Classes successfully seeded! <<<")
    print(f"Java Course: {RecordedClass.objects.filter(course=java_course).count()} lessons (Student Enrolled - Full Access)")
    print(f"Python Course: {RecordedClass.objects.filter(course=python_course).count()} lessons (Student NOT Enrolled - First 5 Lessons Free Preview)")

if __name__ == "__main__":
    seed_recorded_classes()
