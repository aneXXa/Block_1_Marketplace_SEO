from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LlmProvider = Literal[
    "pollinations",
    "openrouter",
    "gemini",
    "groq",
    "huggingface",
    "openai",
    "ollama",
]


class Settings(BaseSettings):
    """Конфигурация только из окружения / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    telegram_bot_token: str
    llm_provider: LlmProvider = "pollinations"
    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "LLM_API_KEY",
            "OPENROUTER_API_KEY",
            "GEMINI_API_KEY",
            "GROQ_API_KEY",
            "HF_TOKEN",
        ),
    )
    llm_base_url: str = "https://text.pollinations.ai/openai"
    llm_model: str = "openai"
    llm_hf_provider: str = "auto"
    llm_timeout_s: float = 90.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
