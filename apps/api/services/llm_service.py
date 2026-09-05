from __future__ import annotations

import httpx

try:
    from ..config import settings
except ImportError:  # pragma: no cover - direct script compatibility
    from config import settings


class LLMServiceError(Exception):
    pass


class LLMService:
    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        if not settings.openai_api_key:
            return self._fallback_response(messages)

        payload = {
            "model": settings.openai_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{settings.openai_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            raise LLMServiceError(f"LLM provider returned HTTP {exc.response.status_code}") from None
        except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError):
            raise LLMServiceError("LLM transport or response validation failed") from None

    def _fallback_response(self, messages: list[dict[str, str]]) -> str:
        user_content = next(
            (message["content"] for message in reversed(messages) if message["role"] == "user"),
            "",
        )

        return (
            "**Sonic AI Studio — Offline Mode**\n\n"
            "The LLM provider is not configured. Set `SONIC_OPENAI_API_KEY` in your environment "
            "to enable full Producer Intelligence.\n\n"
            f"Your message was received: *\"{user_content[:200]}\"*\n\n"
            "Once connected, Sonic AI will provide context-aware production, mixing, and "
            "mastering guidance powered by your project data and studio memory."
        )


llm_service = LLMService()
