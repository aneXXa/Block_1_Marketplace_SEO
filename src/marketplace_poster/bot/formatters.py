from __future__ import annotations

from html import escape

from marketplace_poster.models.seo_package import SeoPackage
from marketplace_poster.platforms.base import PlatformRulePack

COPY_TEXT_LIMIT = 256


def format_result_html(package: SeoPackage, platform: PlatformRulePack) -> str:
    tags = ", ".join(package.tags) if package.tags else "—"
    attributes = ", ".join(package.attributes) if package.attributes else "—"
    return (
        f"<b>{escape(platform.display_name)}</b> · SEO-пакет\n\n"
        f"📌 <b>Заголовок</b> ({len(package.title)}/{platform.max_title})\n"
        f"{escape(package.title)}\n\n"
        f"📝 <b>Описание</b> ({len(package.description)}/{platform.max_description})\n"
        f"{escape(package.description)}\n\n"
        f"🏷 <b>Теги</b>\n{escape(tags)}\n\n"
        f"📋 <b>Характеристики</b>\n{escape(attributes)}"
    )


def format_plain_package(package: SeoPackage) -> str:
    lines = [
        "Заголовок:",
        package.title,
        "",
        "Описание:",
        package.description,
        "",
        "Теги:",
        ", ".join(package.tags),
    ]
    if package.attributes:
        lines.extend(["", "Характеристики:", ", ".join(package.attributes)])
    return "\n".join(lines)


def copyable(text: str) -> bool:
    return 0 < len(text) <= COPY_TEXT_LIMIT


def field_plain(package: SeoPackage, field: str) -> str:
    if field == "title":
        return package.title
    if field == "description":
        return package.description
    if field == "tags":
        return ", ".join(package.tags)
    if field == "all":
        return format_plain_package(package)
    raise KeyError(field)
