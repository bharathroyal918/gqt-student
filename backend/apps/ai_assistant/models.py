from django.db import models

from apps.common.models import BaseModel


class AIConversation(BaseModel):
    """Contextual conversation session between a student and the AI tutor."""

    student = models.ForeignKey(
        "students.StudentProfile", on_delete=models.CASCADE, related_name="ai_conversations"
    )
    context_question = models.ForeignKey(
        "assignments.CodingQuestion",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ai_conversations",
    )
    title = models.CharField(max_length=200, default="New Consultation")
    is_archived = models.BooleanField(default=False, db_index=True)

    class Meta:
        verbose_name = "AI Conversation"
        verbose_name_plural = "AI Conversations"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["student", "-updated_at"], name="ai_conv_student_date_idx"),
        ]

    def __str__(self):
        return f"{self.student.full_name}: {self.title}"


class AIMessage(BaseModel):
    """Individual message exchange inside an AI tutor conversation."""

    class SenderChoices(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        ASSISTANT = "ASSISTANT", "AI Assistant"
        SYSTEM = "SYSTEM", "System Prompt"

    conversation = models.ForeignKey(
        AIConversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.CharField(max_length=20, choices=SenderChoices.choices, db_index=True)
    content = models.TextField()
    tokens_used = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "AI Message"
        verbose_name_plural = "AI Messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"], name="ai_msg_conv_date_idx"),
        ]

    def __str__(self):
        return f"[{self.sender}] {self.content[:40]}..."
