from types import SimpleNamespace
from typing import Any

import pytest

from marketplace_poster.config import Settings
from marketplace_poster.llm.client import (
    HuggingFaceClient,
    OpenAiCompatibleClient,
    apply_provider_preset,
    build_llm_client,
    normalize_hf_model_id,
)


def _settings(**overrides: object) -> Settings:
    data: dict[str, Any] = {
        "telegram_bot_token": "0:test",
        "llm_api_key": "test-key",
        "llm_provider": "openrouter",
        "llm_model": "qwen/qwen3.8-27b:free",
        "llm_base_url": "https://openrouter.ai/api/v1",
    }
    data.update(overrides)
    return Settings(_env_file=None, **data)


def test_normalize_hf_model_id_from_url() -> None:
    assert (
        normalize_hf_model_id("https://huggingface.co/Qwen/Qwen2.5-7B-Instruct")
        == "Qwen/Qwen2.5-7B-Instruct"
    )
    assert (
        normalize_hf_model_id("https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/tree/main")
        == "Qwen/Qwen2.5-7B-Instruct"
    )
    assert normalize_hf_model_id("Qwen/Qwen2.5-7B-Instruct") == "Qwen/Qwen2.5-7B-Instruct"


def test_factory_defaults_to_openrouter() -> None:
    client = build_llm_client(_settings())
    assert isinstance(client, OpenAiCompatibleClient)
    assert client._model == "qwen/qwen3.8-27b:free"


def test_pollinations_preset() -> None:
    resolved = apply_provider_preset(
        _settings(llm_provider="pollinations", llm_api_key="", llm_model="openai")
    )
    assert resolved.llm_base_url == "https://text.pollinations.ai/openai"
    assert resolved.llm_model == "openai"


def test_openrouter_preset() -> None:
    resolved = apply_provider_preset(_settings(llm_provider="openrouter"))
    assert resolved.llm_base_url == "https://openrouter.ai/api/v1"
    assert resolved.llm_model == "qwen/qwen3.8-27b:free"


def test_groq_preset() -> None:
    resolved = apply_provider_preset(_settings(llm_provider="groq"))
    assert resolved.llm_base_url == "https://api.groq.com/openai/v1"
    assert resolved.llm_model == "llama-3.3-70b-versatile"


def test_ollama_preset() -> None:
    resolved = apply_provider_preset(_settings(llm_provider="ollama"))
    assert resolved.llm_base_url == "http://127.0.0.1:11434/v1"
    assert resolved.llm_model == "qwen2.5"


def test_factory_openai_provider() -> None:
    client = build_llm_client(
        _settings(
            llm_provider="openai",
            llm_model="gpt-4o-mini",
            llm_base_url="https://api.openai.com/v1",
        )
    )
    assert isinstance(client, OpenAiCompatibleClient)
    assert client._model == "gpt-4o-mini"


def test_factory_huggingface() -> None:
    client = build_llm_client(
        _settings(llm_provider="huggingface", llm_model="Qwen/Qwen2.5-7B-Instruct")
    )
    assert isinstance(client, HuggingFaceClient)


class _FakeCompletions:
    def __init__(
        self,
        content: str,
        fail_once: bool = False,
        fail_always: str | None = None,
    ) -> None:
        self.content = content
        self.fail_once = fail_once
        self.fail_always = fail_always
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        if self.fail_always:
            raise RuntimeError(self.fail_always)
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("json_object not supported")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.chat = SimpleNamespace(completions=completions)


@pytest.mark.asyncio
async def test_pollinations_sends_low_reasoning_effort() -> None:
    fake = _FakeCompletions('{"title": "Монитор"}')
    client = OpenAiCompatibleClient(
        _settings(llm_provider="pollinations", llm_api_key="pollinations", llm_model="openai"),
        client=_FakeChat(fake),
    )
    text = await client.complete([{"role": "user", "content": "hi"}])
    assert text == '{"title": "Монитор"}'
    assert fake.calls[0]["extra_body"] == {"reasoning_effort": "low"}


@pytest.mark.asyncio
async def test_hf_client_returns_content() -> None:
    fake = _FakeCompletions('{"title": "Худи"}')
    client = HuggingFaceClient(
        _settings(llm_provider="huggingface", llm_model="Qwen/Qwen2.5-7B-Instruct"),
        client=_FakeChat(fake),
    )
    text = await client.complete([{"role": "user", "content": "hi"}])
    assert text == '{"title": "Худи"}'
    assert fake.calls[0]["model"] == "Qwen/Qwen2.5-7B-Instruct"
    assert fake.calls[0]["response_format"] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_hf_client_retries_without_json_mode() -> None:
    fake = _FakeCompletions('{"title": "Худи"}', fail_once=True)
    client = HuggingFaceClient(
        _settings(llm_provider="huggingface", llm_model="Qwen/Qwen2.5-7B-Instruct"),
        client=_FakeChat(fake),
    )
    text = await client.complete([{"role": "user", "content": "hi"}])
    assert text == '{"title": "Худи"}'
    assert len(fake.calls) == 2
    assert "response_format" not in fake.calls[1]


@pytest.mark.asyncio
async def test_location_error_does_not_retry() -> None:
    fake = _FakeCompletions(
        "x",
        fail_always="Error code: 400 User location is not supported for the API use.",
    )
    client = HuggingFaceClient(
        _settings(llm_provider="huggingface", llm_model="Qwen/Qwen2.5-7B-Instruct"),
        client=_FakeChat(fake),
    )
    with pytest.raises(RuntimeError, match="location"):
        await client.complete([{"role": "user", "content": "hi"}])
    assert len(fake.calls) == 1
