from __future__ import annotations

import json
import re

from marketplace_poster.models.seo_package import SeoPackage

FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


class SeoParseError(ValueError):
    """Модель вернула текст, который нельзя разобрать как SeoPackage."""


def parse_seo_package(raw: str) -> SeoPackage:
    """Достаёт JSON из сырого ответа (включая markdown-ограждения)."""
    if not raw or not raw.strip():
        raise SeoParseError("пустой ответ модели")

    text = raw.strip()
    if text.startswith("```"):
        text = FENCE_RE.sub("", text).strip()

    try:
        return SeoPackage.model_validate_json(text)
    except Exception:
        payload = _extract_json_object(text)
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise SeoParseError(f"ответ не JSON: {exc.msg}") from exc
        try:
            return SeoPackage.model_validate(data)
        except Exception as exc:
            raise SeoParseError(f"JSON не совпал со схемой: {exc}") from exc


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise SeoParseError("в ответе нет JSON-объекта")
    return text[start : end + 1]
