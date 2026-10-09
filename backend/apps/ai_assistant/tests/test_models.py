from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.ai_assistant.models import AIConversation, AIMessage
from apps.students.models import StudentProfile

User = get_user_model()


class AIAssistantModelTests(TestCase):
    """Test suite for AI Conversation and Message models."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="ai.student@gqt.local", password="Password123!"
        )
        self.student = StudentProfile.objects.create(
            user=self.user,
            student_id_number="GQT-STU-007",
            full_name="AI Student",
            batch_code="BATCH-2026-A",
        )

    def test_conversation_and_messages(self):
        conv = AIConversation.objects.create(
            student=self.student,
            title="Debugging Recursion Depth",
        )
        msg_1 = AIMessage.objects.create(
            conversation=conv,
            sender=AIMessage.SenderChoices.STUDENT,
            content="Why am I getting a RecursionError?",
            tokens_used=12,
        )
        msg_2 = AIMessage.objects.create(
            conversation=conv,
            sender=AIMessage.SenderChoices.ASSISTANT,
            content="Check your base case in the recursive function.",
            tokens_used=18,
        )
        self.assertEqual(conv.messages.count(), 2)
        self.assertEqual(msg_1.conversation, conv)
        self.assertEqual(msg_2.sender, AIMessage.SenderChoices.ASSISTANT)
