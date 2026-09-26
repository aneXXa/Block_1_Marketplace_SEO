from __future__ import annotations

import os

import pytest

from marketplace_poster.config import Settings
from marketplace_poster.llm.client import build_llm_client
from marketplace_poster.models.seo_package import ProductBrief
from marketplace_poster.platforms import WILDBERRIES
from marketplace_poster.preview import SAMPLE_BRIEF
from marketplace_poster.services.generation import GenerationService

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("LLM_API_KEY") and not os.getenv("HF_TOKEN"), reason="нет LLM_API_KEY/HF_TOKEN")
async def test_live_model_returns_valid_wb_package() -> None:
    settings = Settings(
        telegram_bot_token="0:test",
        llm_api_key=os.getenv("LLM_API_KEY") or os.environ["HF_TOKEN"],
        llm_provider=os.getenv("LLM_PROVIDER", "pollinations"),  # type: ignore[arg-type]
        llm_base_url=os.getenv(
            "LLM_BASE_URL",
            "https://text.pollinations.ai/openai",
        ),
        llm_model=os.getenv("LLM_MODEL", "openai"),
    )
    service = GenerationService(build_llm_client(settings))
    brief = ProductBrief(facts=SAMPLE_BRIEF.facts)
    package, result = await service.generate(WILDBERRIES, brief)
    assert package.title
    assert len(package.title) <= WILDBERRIES.max_title
    assert package.description
    assert package.tags
    assert not result.needs_llm_repair or len(package.title) <= WILDBERRIES.max_title
