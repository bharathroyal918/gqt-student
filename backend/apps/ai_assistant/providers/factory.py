"""Factory function for instantiating the appropriate AI provider."""

from django.conf import settings

from apps.ai_assistant.providers.base import BaseAIProvider
from apps.ai_assistant.providers.external import ExternalLLMProvider
from apps.ai_assistant.providers.smart_tutor import SmartTutorAIProvider


def get_ai_provider(provider_type: str | None = None) -> BaseAIProvider:
    """Return an AIProvider instance based on system configuration.

    Defaults to SmartTutorAIProvider or ExternalLLMProvider with fallback.
    """
    configured_provider = (
        provider_type or getattr(settings, "AI_ASSISTANT_PROVIDER", "smart_tutor")
    ).lower()

    if configured_provider == "external":
        return ExternalLLMProvider()
    elif configured_provider in ["openai", "gemini"]:
        return ExternalLLMProvider(provider_type=configured_provider)
    else:
        return SmartTutorAIProvider()
