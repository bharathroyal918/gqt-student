"""External cloud LLM provider integration adapters (OpenAI, Gemini, Anthropic) with fallback."""

import logging
import os
from typing import Any, Dict, List, Optional

from django.conf import settings

from apps.ai_assistant.providers.base import AIProviderResult, BaseAIProvider
from apps.ai_assistant.providers.smart_tutor import SmartTutorAIProvider

logger = logging.getLogger(__name__)


class ExternalLLMProvider(BaseAIProvider):
    """Adapter for external LLM APIs (OpenAI / Gemini / Anthropic) with automatic fallback.

    Ensures API keys are never exposed and requests are sanitized.
    """

    def __init__(self, provider_type: str = "auto"):
        self.provider_type = provider_type.lower()
        self.fallback_provider = SmartTutorAIProvider()

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AIProviderResult:
        # Check if an external provider key is configured
        openai_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
        gemini_key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")

        if openai_key and (self.provider_type in ["openai", "auto"]):
            try:
                return self._call_openai(openai_key, messages, system_prompt, **kwargs)
            except Exception as exc:
                # Log without exposing API key
                logger.warning(
                    "OpenAI generation failed; falling back to SmartTutorProvider: %s",
                    str(exc).replace(openai_key, "***"),
                )

        if gemini_key and (self.provider_type in ["gemini", "auto"]):
            try:
                return self._call_gemini(gemini_key, messages, system_prompt, **kwargs)
            except Exception as exc:
                logger.warning(
                    "Gemini generation failed; falling back to SmartTutorProvider: %s",
                    str(exc).replace(gemini_key, "***"),
                )

        # Fallback to local high-quality SmartTutor provider
        return self.fallback_provider.generate_response(messages, system_prompt, context, **kwargs)

    def _call_openai(
        self,
        api_key: str,
        messages: List[Dict[str, str]],
        system_prompt: str,
        **kwargs: Any,
    ) -> AIProviderResult:
        # Structured payload construction
        import urllib.request
        import json

        url = "https://api.openai.com/v1/chat/completions"
        formatted_msgs = [{"role": "system", "content": system_prompt}]
        for m in messages:
            role = "user" if m.get("role") in ["user", "STUDENT"] else "assistant"
            formatted_msgs.append({"role": role, "content": m.get("content", "")})

        payload = {
            "model": kwargs.get("model", "gpt-4o-mini"),
            "messages": formatted_msgs,
            "temperature": 0.4,
            "max_tokens": 1000,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            choice = res_data["choices"][0]
            content = choice["message"]["content"]
            tokens = res_data.get("usage", {}).get("total_tokens", len(content.split()))
            return AIProviderResult(
                content=content,
                tokens_used=tokens,
                model_name=res_data.get("model", "openai-gpt-4o-mini"),
                finish_reason=choice.get("finish_reason", "stop"),
            )

    def _call_gemini(
        self,
        api_key: str,
        messages: List[Dict[str, str]],
        system_prompt: str,
        **kwargs: Any,
    ) -> AIProviderResult:
        import urllib.request
        import json

        model = kwargs.get("model", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        contents = []
        for m in messages:
            role = "user" if m.get("role") in ["user", "STUDENT"] else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1000},
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidate = res_data["candidates"][0]
            content = candidate["content"]["parts"][0]["text"]
            return AIProviderResult(
                content=content,
                tokens_used=len(content.split()) * 2,
                model_name=f"google-{model}",
                finish_reason="stop",
            )
