"""Base classes and interfaces for pluggable AI Providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AIProviderResult:
    """Standardized response from an AI Provider."""

    content: str
    tokens_used: int = 0
    model_name: str = "default-tutor"
    finish_reason: str = "stop"
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAIProvider(ABC):
    """Abstract interface for AI generation providers."""

    @abstractmethod
    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> AIProviderResult:
        """Generate a pedagogical AI tutor response.

        Args:
            messages: List of message dictionaries with 'role' ('user', 'assistant', 'system')
                      and 'content'.
            system_prompt: The guiding pedagogical system prompt.
            context: Optional contextual parameters (e.g. current assignment question).

        Returns:
            AIProviderResult containing the AI text, tokens used, and metadata.
        """
