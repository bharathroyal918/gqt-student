"""URL routing for Student AI Consultation endpoints."""

from django.urls import path

from apps.ai_assistant.views import (
    StudentAIConversationDetailView,
    StudentAIConversationListView,
    StudentAIMessageRetryView,
    StudentAIMessageSendView,
)

app_name = "ai_assistant"

urlpatterns = [
    path("conversations/", StudentAIConversationListView.as_view(), name="conversation_list_create"),
    path(
        "conversations/<uuid:conversation_id>/",
        StudentAIConversationDetailView.as_view(),
        name="conversation_detail_archive",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        StudentAIMessageSendView.as_view(),
        name="message_send",
    ),
    path(
        "conversations/<uuid:conversation_id>/retry/",
        StudentAIMessageRetryView.as_view(),
        name="message_retry",
    ),
]
