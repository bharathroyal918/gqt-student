"""Student views for AI Consultation Sessions and Message exchanges."""

import uuid

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.ai_assistant.serializers import (
    AIConversationDetailSerializer,
    AIConversationListSerializer,
    AIMessageSerializer,
    CreateAIConversationSerializer,
    SendAIMessageSerializer,
)
from apps.ai_assistant.services import AIService
from apps.common.responses import api_error, api_success
from apps.students.models import StudentProfile


def _get_student_profile(request):
    student = getattr(request.user, "student_profile", None)
    if not student:
        student = StudentProfile.objects.filter(user=request.user).first()
    return student


class StudentAIConversationListView(APIView):
    """List active AI consultations or start a new conversation session."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List AI Conversations",
        description="Retrieve history of AI consultation sessions belonging to the student.",
        responses={200: AIConversationListSerializer(many=True)},
        tags=["Student AI Help"],
    )
    def get(self, request):
        student = _get_student_profile(request)
        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required to access AI consultation.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        service = AIService()
        conversations = service.list_conversations(student)
        serializer = AIConversationListSerializer(conversations, many=True)

        return api_success(
            data={"conversations": serializer.data, "count": len(serializer.data)},
            message="AI consultations retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Create AI Conversation",
        description="Initiate a new AI conversation session, optionally with an initial prompt.",
        request=CreateAIConversationSerializer,
        responses={201: AIConversationDetailSerializer},
        tags=["Student AI Help"],
    )
    def post(self, request):
        student = _get_student_profile(request)
        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required to access AI consultation.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = CreateAIConversationSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Invalid conversation parameters.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data
        service = AIService()

        try:
            conversation = service.create_conversation(
                student=student,
                title=validated_data.get("title"),
                context_question_id=validated_data.get("context_question_id"),
                initial_message=validated_data.get("initial_message"),
            )
            detail_serializer = AIConversationDetailSerializer(conversation)
            return api_success(
                data=detail_serializer.data,
                message="AI consultation session created successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except Throttled as exc:
            return api_error(
                code="RATE_LIMIT_EXCEEDED",
                message=str(exc.detail),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except ValidationError as exc:
            return api_error(
                code="VALIDATION_ERROR",
                message="Validation failed.",
                details=exc.message_dict
                if hasattr(exc, "message_dict")
                else exc.messages,
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class StudentAIConversationDetailView(APIView):
    """Retrieve or archive a specific AI consultation session."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve AI Conversation",
        description="Fetch conversation details along with full chronological message history.",
        responses={200: AIConversationDetailSerializer},
        tags=["Student AI Help"],
    )
    def get(self, request, conversation_id: uuid.UUID):
        student = _get_student_profile(request)
        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        service = AIService()
        try:
            conversation = service.get_conversation_for_student(
                student, conversation_id
            )
            serializer = AIConversationDetailSerializer(conversation)
            return api_success(
                data=serializer.data,
                message="Conversation retrieved successfully.",
                status_code=status.HTTP_200_OK,
            )
        except NotFound as exc:
            return api_error(
                code="NOT_FOUND",
                message=str(exc.detail),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except PermissionDenied as exc:
            return api_error(
                code="PERMISSION_DENIED",
                message=str(exc),
                status_code=status.HTTP_403_FORBIDDEN,
            )

    @extend_schema(
        summary="Archive AI Conversation",
        description="Soft delete or archive a conversation session.",
        responses={200: None},
        tags=["Student AI Help"],
    )
    def delete(self, request, conversation_id: uuid.UUID):
        student = _get_student_profile(request)
        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        service = AIService()
        try:
            service.archive_conversation(student, conversation_id)
            return api_success(
                data=None,
                message="Conversation archived successfully.",
                status_code=status.HTTP_200_OK,
            )
        except NotFound as exc:
            return api_error(
                code="NOT_FOUND",
                message=str(exc.detail),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except PermissionDenied as exc:
            return api_error(
                code="PERMISSION_DENIED",
                message=str(exc),
                status_code=status.HTTP_403_FORBIDDEN,
            )


class StudentAIMessageSendView(APIView):
    """Post a new student prompt to the conversation and receive the AI tutor's response."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Send AI Message",
        description="Post a query in the conversation and receive an intelligent pedagogical response.",
        request=SendAIMessageSerializer,
        responses={200: AIMessageSerializer},
        tags=["Student AI Help"],
    )
    def post(self, request, conversation_id: uuid.UUID):
        student = _get_student_profile(request)
        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        serializer = SendAIMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                code="VALIDATION_ERROR",
                message="Invalid message format.",
                details=serializer.errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        service = AIService()
        try:
            assistant_message = service.post_message(
                student=student,
                conversation_id=conversation_id,
                content=serializer.validated_data["content"],
            )
            msg_serializer = AIMessageSerializer(assistant_message)
            return api_success(
                data=msg_serializer.data,
                message="AI response generated successfully.",
                status_code=status.HTTP_200_OK,
            )
        except NotFound as exc:
            return api_error(
                code="NOT_FOUND",
                message=str(exc.detail),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except PermissionDenied as exc:
            return api_error(
                code="PERMISSION_DENIED",
                message=str(exc),
                status_code=status.HTTP_403_FORBIDDEN,
            )
        except Throttled as exc:
            return api_error(
                code="RATE_LIMIT_EXCEEDED",
                message=str(exc.detail),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except ValidationError as exc:
            return api_error(
                code="VALIDATION_ERROR",
                message="Validation failed.",
                details=exc.message_dict
                if hasattr(exc, "message_dict")
                else exc.messages,
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class StudentAIMessageRetryView(APIView):
    """Regenerate an AI tutor response for the last student inquiry."""

    permission_classes = [IsAuthenticated]
    serializer_class = AIMessageSerializer

    @extend_schema(
        summary="Retry AI Message",
        description="Regenerate an assistant response for the last student message in the session.",
        request=None,
        responses={200: AIMessageSerializer},
        tags=["Student AI Help"],
    )
    def post(self, request, conversation_id: uuid.UUID):
        student = _get_student_profile(request)
        if not student:
            return api_error(
                code="STUDENT_PROFILE_REQUIRED",
                message="An active student profile is required.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        service = AIService()
        try:
            assistant_message = service.retry_last_message(
                student=student,
                conversation_id=conversation_id,
            )
            msg_serializer = AIMessageSerializer(assistant_message)
            return api_success(
                data=msg_serializer.data,
                message="AI response regenerated successfully.",
                status_code=status.HTTP_200_OK,
            )
        except NotFound as exc:
            return api_error(
                code="NOT_FOUND",
                message=str(exc.detail),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        except PermissionDenied as exc:
            return api_error(
                code="PERMISSION_DENIED",
                message=str(exc),
                status_code=status.HTTP_403_FORBIDDEN,
            )
        except Throttled as exc:
            return api_error(
                code="RATE_LIMIT_EXCEEDED",
                message=str(exc.detail),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except ValidationError as exc:
            return api_error(
                code="VALIDATION_ERROR",
                message=str(exc),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
