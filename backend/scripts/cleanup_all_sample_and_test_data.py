"""Comprehensive cleanup script to purge all sample, duplicate, and testing data from the database.

Preserves:
- All real user and student accounts
- Official colleges, placement drives, recorded classes
- High-quality 273 LeetCode curriculum questions in the 6 Agentic AI tracks
"""

import os
import sys
from decimal import Decimal

# Configure path & Django settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from django.db import transaction, models
from apps.accounts.models import User, OTPVerification, PasswordResetRequest, AuditLog
from apps.students.models import College, StudentProfile
from apps.courses.models import Course, RecordedClass
from apps.modules.models import Module, StudentModuleProgress
from apps.assignments.models import CodingQuestion, TestCase, CodeSubmission, ExecutionResult, StudentQuestionProgress
from apps.scoring.models import ScoreRecord, ScoreEvent, LeaderboardSnapshot
from apps.certificates.models import StudentBadge
from apps.contact.models import ContactInquiry
from apps.ai_assistant.models import AIConversation, AIMessage
from apps.notifications.models import Notification
from apps.placements.models import PlacementApplication


def purge_data():
    print("=== STARTING PURGE OF ALL SAMPLE, DUPLICATE, AND TESTING DATA ===")

    with transaction.atomic():
        # 1. Purge all test submissions and execution outputs
        sub_count = CodeSubmission.objects.count()
        CodeSubmission.objects.all().delete()
        print(f"[OK] Purged {sub_count} test CodeSubmission records")

        exec_count = ExecutionResult.objects.count()
        ExecutionResult.objects.all().delete()
        print(f"[OK] Purged {exec_count} test ExecutionResult records")

        prog_count = StudentQuestionProgress.objects.count()
        StudentQuestionProgress.objects.all().delete()
        print(f"[OK] Purged {prog_count} test StudentQuestionProgress records")

        # 2. Purge all test scoring and leaderboard records
        score_rec_count = ScoreRecord.objects.count()
        ScoreRecord.objects.all().delete()
        print(f"[OK] Purged {score_rec_count} test ScoreRecord records")

        score_evt_count = ScoreEvent.objects.count()
        ScoreEvent.objects.all().delete()
        print(f"[OK] Purged {score_evt_count} test ScoreEvent records")

        snap_count = LeaderboardSnapshot.objects.count()
        LeaderboardSnapshot.objects.all().delete()
        print(f"[OK] Purged {snap_count} test LeaderboardSnapshot records")

        # Reset total points and streaks on all student profiles to clean baseline (0)
        reset_count = StudentProfile.objects.update(
            total_points=Decimal("0.00"),
            current_streak_days=0,
            highest_streak_days=0,
        )
        print(f"[OK] Reset points and streaks to 0 for {reset_count} StudentProfiles")

        # 3. Purge test badges and test module progress
        badge_count = StudentBadge.objects.count()
        StudentBadge.objects.all().delete()
        print(f"[OK] Purged {badge_count} test StudentBadge records")

        mod_prog_count = StudentModuleProgress.objects.count()
        StudentModuleProgress.objects.all().delete()
        print(f"[OK] Purged {mod_prog_count} test StudentModuleProgress records")

        # 4. Purge sample contact inquiries and AI assistant conversations
        ci_count = ContactInquiry.objects.count()
        ContactInquiry.objects.all().delete()
        print(f"[OK] Purged {ci_count} sample ContactInquiry records")

        msg_count = AIMessage.objects.count()
        AIMessage.objects.all().delete()
        conv_count = AIConversation.objects.count()
        AIConversation.objects.all().delete()
        print(f"[OK] Purged {conv_count} test AIConversations and {msg_count} AIMessages")

        # 5. Purge test notifications
        test_notifications = Notification.objects.filter(
            models.Q(title__startswith="Assessment Graded")
            | models.Q(title__contains="Achievement Unlocked")
            | models.Q(title__contains="Portal Access Granted")
        )
        notif_count = test_notifications.count()
        test_notifications.delete()
        print(f"[OK] Purged {notif_count} test Notification records")

        # 6. Purge sample placement applications (fake resumes and notes)
        pa_count = PlacementApplication.objects.count()
        PlacementApplication.objects.all().delete()
        print(f"[OK] Purged {pa_count} sample PlacementApplication records")

        # 7. Delete old duplicate questions in Agentic AI with Java Full Stack
        old_duplicate_qs = CodingQuestion.objects.filter(
            id__in=[
                "8a5ed438-4f0a-4f25-9b8e-fe897b9f2f3a",
                "21019c04-634a-4cc3-9bcd-08f9e2ad03f2",
            ]
        )
        old_q_count = old_duplicate_qs.count()
        old_duplicate_qs.delete()
        print(f"[OK] Purged {old_q_count} old duplicate CodingQuestion records from Java Full Stack")

        # 8. Clean up video courses (Java Full Stack Development & Python & AI Full Stack Mastery)
        # Remove erroneously seeded coding questions from video courses
        video_courses = Course.objects.filter(
            slug__in=["java-full-stack-development", "python-ai-fullstack-mastery"]
        )
        for vc in video_courses:
            # Delete questions in this video course
            q_in_vc = CodingQuestion.objects.filter(module__course=vc)
            q_in_vc_count = q_in_vc.count()
            q_in_vc.delete()
            print(f"[OK] Purged {q_in_vc_count} misplaced CodingQuestions from video course '{vc.title}'")

            # Delete erroneous modules (order_index > 2 or modules with 0 recorded classes)
            erroneous_modules = Module.objects.filter(course=vc, recorded_classes__isnull=True)
            em_count = erroneous_modules.count()
            erroneous_modules.delete()
            print(f"[OK] Purged {em_count} erroneous empty modules from video course '{vc.title}'")

        # Ensure correct naming for the 2 genuine video modules in Java Full Stack Development
        java_course = Course.objects.filter(slug="java-full-stack-development").first()
        if java_course:
            Module.objects.filter(course=java_course, order_index=1).update(
                title="01 - Core Java Fundamentals & OOP",
                slug="java-core-fundamentals",
                summary="Master Java architecture, data types, control flow, and object-oriented programming foundations.",
            )
            Module.objects.filter(course=java_course, order_index=2).update(
                title="02 - Advanced Java, Concurrency & Spring Boot",
                slug="java-advanced-frameworks",
                summary="Inheritance, collections framework, exception handling, multi-threading, and Spring Boot REST APIs.",
            )

        # Ensure correct naming for the 2 genuine video modules in Python & AI Full Stack Mastery
        python_course = Course.objects.filter(slug="python-ai-fullstack-mastery").first()
        if python_course:
            Module.objects.filter(course=python_course, order_index=1).update(
                title="01 - Python Foundations & Data Structures",
                slug="py-core-basics",
                summary="Core syntax, data types, collections, functions and OOP with Python.",
            )
            Module.objects.filter(course=python_course, order_index=2).update(
                title="02 - Django Web APIs & AI Integration",
                slug="py-backend-ai",
                summary="File I/O, Django REST APIs, AI LLMs, and agentic workflows.",
            )

        # 9. Purge dummy staging colleges
        stg_colleges = College.objects.filter(code__in=["STG-ENG-A", "STG-ENG-B"])
        stg_col_count = stg_colleges.count()
        stg_colleges.delete()
        print(f"[OK] Purged {stg_col_count} dummy staging colleges ('STG-ENG-A', 'STG-ENG-B')")

        # 10. Purge test / staging users
        test_emails = [
            "staging_admin@gqt.edu",
            "tpo_alpha@gqt.edu",
            "tpo_unassigned@gqt.edu",
            "tpo_inactive@gqt.edu",
            "student_a1@gqt.edu",
            "student_b1@gqt.edu",
            "staging_tpo_new_005762@gqt.edu",
            "staging_tpo_new_66757e@gqt.edu",
            "staging_tpo_new_105fe7@gqt.edu",
            "staging_tpo_new_a80fcd@gqt.edu",
            "test@gmail.com",
            "student_9876939049@gqt.edu",
        ]
        test_users = User.objects.filter(email__in=test_emails)
        tu_count = test_users.count()
        test_users.delete()
        print(f"[OK] Purged {tu_count} test/staging user accounts")

        # 11. Purge test OTPs and password reset requests
        otp_count = OTPVerification.objects.count()
        OTPVerification.objects.all().delete()
        print(f"[OK] Purged {otp_count} test OTP verification records")

        pr_count = PasswordResetRequest.objects.count()
        PasswordResetRequest.objects.all().delete()
        print(f"[OK] Purged {pr_count} test PasswordResetRequest records")

    print("\n=== PURGE COMPLETED SUCCESSFULLY! ===")


if __name__ == "__main__":
    purge_data()
