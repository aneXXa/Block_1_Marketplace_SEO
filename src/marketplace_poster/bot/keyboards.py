from aiogram.types import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup

from marketplace_poster.bot.formatters import copyable, field_plain
from marketplace_poster.models.seo_package import SeoPackage
from marketplace_poster.platforms import PLATFORMS, PlatformId, PlatformRulePack


def platform_keyboard(*, exclude: PlatformId | None = None) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for pack in PLATFORMS.values():
        if exclude is not None and pack.id == exclude:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=pack.display_name,
                    callback_data=f"platform:{pack.id}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def collect_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Без фото", callback_data="skip_photo")],
            [InlineKeyboardButton(text="Сменить площадку", callback_data="switch")],
        ]
    )


def retry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Повторить", callback_data="retry")],
            [InlineKeyboardButton(text="Новый товар", callback_data="new")],
        ]
    )


def result_keyboard(package: SeoPackage, platform: PlatformRulePack) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [_copy_or_send("Копировать заголовок", "title", field_plain(package, "title"))],
        [_copy_or_send("Копировать описание", "description", field_plain(package, "description"))],
        [_copy_or_send("Копировать теги", "tags", field_plain(package, "tags"))],
        [_copy_or_send("Копировать всё", "all", field_plain(package, "all"))],
        [
            InlineKeyboardButton(text="Перегенерировать", callback_data="regen"),
            InlineKeyboardButton(text="Другая площадка", callback_data="switch"),
        ],
        [InlineKeyboardButton(text="Новый товар", callback_data="new")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _copy_or_send(label: str, field: str, text: str) -> InlineKeyboardButton:
    if copyable(text):
        return InlineKeyboardButton(text=label, copy_text=CopyTextButton(text=text))
    return InlineKeyboardButton(text=f"{label} → чат", callback_data=f"copy:{field}")
