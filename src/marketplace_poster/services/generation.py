from __future__ import annotations

import base64
import logging
from typing import Any

from marketplace_poster.llm.client import LlmClient
from marketplace_poster.llm.parse import SeoParseError, parse_seo_package
from marketplace_poster.llm.prompts import build_system_prompt, build_user_prompt, variation_hint
from marketplace_poster.models.seo_package import ProductBrief, SeoPackage
from marketplace_poster.platforms.base import PlatformRulePack
from marketplace_poster.services.validation import ValidationResult, validate_package

logger = logging.getLogger(__name__)


class GenerationError(Exception):
    """Пользователю показываем одно короткое сообщение, без стека."""


class GenerationService:
    def __init__(self, llm: LlmClient) -> None:
        self._llm = llm

    async def generate(
        self,
        platform: PlatformRulePack,
        brief: ProductBrief,
        *,
        photo_bytes: bytes | None = None,
        variation_index: int = 0,
    ) -> tuple[SeoPackage, ValidationResult]:
        hint = variation_hint(variation_index)
        raw = await self._complete(platform, brief, photo_bytes=photo_bytes, hint=hint)
        try:
            draft = parse_seo_package(raw)
        except SeoParseError as exc:
            logger.warning("parse failed: %s", exc)
            raise GenerationError("модель вернула неразборчивый ответ") from exc

        result = validate_package(draft, platform)
        if result.needs_llm_repair:
            repaired_raw = await self._complete(
                platform,
                brief,
                photo_bytes=photo_bytes,
                hint=hint,
                repair_issues=result.issues,
            )
            try:
                repaired = parse_seo_package(repaired_raw)
            except SeoParseError:
                logger.warning("repair parse failed, keep local validation")
                return result.package, result
            result = validate_package(repaired, platform)
        return result.package, result

    async def _complete(
        self,
        platform: PlatformRulePack,
        brief: ProductBrief,
        *,
        photo_bytes: bytes | None,
        hint: str | None = None,
        repair_issues: list[str] | None = None,
    ) -> str:
        user_text = build_user_prompt(
            platform, brief, hint=hint, repair_issues=repair_issues
        )
        user_content: str | list[dict[str, Any]]
        if photo_bytes:
            encoded = base64.b64encode(photo_bytes).decode("ascii")
            user_content = [
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded}"},
                },
            ]
        else:
            user_content = user_text

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": build_system_prompt(platform)},
            {"role": "user", "content": user_content},
        ]
        try:
            return await self._llm.complete(messages)
        except GenerationError:
            raise
        except Exception as exc:
            logger.exception("llm call failed")
            raise GenerationError(humanize_llm_error(exc)) from exc


def humanize_llm_error(exc: BaseException) -> str:
    text = str(exc).lower()
    if "401" in text or "invalid api key" in text or "api_key" in text and "invalid" in text:
        return "Ключ LLM отклонён. Проверьте LLM_API_KEY в .env."
    if "429" in text or "rate limit" in text:
        return "Модель отклонила запрос: слишком частые вызовы. Подождите минуту и повторите."
    return "Не удалось обратиться к модели. Подробности в логе терминала."
