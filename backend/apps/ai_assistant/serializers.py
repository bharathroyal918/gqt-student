"""Serializers for AI Consultations and Message exchanges."""

from rest_framework import serializers

from apps.ai_assistant.models import AIConversation, AIMessage


class AIMessageSerializer(serializers.ModelSerializer):
    """Serializer for individual chat messages."""

    class Meta:
        model = AIMessage
        fields = [
            "id",
            "sender",
            "content",
            "tokens_used",
            "created_at",
        ]


class AIConversationListSerializer(serializers.ModelSerializer):
    """Serializer for conversation history listing."""

    messages_count = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()

    class Meta:
        model = AIConversation
        fields = [
            "id",
            "title",
            "is_archived",
            "messages_count",
            "last_message_preview",
            "created_at",
            "updated_at",
        ]

    def get_messages_count(self, obj) -> int:
        return obj.messages.count()

    def get_last_message_preview(self, obj) -> str:
        last_msg = obj.messages.order_by("-created_at").first()
        if not last_msg:
            return ""
        return (last_msg.content[:80] + "...") if len(last_msg.content) > 80 else last_msg.content


class AIConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer for full conversation details including messages."""

    messages = AIMessageSerializer(many=True, read_only=True)
    context_question_title = serializers.CharField(
        source="context_question.title", allow_null=True, read_only=True
    )

    class Meta:
        model = AIConversation
        fields = [
            "id",
            "title",
            "context_question",
            "context_question_title",
            "is_archived",
            "messages",
            "created_at",
            "updated_at",
        ]


class SendAIMessageSerializer(serializers.Serializer):
    """Input serializer for sending a message in a conversation."""

    content = serializers.CharField(max_length=4000, allow_blank=False, trim_whitespace=True)


class CreateAIConversationSerializer(serializers.Serializer):
    """Input serializer for starting a new consultation."""

    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    context_question_id = serializers.UUIDField(required=False, allow_null=True)
    initial_message = serializers.CharField(max_length=4000, required=False, allow_blank=True)
