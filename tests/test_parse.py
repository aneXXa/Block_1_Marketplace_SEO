import pytest

from marketplace_poster.llm.parse import SeoParseError, parse_seo_package

VALID = """{"title": "Худи мужское", "description": "Текст", "tags": ["худи"], "attributes": []}"""


def test_plain_json() -> None:
    package = parse_seo_package(VALID)
    assert package.title == "Худи мужское"
    assert package.tags == ["худи"]


def test_markdown_fence() -> None:
    package = parse_seo_package(f"```json\n{VALID}\n```")
    assert package.title == "Худи мужское"


def test_prose_around_json() -> None:
    package = parse_seo_package(f"Вот пакет:\n{VALID}\nГотово.")
    assert package.description == "Текст"


def test_tags_as_comma_string() -> None:
    raw = '{"title": "А", "description": "Б", "tags": "худи, оверсайз", "attributes": null}'
    package = parse_seo_package(raw)
    assert package.tags == ["худи", "оверсайз"]
    assert package.attributes == []


def test_empty_raises() -> None:
    with pytest.raises(SeoParseError):
        parse_seo_package("   ")


def test_broken_json_raises() -> None:
    with pytest.raises(SeoParseError):
        parse_seo_package("это не json")
