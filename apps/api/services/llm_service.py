from __future__ import annotations

import httpx

try:
    from ..config import Settings
except ImportError:  # pragma: no cover - direct script compatibility
    from config import Settings


class LLMServiceError(Exception):
    pass


class LLMService:
    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        settings = Settings.from_env()
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
            with httpx.Client(timeout=35.0, follow_redirects=False) as client:
                response = client.post(
                    f"{settings.openai_base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise LLMServiceError("AI returned an empty response. Try again.")
                return content
        except httpx.HTTPStatusError as exc:
            messages = {401: "AI key was rejected. Check the AI connection in Settings.",
                        403: "AI access was denied for this account or model.",
                        429: "AI usage limit reached. Check provider quota or retry later."}
            raise LLMServiceError(messages.get(exc.response.status_code, "AI provider is unavailable. Try again later.")) from None
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            raise LLMServiceError("AI connection failed or returned an invalid response. Try again later.") from None

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
