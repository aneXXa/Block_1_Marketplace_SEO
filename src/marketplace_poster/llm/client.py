from __future__ import annotations

from typing import Any, Protocol

from huggingface_hub import AsyncInferenceClient
from openai import AsyncOpenAI

from marketplace_poster.config import Settings

OPENAI_PRESETS: dict[str, tuple[str, str]] = {
    "pollinations": (
        "https://text.pollinations.ai/openai",
        "openai",
    ),
    "openrouter": (
        "https://openrouter.ai/api/v1",
        "qwen/qwen3.8-27b:free",
    ),
    "gemini": (
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        "gemini-3.6-flash",
    ),
    "groq": (
        "https://api.groq.com/openai/v1",
        "llama-3.3-70b-versatile",
    ),
    "ollama": (
        "http://127.0.0.1:11434/v1",
        "qwen2.5",
    ),
}

_STOCK_MODELS = {
    "Qwen/Qwen2.5-7B-Instruct",
    "gpt-4o-mini",
    "gemini-3.6-flash",
    "llama-3.3-70b-versatile",
    "qwen/qwen3.8-27b:free",
    "qwen2.5",
    "openai",
}


class LlmClient(Protocol):
    async def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.6,
    ) -> str: ...


def normalize_hf_model_id(raw: str) -> str:
    """Карточка `huggingface.co/org/model` → id `org/model`."""
    text = raw.strip().rstrip("/")
    for prefix in (
        "https://huggingface.co/",
        "http://huggingface.co/",
        "https://www.huggingface.co/",
        "huggingface.co/",
    ):
        if text.lower().startswith(prefix):
            text = text[len(prefix) :]
            break
    parts = [part for part in text.split("/") if part and part not in {"tree", "blob"}]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return text


def apply_provider_preset(settings: Settings) -> Settings:
    preset = OPENAI_PRESETS.get(settings.llm_provider)
    if preset is None:
        return settings
    base_url, model = preset
    update: dict[str, str] = {"llm_base_url": base_url}
    if settings.llm_model in _STOCK_MODELS:
        update["llm_model"] = model
    return settings.model_copy(update=update)


def build_llm_client(settings: Settings) -> LlmClient:
    if settings.llm_provider == "huggingface":
        return HuggingFaceClient(settings)
    return OpenAiCompatibleClient(apply_provider_preset(settings))


class HuggingFaceClient:
    """Официальный клиент Hub: Inference Providers, не скачивание весов на диск."""

    def __init__(self, settings: Settings, *, client: Any | None = None) -> None:
        self._model = normalize_hf_model_id(settings.llm_model)
        self._json_mode = True
        client_kwargs: dict[str, Any] = {
            "token": settings.llm_api_key,
            "timeout": settings.llm_timeout_s,
        }
        if settings.llm_hf_provider != "auto":
            client_kwargs["provider"] = settings.llm_hf_provider
        self._client = client or AsyncInferenceClient(**client_kwargs)

    async def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.6,
    ) -> str:
        return await _complete_chat(
            self._client,
            self._model,
            messages,
            temperature=temperature,
            json_mode=self._json_mode,
            extra_body=None,
            on_json_unsupported=lambda: setattr(self, "_json_mode", False),
        )


class OpenAiCompatibleClient:
    """Pollinations, Gemini, Groq, OpenAI и любой прокси с `/v1/chat/completions`."""

    def __init__(self, settings: Settings, *, client: Any | None = None) -> None:
        self._model = settings.llm_model
        self._json_mode = True
        self._extra_body: dict[str, Any] = {}
        client_kwargs: dict[str, Any] = {
            "api_key": settings.llm_api_key or "ollama",
            "base_url": settings.llm_base_url,
            "timeout": settings.llm_timeout_s,
        }
        if settings.llm_provider == "openrouter":
            client_kwargs["default_headers"] = {
                "HTTP-Referer": "https://t.me/CardSEO_bot",
                "X-Title": "Marketplace SEO Poster",
            }
        if settings.llm_provider == "pollinations":
            # gpt-oss иначе сжигает max_tokens на reasoning и отдаёт content=None.
            self._extra_body["reasoning_effort"] = "low"
        self._client = client or AsyncOpenAI(**client_kwargs)

    async def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.6,
    ) -> str:
        return await _complete_chat(
            self._client,
            self._model,
            messages,
            temperature=temperature,
            json_mode=self._json_mode,
            extra_body=self._extra_body or None,
            on_json_unsupported=lambda: setattr(self, "_json_mode", False),
        )


async def _complete_chat(
    client: Any,
    model: str,
    messages: list[dict[str, Any]],
    *,
    temperature: float,
    json_mode: bool,
    extra_body: dict[str, Any] | None,
    on_json_unsupported: Any,
) -> str:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 3072,
    }
    if extra_body:
        kwargs["extra_body"] = extra_body
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        response = await client.chat.completions.create(**kwargs)
    except Exception as exc:
        if json_mode and _is_json_mode_unsupported(exc):
            on_json_unsupported()
            kwargs.pop("response_format", None)
            response = await client.chat.completions.create(**kwargs)
        else:
            raise
    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("модель вернула пустой content")
    return content


def _is_json_mode_unsupported(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(
        token in text
        for token in ("response_format", "json_object", "json mode", "invalid schema")
    )
