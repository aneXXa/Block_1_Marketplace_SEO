from __future__ import annotations

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from marketplace_poster.bot.formatters import format_result_html
from marketplace_poster.bot.keyboards import result_keyboard, retry_keyboard
from marketplace_poster.bot.media import download_telegram_file
from marketplace_poster.bot.states import GenerateStates
from marketplace_poster.models.seo_package import ProductBrief, SeoPackage
from marketplace_poster.platforms import get_platform
from marketplace_poster.services.generation import GenerationError, GenerationService


async def run_generation(
    message: Message,
    state: FSMContext,
    generator: GenerationService,
    *,
    keep_variation: bool = False,
) -> None:
    data = await state.get_data()
    platform_id = data.get("platform")
    if not platform_id:
        await message.answer("Сначала выберите площадку: /start")
        return

    brief = ProductBrief(
        facts=str(data.get("facts") or ""),
        photo_file_id=data.get("photo_file_id"),
    )
    if not brief.has_signal():
        await message.answer("Нужны фото или хотя бы несколько фактов о товаре.")
        return

    variation = int(data.get("variation_index") or 0)
    if keep_variation:
        variation += 1
        await state.update_data(variation_index=variation)
    else:
        variation = 0
        await state.update_data(variation_index=0)

    status = await message.answer("Собираю SEO-пакет…")

    photo_bytes: bytes | None = None
    try:
        if brief.photo_file_id:
            photo_bytes = await download_telegram_file(message.bot, brief.photo_file_id)
        platform = get_platform(platform_id)
        package, _validation = await generator.generate(
            platform,
            brief,
            photo_bytes=photo_bytes,
            variation_index=variation,
        )
    except GenerationError as exc:
        await status.edit_text(str(exc), reply_markup=retry_keyboard())
        await state.set_state(GenerateStates.result)
        await state.update_data(awaiting="result")
        return
    except Exception:
        await status.edit_text(
            "Что-то сломалось на стороне бота. Нажмите «Повторить» или /start.",
            reply_markup=retry_keyboard(),
        )
        await state.set_state(GenerateStates.result)
        await state.update_data(awaiting="result")
        return

    await state.update_data(last_package=package.model_dump(), awaiting="result")
    await state.set_state(GenerateStates.result)
    await status.edit_text(
        format_result_html(package, platform),
        reply_markup=result_keyboard(package, platform),
        parse_mode="HTML",
    )


def package_from_state(data: dict) -> SeoPackage | None:
    raw = data.get("last_package")
    if not raw:
        return None
    return SeoPackage.model_validate(raw)
