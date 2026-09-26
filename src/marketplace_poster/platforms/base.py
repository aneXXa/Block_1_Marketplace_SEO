from dataclasses import dataclass
from enum import StrEnum


class PlatformId(StrEnum):
    WILDBERRIES = "wildberries"
    OZON = "ozon"
    AVITO = "avito"


@dataclass(frozen=True)
class PlatformRulePack:
    """Жёсткие правила площадки: лимиты живут здесь, не в промпте модели."""

    id: PlatformId
    display_name: str
    max_title: int
    target_title_min: int
    target_title_max: int
    max_description: int
    target_description_min: int
    target_description_max: int
    min_tags: int
    max_tags: int
    title_formula: str
    extra_instructions: str
    max_word_length: int | None = None
    max_word_repeats: int | None = None
    banned_substrings: tuple[str, ...] = ()
    strip_hashtags: bool = False
    search_indexes_description: bool = True
