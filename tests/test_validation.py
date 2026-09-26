from marketplace_poster.models.seo_package import SeoPackage
from marketplace_poster.platforms import AVITO, OZON, WILDBERRIES
from marketplace_poster.services.validation import (
    collapse_word_repeats,
    trim_to_limit,
    validate_package,
)


def _pkg(**overrides: object) -> SeoPackage:
    data = {
        "title": "Худи мужское оверсайз хлопок",
        "description": "Мужское худи для повседневной носки.",
        "tags": ["худи", "оверсайз", "хлопок", "капюшон", "подарок коллеге"],
        "attributes": ["мужской"],
    }
    data.update(overrides)
    return SeoPackage.model_validate(data)


def test_trim_to_limit_word_boundary() -> None:
    assert trim_to_limit("худи мужское оверсайз", 12) == "худи"


def test_wb_title_hard_limit() -> None:
    title = "Х " * 40
    result = validate_package(_pkg(title=title), WILDBERRIES)
    assert len(result.package.title) <= 60
    assert any(issue.startswith("trimmed:title") for issue in result.issues)


def test_wb_title_overshoot_marks_repair() -> None:
    title = "а" * 80
    result = validate_package(_pkg(title=title), WILDBERRIES)
    assert result.needs_llm_repair
    assert "repair:title_overshoot" in result.issues


def test_avito_title_limit_50() -> None:
    result = validate_package(
        _pkg(title="Худи мужское оверсайз хлопок чёрное с капюшоном кенгуру"),
        AVITO,
    )
    assert len(result.package.title) <= 50
    assert any(issue.startswith("trimmed:title") for issue in result.issues)


def test_strips_emoji_and_urls() -> None:
    result = validate_package(
        _pkg(title="Худи 🔥 мужское", description="Смотрите www.example.com и ещё текст"),
        WILDBERRIES,
    )
    assert "🔥" not in result.package.title
    assert "www.example.com" not in result.package.description


def test_ozon_collapses_word_repeats() -> None:
    title = collapse_word_repeats("Кружка кружка кружка для кофе", 2)
    assert title.lower().count("кружка") == 2
    result = validate_package(_pkg(title="Кружка кружка кружка керамика"), OZON)
    assert result.package.title.lower().count("кружка") <= 2


def test_ozon_enforces_word_length() -> None:
    long_word = "а" * 40
    result = validate_package(_pkg(title=f"Кружка {long_word}"), OZON)
    assert all(len(word) <= 27 for word in result.package.title.split())


def test_avito_strips_hashtags() -> None:
    result = validate_package(_pkg(tags=["#худи", "оверсайз"]), AVITO)
    assert result.package.tags[0] == "худи"


def test_banned_tokens_request_repair() -> None:
    result = validate_package(_pkg(description="Это лучший в мире худи"), WILDBERRIES)
    assert result.needs_llm_repair
    assert any(issue.startswith("repair:banned") for issue in result.issues)


def test_ozon_banned_replica() -> None:
    result = validate_package(_pkg(description="Реплика известного бренда"), OZON)
    assert result.needs_llm_repair


def test_short_description_marks_repair() -> None:
    result = validate_package(_pkg(description="Короткий текст."), WILDBERRIES)
    assert "repair:description_short" in result.issues
