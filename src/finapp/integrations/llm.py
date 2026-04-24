"""LLM provider abstraction. Default: Azure OpenAI (matches agents/Foundry-test)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from finapp.config import get_settings


@dataclass(slots=True)
class LLMResponse:
    text: str
    model: str
    tokens_in: int
    tokens_out: int


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, system: str, user: str, *, temperature: float = 0.2) -> LLMResponse: ...

    def complete_json(self, system: str, user: str) -> str:
        """Convenience: ask the model to return strict JSON."""
        return self.complete(
            system + "\nReply with valid JSON only.", user, temperature=0.0
        ).text


class AzureOpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        s = get_settings()
        if not (s.azure_openai_endpoint and s.azure_openai_api_key and s.azure_openai_deployment):
            raise RuntimeError(
                "Azure OpenAI is not configured. See .env.template for required variables."
            )
        from openai import AzureOpenAI

        self._client = AzureOpenAI(
            api_key=s.azure_openai_api_key,
            api_version=s.azure_openai_api_version,
            azure_endpoint=s.azure_openai_endpoint,
        )
        self._deployment = s.azure_openai_deployment

    def complete(
        self, system: str, user: str, *, temperature: float = 0.2
    ) -> LLMResponse:  # pragma: no cover - network
        resp = self._client.chat.completions.create(
            model=self._deployment,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        usage = resp.usage
        return LLMResponse(
            text=resp.choices[0].message.content or "",
            model=self._deployment,
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
        )


def default_provider() -> LLMProvider:
    return AzureOpenAIProvider()
