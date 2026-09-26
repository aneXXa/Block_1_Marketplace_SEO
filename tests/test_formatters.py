from marketplace_poster.bot.formatters import (
    COPY_TEXT_LIMIT,
    copyable,
    field_plain,
    format_plain_package,
    format_result_html,
)
from marketplace_poster.bot.keyboards import result_keyboard
from marketplace_poster.platforms import WILDBERRIES
from marketplace_poster.preview import GOLDEN_PACKAGES


def test_html_escapes_and_shows_counters() -> None:
    package = GOLDEN_PACKAGES[WILDBERRIES.id].model_copy(
        update={"title": "Худи <script>"}
    )
    html = format_result_html(package, WILDBERRIES)
    assert "&lt;script&gt;" in html
    assert f"{len(package.title)}/{WILDBERRIES.max_title}" in html


def test_plain_contains_all_fields() -> None:
    package = GOLDEN_PACKAGES[WILDBERRIES.id]
    plain = format_plain_package(package)
    assert package.title in plain
    assert package.description in plain
    assert "Теги:" in plain


def test_copyable_respects_telegram_limit() -> None:
    assert copyable("короткий")
    assert not copyable("x" * (COPY_TEXT_LIMIT + 1))


def test_field_plain_all() -> None:
    package = GOLDEN_PACKAGES[WILDBERRIES.id]
    assert field_plain(package, "title") == package.title
    assert package.title in field_plain(package, "all")


def test_long_description_uses_callback_not_copy_text() -> None:
    package = GOLDEN_PACKAGES[WILDBERRIES.id]
    markup = result_keyboard(package, WILDBERRIES)
    description_btn = markup.inline_keyboard[1][0]
    if copyable(package.description):
        assert description_btn.copy_text is not None
    else:
        assert description_btn.callback_data == "copy:description"
    title_btn = markup.inline_keyboard[0][0]
    assert title_btn.copy_text is not None
    assert title_btn.copy_text.text == package.title
