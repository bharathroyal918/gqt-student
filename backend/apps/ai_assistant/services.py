"""AIService coordinating conversations, context windowing, rate limiting, and AI provider interaction."""

import logging
import re
import uuid

from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, Throttled

from apps.ai_assistant.models import AIConversation, AIMessage
from apps.ai_assistant.providers.base import BaseAIProvider
from apps.ai_assistant.providers.factory import get_ai_provider
from apps.students.models import StudentProfile

logger = logging.getLogger(__name__)

SYSTEM_PEDAGOGICAL_PROMPT = """You are the intelligent AI Learning Mentor for the GQT Student Portal.
Your primary objective is to help students learn and master programming concepts, understand error messages, debug runtime exceptions, explore coding approaches, and obtain structured hints.

Guidelines:
1. Explain concepts clearly with structured markdown and syntax-highlighted code snippets.
2. When asked about an error or bug, explain the root cause and provide clear corrective patterns.
3. Encourage understanding and algorithmic thinking rather than merely providing rote answers.
4. Keep the tone encouraging, professional, and pedagogically sound.
5. Format all code blocks with appropriate language tags (e.g. ```python, ```javascript, ```sql).
"""

# Maximum context history messages to feed to LLM
MAX_CONTEXT_MESSAGES = 10
MAX_MESSAGE_LENGTH = 4000
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW_SECONDS = 60


def safe_scrub_secrets(text: str) -> str:
    """Scrub sensitive API tokens or secrets from strings prior to logging."""
    if not text:
        return text
    # Mask common API key patterns (e.g. sk-..., AIza...)
    scrubbed = re.sub(r"(sk-[a-zA-Z0-9_-]{20,})", "sk-***", text)
    scrubbed = re.sub(r"(AIza[a-zA-Z0-9_-]{20,})", "AIza***", scrubbed)
    scrubbed = re.sub(r"(Bearer\s+[a-zA-Z0-9._-]+)", "Bearer ***", scrubbed)
    return scrubbed


class AIService:
    """Core domain service for Student AI consultations."""

    def __init__(self, provider: BaseAIProvider | None = None):
        self.provider = provider or get_ai_provider()

    def check_rate_limit(self, student_id: uuid.UUID) -> None:
        """Enforce rate limits per student using cache-backed sliding window."""
        cache_key = f"ai_rate_limit_{student_id}"
        current_count = cache.get(cache_key, 0)
        if current_count >= RATE_LIMIT_REQUESTS:
            logger.warning("Rate limit exceeded for student %s in AI tutor", student_id)
            raise Throttled(
                detail=f"Rate limit exceeded. You can send up to {RATE_LIMIT_REQUESTS} AI messages per minute. Please try again shortly."
            )
        # Increment counter or set new window
        try:
            if current_count == 0:
                cache.set(cache_key, 1, timeout=RATE_LIMIT_WINDOW_SECONDS)
            else:
                cache.incr(cache_key)
        except (ValueError, TypeError, KeyError, OSError):
            # Fallback if incr fails
            cache.set(cache_key, current_count + 1, timeout=RATE_LIMIT_WINDOW_SECONDS)

    def list_conversations(self, student: StudentProfile):
        """Retrieve all active conversations belonging to the student."""
        return (
            AIConversation.objects.filter(
                student=student,
                is_archived=False,
            )
            .prefetch_related("messages")
            .order_by("-updated_at")
        )

    def get_conversation_for_student(
        self, student: StudentProfile, conversation_id: uuid.UUID
    ) -> AIConversation:
        """Fetch a specific conversation ensuring strict ownership authorization."""
        try:
            conv = AIConversation.objects.prefetch_related("messages").get(
                id=conversation_id
            )
        except AIConversation.DoesNotExist:
            raise NotFound("AI consultation session not found.")

        if conv.student_id != student.id:
            logger.warning(
                "Unauthorized AI conversation access attempt by student %s on conversation %s",
                student.id,
                conversation_id,
            )
            raise PermissionDenied(
                "You do not have permission to access this consultation session."
            )

        if conv.is_archived:
            raise NotFound("AI consultation session has been archived.")

        return conv

    @transaction.atomic
    def create_conversation(
        self,
        student: StudentProfile,
        title: str | None = None,
        context_question_id: uuid.UUID | None = None,
        initial_message: str | None = None,
    ) -> AIConversation:
        """Create a new AI conversation session and optionally process an initial prompt."""
        conv_title = (title.strip() if title and title.strip() else "New Consultation")[
            :200
        ]
        conversation = AIConversation.objects.create(
            student=student,
            title=conv_title,
            context_question_id=context_question_id,
        )

        if initial_message and initial_message.strip():
            self.post_message(
                student=student,
                conversation_id=conversation.id,
                content=initial_message.strip(),
            )
            conversation.refresh_from_db()

        return conversation

    @transaction.atomic
    def post_message(
        self,
        student: StudentProfile,
        conversation_id: uuid.UUID,
        content: str,
    ) -> AIMessage:
        """Validate student message, enforce rate limit, query AI provider, and persist messages."""
        # 1. Validate content
        if not content or not content.strip():
            raise ValidationError({"content": "Message cannot be empty."})

        cleaned_content = content.strip()
        if len(cleaned_content) > MAX_MESSAGE_LENGTH:
            raise ValidationError(
                {
                    "content": f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters."
                }
            )

        # 2. Authorization check
        conversation = self.get_conversation_for_student(student, conversation_id)

        # 3. Rate limiting check
        self.check_rate_limit(student.id)

        # 4. Save student message
        AIMessage.objects.create(
            conversation=conversation,
            sender=AIMessage.SenderChoices.STUDENT,
            content=cleaned_content,
            tokens_used=max(1, len(cleaned_content.split())),
        )

        # 5. Build context window (last N messages)
        recent_messages = list(
            conversation.messages.order_by("-created_at")[:MAX_CONTEXT_MESSAGES]
        )
        recent_messages.reverse()

        messages_payload = []
        for msg in recent_messages:
            role = (
                "user" if msg.sender == AIMessage.SenderChoices.STUDENT else "assistant"
            )
            messages_payload.append({"role": role, "content": msg.content})

        # 6. Query AI Provider safely
        try:
            provider_result = self.provider.generate_response(
                messages=messages_payload,
                system_prompt=SYSTEM_PEDAGOGICAL_PROMPT,
                context={"student_id": str(student.id), "title": conversation.title},
            )
        except (
            RuntimeError,
            ValueError,
            TypeError,
            OSError,
            TimeoutError,
            KeyError,
        ) as exc:
            safe_err = safe_scrub_secrets(str(exc))
            logger.error("AI Provider error during message generation: %s", safe_err)
            provider_result = self.provider.generate_response(
                messages=messages_payload,
                system_prompt=SYSTEM_PEDAGOGICAL_PROMPT,
            )

        # 7. Persist AI assistant message
        assistant_msg = AIMessage.objects.create(
            conversation=conversation,
            sender=AIMessage.SenderChoices.ASSISTANT,
            content=provider_result.content,
            tokens_used=provider_result.tokens_used,
        )

        # 8. Auto-title conversation if it's default
        if conversation.title in ["New Consultation", "New Conversation"]:
            words = cleaned_content.split()[:6]
            if words:
                new_title = " ".join(words).capitalize()[:60]
                conversation.title = new_title

        conversation.updated_at = timezone.now()
        conversation.save(update_fields=["title", "updated_at"])

        return assistant_msg

    @transaction.atomic
    def retry_last_message(
        self,
        student: StudentProfile,
        conversation_id: uuid.UUID,
    ) -> AIMessage:
        """Re-generate AI response for the last student inquiry in the conversation."""
        conversation = self.get_conversation_for_student(student, conversation_id)
        self.check_rate_limit(student.id)

        # Find the last student message
        last_student_msg = (
            conversation.messages.filter(sender=AIMessage.SenderChoices.STUDENT)
            .order_by("-created_at")
            .first()
        )

        if not last_student_msg:
            raise ValidationError("No student message found to retry.")

        # Build context history up to that point
        history_msgs = list(
            conversation.messages.filter(
                created_at__lte=last_student_msg.created_at
            ).order_by("-created_at")[:MAX_CONTEXT_MESSAGES]
        )
        history_msgs.reverse()

        messages_payload = [
            {
                "role": "user"
                if m.sender == AIMessage.SenderChoices.STUDENT
                else "assistant",
                "content": m.content,
            }
            for m in history_msgs
        ]

        provider_result = self.provider.generate_response(
            messages=messages_payload,
            system_prompt=SYSTEM_PEDAGOGICAL_PROMPT,
            context={"student_id": str(student.id), "title": conversation.title},
        )

        assistant_msg = AIMessage.objects.create(
            conversation=conversation,
            sender=AIMessage.SenderChoices.ASSISTANT,
            content=provider_result.content,
            tokens_used=provider_result.tokens_used,
        )

        conversation.updated_at = timezone.now()
        conversation.save(update_fields=["updated_at"])

        return assistant_msg

    def archive_conversation(
        self, student: StudentProfile, conversation_id: uuid.UUID
    ) -> None:
        """Soft-delete/archive an AI consultation session."""
        conversation = self.get_conversation_for_student(student, conversation_id)
        conversation.is_archived = True
        conversation.save(update_fields=["is_archived", "updated_at"])
