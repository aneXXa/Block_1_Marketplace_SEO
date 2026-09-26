from marketplace_poster.bot.formatters import format_result_html
from marketplace_poster.llm.prompts import build_system_prompt, build_user_prompt, variation_hint
from marketplace_poster.platforms import PLATFORMS
from marketplace_poster.preview import GOLDEN_PACKAGES, SAMPLE_BRIEF, preview_sku
from marketplace_poster.services.occasions import suggest_occasions
from marketplace_poster.services.validation import validate_package

WATER_WORDS = ("лучший", "уникальный", "идеальный", "must have", "премиум качества")


def test_same_sku_three_platforms() -> None:
    rendered = preview_sku()
    assert set(rendered) == {"wildberries", "ozon", "avito"}
    titles = [GOLDEN_PACKAGES[pack.id].title for pack in PLATFORMS.values()]
    assert len(set(titles)) == 3


def test_golden_packages_pass_local_rules() -> None:
    for platform in PLATFORMS.values():
        package = GOLDEN_PACKAGES[platform.id]
        result = validate_package(package, platform)
        assert not result.needs_llm_repair, result.issues
        assert platform.target_title_min <= len(result.package.title) <= platform.max_title
        assert len(result.package.description) >= platform.target_description_min
        blob = f"{package.title}\n{package.description}".lower()
        for word in WATER_WORDS:
            assert word not in blob
        html = format_result_html(result.package, platform)
        assert platform.display_name in html
        assert f"/{platform.max_title}" in html


def test_occasion_hints_from_facts() -> None:
    hints = suggest_occasions(SAMPLE_BRIEF.facts)
    assert "подарок коллеге" in hints


def test_user_prompt_mentions_detected_occasion() -> None:
    ozon = next(pack for pack in PLATFORMS.values() if pack.id.value == "ozon")
    prompt = build_user_prompt(ozon, SAMPLE_BRIEF)
    assert "подарок коллеге" in prompt
    assert "Nordveil" in prompt


def test_variation_hints_cycle() -> None:
    assert variation_hint(0) is None
    assert variation_hint(1) != variation_hint(2)
    assert "угол" in (variation_hint(1) or "")


def test_system_prompts_forbid_invention() -> None:
    for platform in PLATFORMS.values():
        prompt = build_system_prompt(platform)
        assert "выдумывать" in prompt
        assert "JSON" in prompt
