from __future__ import annotations

import re
from dataclasses import dataclass, field

from marketplace_poster.models.seo_package import SeoPackage
from marketplace_poster.platforms.base import PlatformRulePack

URL_RE = re.compile(
    r"https?://\S+|www\.\S+|\b\S+\.(?:ru|com|net|org|рф)\b",
    re.IGNORECASE,
)
HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)
MULTI_SPACE_RE = re.compile(r"\s+")
WORD_RE = re.compile(r"[^\w\-]+", re.UNICODE)
EMOJI_RE = re.compile(
    "["
    "\U0001f1e0-\U0001f1ff"
    "\U0001f300-\U0001f5ff"
    "\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff"
    "\U0001f700-\U0001f77f"
    "\U0001f780-\U0001f7ff"
    "\U0001f800-\U0001f8ff"
    "\U0001f900-\U0001f9ff"
    "\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff"
    "\U00002700-\U000027bf"
    "\U0000fe00-\U0000fe0f"
    "\U0001f004"
    "\U0001f0cf"
    "]+",
    flags=re.UNICODE,
)
GLOBAL_BANNED = (
    "лучший в мире",
    "самый лучший",
    "суперцена",
    "шок-цена",
)

OVERSHOOT_RATIO = 0.10


@dataclass
class ValidationResult:
    package: SeoPackage
    issues: list[str] = field(default_factory=list)
    locally_changed: bool = False

    @property
    def needs_llm_repair(self) -> bool:
        return any(issue.startswith("repair:") for issue in self.issues)


def sanitize_text(text: str, *, strip_hashtags: bool = False) -> str:
    cleaned = EMOJI_RE.sub("", text)
    cleaned = URL_RE.sub("", cleaned)
    if strip_hashtags:
        cleaned = HASHTAG_RE.sub(r"\1", cleaned)
    cleaned = _normalize_caps(cleaned)
    return MULTI_SPACE_RE.sub(" ", cleaned).strip()


def trim_to_limit(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" \t,.;:—-")
    return cut if cut else text[:limit]


def collapse_word_repeats(text: str, max_repeats: int) -> str:
    counts: dict[str, int] = {}
    kept: list[str] = []
    for word in text.split():
        bare = WORD_RE.sub("", word.lower())
        if not bare:
            kept.append(word)
            continue
        counts[bare] = counts.get(bare, 0) + 1
        if counts[bare] <= max_repeats:
            kept.append(word)
    return " ".join(kept)


def enforce_word_length(text: str, max_len: int) -> str:
    words: list[str] = []
    for word in text.split():
        prefix = WORD_RE.sub("", word)
        if len(prefix) > max_len:
            words.append(prefix[:max_len])
        else:
            words.append(word)
    return " ".join(words)


def validate_package(package: SeoPackage, platform: PlatformRulePack) -> ValidationResult:
    """Режет лимиты и баны локально; помечает случаи, где нужен repair у LLM."""
    issues: list[str] = []
    changed = False

    title = sanitize_text(package.title, strip_hashtags=platform.strip_hashtags)
    description = sanitize_text(package.description, strip_hashtags=platform.strip_hashtags)
    if title != package.title or description != package.description:
        changed = True
        issues.append("sanitized:emoji_url_caps")

    title, title_changed, title_issues = _apply_title_rules(title, platform)
    description, desc_changed, desc_issues = _apply_description_rules(description, platform)
    changed = changed or title_changed or desc_changed
    issues.extend(title_issues)
    issues.extend(desc_issues)

    tags = _clean_phrases(package.tags, platform)
    attributes = _clean_phrases(package.attributes, platform)
    if tags != package.tags or attributes != package.attributes:
        changed = True

    if len(tags) > platform.max_tags:
        tags = tags[: platform.max_tags]
        changed = True
        issues.append("trimmed:tags")
    if len(tags) < platform.min_tags:
        issues.append(f"soft:tags_below_min:{len(tags)}<{platform.min_tags}")

    banned_hits = _banned_hits(f"{title} {description}", platform)
    if banned_hits:
        issues.append(f"repair:banned:{','.join(banned_hits)}")

    result = SeoPackage(title=title, description=description, tags=tags, attributes=attributes)
    return ValidationResult(package=result, issues=issues, locally_changed=changed)


def _apply_title_rules(
    title: str, platform: PlatformRulePack
) -> tuple[str, bool, list[str]]:
    issues: list[str] = []
    changed = False
    original_len = len(title)

    if platform.max_word_repeats is not None:
        collapsed = collapse_word_repeats(title, platform.max_word_repeats)
        if collapsed != title:
            title = collapsed
            changed = True
            issues.append("collapsed:title_repeats")

    if platform.max_word_length is not None:
        limited = enforce_word_length(title, platform.max_word_length)
        if limited != title:
            title = limited
            changed = True
            issues.append("trimmed:title_word_length")

    if len(title) > platform.max_title:
        overshoot = (original_len - platform.max_title) / platform.max_title
        title = trim_to_limit(title, platform.max_title)
        changed = True
        issues.append(f"trimmed:title:{original_len}->{platform.max_title}")
        if overshoot > OVERSHOOT_RATIO:
            issues.append("repair:title_overshoot")

    return title, changed, issues


def _apply_description_rules(
    description: str, platform: PlatformRulePack
) -> tuple[str, bool, list[str]]:
    issues: list[str] = []
    changed = False
    original_len = len(description)

    if len(description) > platform.max_description:
        overshoot = (original_len - platform.max_description) / platform.max_description
        description = trim_to_limit(description, platform.max_description)
        changed = True
        issues.append(f"trimmed:description:{original_len}->{platform.max_description}")
        if overshoot > OVERSHOOT_RATIO:
            issues.append("repair:description_overshoot")
    elif original_len < platform.target_description_min:
        issues.append("repair:description_short")

    return description, changed, issues


def _clean_phrases(items: list[str], platform: PlatformRulePack) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for raw in items:
        phrase = sanitize_text(raw, strip_hashtags=platform.strip_hashtags)
        phrase = phrase.strip(" ,.;:#")
        key = phrase.lower()
        if not phrase or key in seen:
            continue
        if _banned_hits(phrase, platform):
            continue
        seen.add(key)
        result.append(phrase)
    return result


def _banned_hits(text: str, platform: PlatformRulePack) -> list[str]:
    lowered = text.lower()
    hits: list[str] = []
    for token in (*GLOBAL_BANNED, *platform.banned_substrings):
        if token.lower() in lowered and token not in hits:
            hits.append(token)
    return hits


def _normalize_caps(text: str) -> str:
    parts: list[str] = []
    for word in text.split():
        letters = [char for char in word if char.isalpha()]
        if len(letters) > 3 and word.isupper():
            parts.append(word.capitalize())
        else:
            parts.append(word)
    return " ".join(parts)
