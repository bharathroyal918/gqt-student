"""Comprehensive test suite for Recorded Classes, student preview locks, and admin allocations."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import (
    Course,
    CourseEnrollment,
    RecordedClass,
    StudentRecordedClassProgress,
)
from apps.students.models import StudentProfile

User = get_user_model()


class RecordedClassesAPITests(APITestCase):
    """Test suite for Recorded Classes access control and admin management."""

    def setUp(self):
        # Admin User
        self.admin_user = User.objects.create_superuser(
            email="admin.classes@gqt.local",
            password="AdminPassword123!",
            role="ADMIN",
        )

        # Enrolled Student
        self.enrolled_user = User.objects.create_user(
            email="enrolled.student@gqt.local",
            password="Password123!",
            role="STUDENT",
        )
        self.enrolled_student = StudentProfile.objects.create(
            user=self.enrolled_user,
            student_id_number="GQT-REC-001",
            full_name="Enrolled Alice",
            batch_code="JAVA-2026-A",
        )

        # Un-enrolled Student (Registered student only)
        self.unenrolled_user = User.objects.create_user(
            email="unenrolled.student@gqt.local",
            password="Password123!",
            role="STUDENT",
        )
        self.unenrolled_student = StudentProfile.objects.create(
            user=self.unenrolled_user,
            student_id_number="GQT-REC-002",
            full_name="Unenrolled Bob",
            batch_code="PYTHON-2026-B",
        )

        # Java Course
        self.java_course = Course.objects.create(
            title="Java Full Stack Mastery",
            slug="java-full-stack-mastery",
            description="Complete Enterprise Java Curriculum with Spring Boot and React",
            is_published=True,
            order=1,
        )

        # Enroll Enrolled Student in Java Course
        self.java_enrollment = CourseEnrollment.objects.create(
            student=self.enrolled_student,
            course=self.java_course,
            status=CourseEnrollment.EnrollmentStatus.ACTIVE,
        )

        # Create 8 sequential recorded videos in Java Course
        self.videos = []
        for i in range(1, 9):
            video = RecordedClass.objects.create(
                course=self.java_course,
                title=f"Lesson {i:02d}: Java Module Topic {i}",
                slug=f"java-lesson-{i:02d}",
                description=f"Detailed syllabus coverage for lesson {i}",
                order_index=i,
                video_source_type=RecordedClass.VideoSourceType.YOUTUBE,
                youtube_url=f"https://www.youtube.com/watch?v=dQw4w9WgXc{i}",
                youtube_video_id=f"dQw4w9WgXc{i}",
                duration_seconds=1800,
                duration_formatted="30:00",
                notes=f"Key notes for lesson {i}",
                is_published=True,
            )
            self.videos.append(video)

    def test_student_recorded_courses_catalog(self):
        """Any registered student can view the courses catalog with preview info and enrollment badges."""
        self.client.force_authenticate(user=self.unenrolled_user)
        url = reverse("api_v1:student_recorded_classes:catalog")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()["data"]["courses"]
        self.assertEqual(len(data), 1)
        course_data = data[0]
        self.assertEqual(course_data["title"], "Java Full Stack Mastery")
        self.assertEqual(course_data["total_videos"], 8)
        self.assertEqual(course_data["preview_videos_count"], 5)
        self.assertFalse(course_data["is_enrolled"])
        self.assertFalse(course_data["has_full_access"])

        # Check for enrolled student
        self.client.force_authenticate(user=self.enrolled_user)
        response = self.client.get(url)
        data = response.json()["data"]["courses"]
        self.assertTrue(data[0]["is_enrolled"])
        self.assertTrue(data[0]["has_full_access"])

    def test_first_5_videos_unrestricted_preview_for_unenrolled_student(self):
        """Un-enrolled students can preview videos 1 to 5, but videos 6+ are marked is_locked=True with streaming data omitted."""
        self.client.force_authenticate(user=self.unenrolled_user)
        url = reverse(
            "api_v1:student_recorded_classes:course_playlist",
            kwargs={"course_id": self.java_course.id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.json()["data"]
        videos = res_data["videos"]
        self.assertEqual(len(videos), 8)

        # Videos 1 to 5 must be UNLOCKED with full streaming metadata
        for v in videos[:5]:
            self.assertFalse(
                v["is_locked"],
                f"Video #{v['order_index']} should be unlocked free preview",
            )
            self.assertTrue(v["is_preview"])
            self.assertIsNotNone(v["video_source_type"])
            self.assertNotEqual(v["video_source_type"], "LOCKED")
            self.assertIn("dQw4w9WgXc", v["youtube_video_id"])

        # Videos 6 to 8 must be LOCKED with streaming URLs stripped
        for v in videos[5:]:
            self.assertTrue(
                v["is_locked"],
                f"Video #{v['order_index']} must be locked for unenrolled students",
            )
            self.assertEqual(v["video_source_type"], "LOCKED")
            self.assertEqual(v["youtube_video_id"], "")
            self.assertEqual(v["youtube_url"], "")
            self.assertEqual(v["video_url"], "")
            self.assertEqual(v["lock_reason"], "ENROLLMENT_REQUIRED")

    def test_enrolled_student_has_all_videos_unlocked(self):
        """Enrolled / approved students have all videos unlocked without restrictions."""
        self.client.force_authenticate(user=self.enrolled_user)
        url = reverse(
            "api_v1:student_recorded_classes:course_playlist",
            kwargs={"course_id": self.java_course.id},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        videos = response.json()["data"]["videos"]
        for v in videos:
            self.assertFalse(
                v["is_locked"],
                f"Enrolled student should have video #{v['order_index']} unlocked",
            )
            self.assertNotEqual(v["video_source_type"], "LOCKED")
            self.assertIn("dQw4w9WgXc", v["youtube_video_id"])

    def test_stream_video_endpoint_permission_boundary(self):
        """Direct stream endpoint returns 403 Forbidden for locked video 6 when accessed by un-enrolled student."""
        video_3 = self.videos[2]  # Lesson 3 (Preview)
        video_7 = self.videos[6]  # Lesson 7 (Restricted)

        self.client.force_authenticate(user=self.unenrolled_user)

        # Video 3 (Free Preview) should be 200 OK
        url_v3 = reverse(
            "api_v1:student_recorded_classes:video_stream",
            kwargs={"course_id": self.java_course.id, "video_id": video_3.id},
        )
        res_v3 = self.client.get(url_v3)
        self.assertEqual(res_v3.status_code, status.HTTP_200_OK)
        self.assertEqual(res_v3.json()["data"]["title"], video_3.title)

        # Video 7 (Restricted) should be 403 FORBIDDEN
        url_v7 = reverse(
            "api_v1:student_recorded_classes:video_stream",
            kwargs={"course_id": self.java_course.id, "video_id": video_7.id},
        )
        res_v7 = self.client.get(url_v7)
        self.assertEqual(res_v7.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res_v7.json()["error"]["code"], "COURSE_ENROLLMENT_REQUIRED")

        # Now authenticate as enrolled student -> Video 7 is 200 OK
        self.client.force_authenticate(user=self.enrolled_user)
        res_v7_enrolled = self.client.get(url_v7)
        self.assertEqual(res_v7_enrolled.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res_v7_enrolled.json()["data"]["youtube_video_id"], video_7.youtube_video_id
        )

    def test_student_video_progress_tracking(self):
        """Students can record playback time position and mark video as completed."""
        video_1 = self.videos[0]
        self.client.force_authenticate(user=self.enrolled_user)
        url = reverse(
            "api_v1:student_recorded_classes:video_progress",
            kwargs={"course_id": self.java_course.id, "video_id": video_1.id},
        )

        response = self.client.post(
            url, {"last_position_seconds": 450, "is_completed": True}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        progress = StudentRecordedClassProgress.objects.get(
            student=self.enrolled_student, recorded_class=video_1
        )
        self.assertEqual(progress.last_position_seconds, 450)
        self.assertTrue(progress.is_completed)
        self.assertIsNotNone(progress.completed_at)

    def test_admin_create_and_manage_recorded_classes(self):
        """Admin can create new recorded classes with YouTube link or direct video, and reorder sequence."""
        self.client.force_authenticate(user=self.admin_user)

        # 1. Create with YouTube link
        url_create = reverse(
            "api_v1:admin_courses:recorded_classes_list_create",
            kwargs={"course_id": self.java_course.id},
        )
        payload = {
            "title": "Lesson 09: Spring Boot REST Architecture",
            "video_source_type": "YOUTUBE",
            "youtube_url": "https://youtu.be/kJQP7kiw5Fk",
            "duration_seconds": 2400,
            "notes": "Spring Boot controller and services overview",
        }
        res_create = self.client.post(url_create, payload, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        created_video = res_create.json()["data"]
        self.assertEqual(created_video["youtube_video_id"], "kJQP7kiw5Fk")
        self.assertEqual(created_video["duration_formatted"], "40:00")
        self.assertEqual(created_video["order_index"], 9)

        # 2. Reorder classes
        url_reorder = reverse(
            "api_v1:admin_courses:recorded_classes_reorder",
            kwargs={"course_id": self.java_course.id},
        )
        reorder_payload = {
            "order_items": [
                {"id": str(self.videos[0].id), "order_index": 2},
                {"id": str(self.videos[1].id), "order_index": 1},
            ]
        }
        res_reorder = self.client.post(url_reorder, reorder_payload, format="json")
        self.assertEqual(res_reorder.status_code, status.HTTP_200_OK)

        self.videos[0].refresh_from_db()
        self.videos[1].refresh_from_db()
        self.assertEqual(self.videos[0].order_index, 2)
        self.assertEqual(self.videos[1].order_index, 1)

    def test_admin_allocate_course_enrollment(self):
        """Admin can allocate / approve course enrollment for un-enrolled students and revoke access."""
        self.client.force_authenticate(user=self.admin_user)

        # Allocate Un-enrolled Bob into Java Course
        url_allocate = reverse(
            "api_v1:admin_courses:enrollments_allocate",
            kwargs={"course_id": self.java_course.id},
        )
        res_alloc = self.client.post(
            url_allocate, {"student_id": str(self.unenrolled_student.id)}, format="json"
        )
        self.assertEqual(res_alloc.status_code, status.HTTP_201_CREATED)

        # Now Bob has full access to all 8 videos
        self.client.force_authenticate(user=self.unenrolled_user)
        url_stream = reverse(
            "api_v1:student_recorded_classes:video_stream",
            kwargs={"course_id": self.java_course.id, "video_id": self.videos[6].id},
        )
        res_stream = self.client.get(url_stream)
        self.assertEqual(res_stream.status_code, status.HTTP_200_OK)

        # Admin revokes Bob's enrollment
        self.client.force_authenticate(user=self.admin_user)
        url_revoke = reverse(
            "api_v1:admin_courses:enrollments_revoke",
            kwargs={
                "course_id": self.java_course.id,
                "student_id": self.unenrolled_student.id,
            },
        )
        res_revoke = self.client.post(url_revoke)
        self.assertEqual(res_revoke.status_code, status.HTTP_200_OK)

        # Now Bob is restricted again on video 7
        self.client.force_authenticate(user=self.unenrolled_user)
        res_stream_revoked = self.client.get(url_stream)
        self.assertEqual(res_stream_revoked.status_code, status.HTTP_403_FORBIDDEN)
