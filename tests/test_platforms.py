from marketplace_poster.llm.prompts import build_system_prompt
from marketplace_poster.platforms import AVITO, OZON, PLATFORMS, WILDBERRIES, get_platform


def test_registry_has_three_distinct_title_limits() -> None:
    limits = {pack.id: pack.max_title for pack in PLATFORMS.values()}
    assert limits[WILDBERRIES.id] == 60
    assert limits[OZON.id] == 200
    assert limits[AVITO.id] == 50
    assert len(set(limits.values())) == 3


def test_get_platform_accepts_string() -> None:
    assert get_platform("ozon") is OZON
    assert get_platform(AVITO.id) is AVITO


def test_prompts_encode_platform_rules() -> None:
    wb = build_system_prompt(WILDBERRIES)
    ozon = build_system_prompt(OZON)
    avito = build_system_prompt(AVITO)
    assert "первых 40" in wb
    assert "НЕ индексируется" in ozon
    assert "Первые 200" in avito
    assert wb != ozon != avito
    assert OZON.search_indexes_description is False
    assert WILDBERRIES.search_indexes_description is True
