from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from marketplace_poster.bot.handlers.pipeline import run_generation
from marketplace_poster.bot.keyboards import collect_keyboard, platform_keyboard
from marketplace_poster.bot.states import GenerateStates
from marketplace_poster.models.seo_package import ProductBrief
from marketplace_poster.platforms import get_platform
from marketplace_poster.services.generation import GenerationService

router = Router()


@router.callback_query(F.data.startswith("platform:"))
async def choose_platform(
    call: CallbackQuery,
    state: FSMContext,
    generator: GenerationService,
) -> None:
    platform_id = (call.data or "").split(":", 1)[1]
    try:
        platform = get_platform(platform_id)
    except ValueError:
        await call.answer("Неизвестная площадка", show_alert=True)
        return

    data = await state.get_data()
    brief = _brief_from_data(data)
    await state.update_data(platform=platform.id.value)

    if call.message and brief.has_signal() and data.get("awaiting") == "result":
        await state.set_state(GenerateStates.result)
        await call.answer(f"{platform.display_name}")
        await run_generation(call.message, state, generator, keep_variation=False)
        return

    await state.set_state(GenerateStates.collecting)
    await state.update_data(awaiting="collect")
    prompt = (
        f"{platform.display_name}. Пришлите фото товара или сразу факты списком: "
        "тип, бренд, материал, цвет, для кого, повод."
    )
    if call.message:
        await call.message.answer(prompt, reply_markup=collect_keyboard())
    await call.answer()


@router.callback_query(GenerateStates.collecting, F.data == "skip_photo")
async def skip_photo(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(photo_file_id=None)
    if call.message:
        await call.message.answer("Ок, без фото. Напишите факты о товаре списком.")
    await call.answer()


@router.callback_query(F.data == "switch")
async def switch_platform(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    current = data.get("platform")
    exclude = None
    if current:
        try:
            exclude = get_platform(current).id
        except ValueError:
            exclude = None
    if call.message:
        await call.message.answer(
            "Куда пересобрать пакет?",
            reply_markup=platform_keyboard(exclude=exclude),
        )
    await call.answer()


@router.message(GenerateStates.collecting, F.photo)
async def collect_photo(
    message: Message,
    state: FSMContext,
    generator: GenerationService,
) -> None:
    file_id = message.photo[-1].file_id
    caption = (message.caption or "").strip()
    await state.update_data(photo_file_id=file_id)
    if caption:
        await state.update_data(facts=caption)
        await run_generation(message, state, generator)
        return
    await message.answer(
        "Фото принял. Напишите факты списком или ещё раз пришлите фото с подписью."
    )


@router.message(GenerateStates.collecting, F.document)
async def collect_document_image(
    message: Message,
    state: FSMContext,
    generator: GenerationService,
) -> None:
    document = message.document
    if document is None or not (document.mime_type or "").startswith("image/"):
        await message.answer("Нужно фото товара или текст с фактами.")
        return
    caption = (message.caption or "").strip()
    await state.update_data(photo_file_id=document.file_id)
    if caption:
        await state.update_data(facts=caption)
        await run_generation(message, state, generator)
        return
    await message.answer("Изображение принял. Напишите факты списком.")


@router.message(GenerateStates.collecting, F.text)
async def collect_facts(
    message: Message,
    state: FSMContext,
    generator: GenerationService,
) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Напишите факты о товаре.")
        return
    await state.update_data(facts=text)
    await run_generation(message, state, generator)


def _brief_from_data(data: dict) -> ProductBrief:
    return ProductBrief(
        facts=str(data.get("facts") or ""),
        photo_file_id=data.get("photo_file_id"),
    )
