"""Comprehensive test suite for Student AI Consultation API & Services."""

import uuid
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.ai_assistant.models import AIConversation, AIMessage
from apps.ai_assistant.providers.base import AIProviderResult, BaseAIProvider
from apps.ai_assistant.services import AIService, safe_scrub_secrets
from apps.students.models import StudentProfile

User = get_user_model()


class MockCustomAIProvider(BaseAIProvider):
    """Predictable mock AI provider for testing."""

    def __init__(self):
        self.call_history = []

    def generate_response(self, messages, system_prompt, context=None, **kwargs):
        self.call_history.append({"messages": messages, "system_prompt": system_prompt, "context": context})
        last_msg = messages[-1]["content"] if messages else ""
        return AIProviderResult(
            content=f"Mock AI tutor response to: {last_msg}",
            tokens_used=42,
            model_name="mock-tutor-v1",
        )


class AIAssistantApiTests(APITestCase):
    """Test suite covering AI Help API endpoints, ownership isolation, and rate limiting."""

    def setUp(self):
        cache.clear()

        # Student A
        self.user_a = User.objects.create_user(
            email="student.a@gqt.local", password="Password123!", role=User.RoleChoices.STUDENT
        )
        self.student_a = StudentProfile.objects.create(
            user=self.user_a,
            student_id_number="GQT-AI-001",
            full_name="Alice AI Tester",
            batch_code="BATCH-2026-AI",
        )

        # Student B
        self.user_b = User.objects.create_user(
            email="student.b@gqt.local", password="Password123!", role=User.RoleChoices.STUDENT
        )
        self.student_b = StudentProfile.objects.create(
            user=self.user_b,
            student_id_number="GQT-AI-002",
            full_name="Bob Unauthorized",
            batch_code="BATCH-2026-AI",
        )

    def test_list_and_create_conversation(self):
        """Student creates a consultation and lists active conversations."""
        self.client.force_authenticate(user=self.user_a)

        # 1. Create a new conversation
        create_res = self.client.post(
            "/api/v1/students/ai/conversations/",
            {"title": "Understanding Python Decorators", "initial_message": "What is a decorator?"},
            format="json",
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        conv_id = create_res.json()["data"]["id"]

        # Verify messages inside the created conversation
        messages = create_res.json()["data"]["messages"]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["sender"], "STUDENT")
        self.assertEqual(messages[1]["sender"], "ASSISTANT")

        # 2. List conversations
        list_res = self.client.get("/api/v1/students/ai/conversations/")
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        items = list_res.json()["data"]["conversations"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], conv_id)
        self.assertEqual(items[0]["messages_count"], 2)

    def test_conversation_ownership_isolation(self):
        """Student A's conversation cannot be accessed or modified by Student B."""
        conv_a = AIConversation.objects.create(
            student=self.student_a,
            title="Private Python Consultation",
        )
        AIMessage.objects.create(
            conversation=conv_a,
            sender=AIMessage.SenderChoices.STUDENT,
            content="Sensitive question about code",
        )

        # Student B attempts to read Student A's conversation
        self.client.force_authenticate(user=self.user_b)
        get_res = self.client.get(f"/api/v1/students/ai/conversations/{conv_a.id}/")
        self.assertIn(get_res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Student B attempts to send message to Student A's conversation
        send_res = self.client.post(
            f"/api/v1/students/ai/conversations/{conv_a.id}/messages/",
            {"content": "Unauthorized prompt injection"},
            format="json",
        )
        self.assertIn(send_res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

        # Student B's conversation list is empty
        list_b = self.client.get("/api/v1/students/ai/conversations/")
        self.assertEqual(len(list_b.json()["data"]["conversations"]), 0)

    def test_send_message_and_auto_title_update(self):
        """Posting a message updates the conversation and triggers SmartTutor response."""
        self.client.force_authenticate(user=self.user_a)

        conv = AIConversation.objects.create(
            student=self.student_a,
            title="New Consultation",
        )

        res = self.client.post(
            f"/api/v1/students/ai/conversations/{conv.id}/messages/",
            {"content": "How do I fix a RecursionError in Python?"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res_data = res.json()["data"]
        self.assertEqual(res_data["sender"], "ASSISTANT")
        self.assertIn("RecursionError", res_data["content"])

        # Verify auto-title updated
        conv.refresh_from_db()
        self.assertNotEqual(conv.title, "New Consultation")
        self.assertIn("recursionerror", conv.title.lower())

    def test_message_validation(self):
        """Empty messages or oversized messages are rejected."""
        self.client.force_authenticate(user=self.user_a)
        conv = AIConversation.objects.create(
            student=self.student_a,
            title="Validation Test",
        )

        # Empty content
        res_empty = self.client.post(
            f"/api/v1/students/ai/conversations/{conv.id}/messages/",
            {"content": "   "},
            format="json",
        )
        self.assertEqual(res_empty.status_code, status.HTTP_400_BAD_REQUEST)

        # Oversized content
        res_huge = self.client.post(
            f"/api/v1/students/ai/conversations/{conv.id}/messages/",
            {"content": "A" * 4001},
            format="json",
        )
        self.assertEqual(res_huge.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retry_message_flow(self):
        """Student can retry the last AI response."""
        self.client.force_authenticate(user=self.user_a)
        conv = AIConversation.objects.create(
            student=self.student_a,
            title="Retry Test",
        )
        AIMessage.objects.create(
            conversation=conv,
            sender=AIMessage.SenderChoices.STUDENT,
            content="Explain polymorphism in Python OOP",
        )
        AIMessage.objects.create(
            conversation=conv,
            sender=AIMessage.SenderChoices.ASSISTANT,
            content="Initial brief reply",
        )

        retry_res = self.client.post(
            f"/api/v1/students/ai/conversations/{conv.id}/retry/",
            {},
            format="json",
        )
        self.assertEqual(retry_res.status_code, status.HTTP_200_OK)
        new_msg = retry_res.json()["data"]
        self.assertEqual(new_msg["sender"], "ASSISTANT")
        self.assertIn("Polymorphism", new_msg["content"])
        self.assertEqual(conv.messages.count(), 3)

    def test_archive_conversation(self):
        """Archiving conversation removes it from active list and blocks further access."""
        self.client.force_authenticate(user=self.user_a)
        conv = AIConversation.objects.create(
            student=self.student_a,
            title="To Archive",
        )

        del_res = self.client.delete(f"/api/v1/students/ai/conversations/{conv.id}/")
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)

        conv.refresh_from_db()
        self.assertTrue(conv.is_archived)

        # Further retrieval gives 404
        get_res = self.client.get(f"/api/v1/students/ai/conversations/{conv.id}/")
        self.assertEqual(get_res.status_code, status.HTTP_404_NOT_FOUND)

    def test_rate_limiting_enforcement(self):
        """Exceeding requests per minute raises 429 Too Many Requests."""
        self.client.force_authenticate(user=self.user_a)
        conv = AIConversation.objects.create(
            student=self.student_a,
            title="Rate Limit Test",
        )

        # Artificially set cache counter to max
        cache.set(f"ai_rate_limit_{self.student_a.id}", 30, timeout=60)

        res = self.client.post(
            f"/api/v1/students/ai/conversations/{conv.id}/messages/",
            {"content": "Are you still there?"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        err_msg = res.json().get("error", {}).get("message", "")
        self.assertIn("Rate limit", err_msg)

    def test_secret_scrubbing_utility(self):
        """Secrets like OpenAI API keys and Bearer tokens are scrubbed from log strings."""
        raw_text = "Error sk-proj-1234567890abcdef1234567890 and Bearer eyJhbGciOiJIUzI1Ni.secret and AIzaSy1234567890abcdef1234567890"
        scrubbed = safe_scrub_secrets(raw_text)
        self.assertNotIn("sk-proj-1234567890abcdef1234567890", scrubbed)
        self.assertNotIn("AIzaSy1234567890abcdef1234567890", scrubbed)
        self.assertIn("sk-***", scrubbed)
        self.assertIn("Bearer ***", scrubbed)
        self.assertIn("AIza***", scrubbed)
