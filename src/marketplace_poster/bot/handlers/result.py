from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from marketplace_poster.bot.formatters import field_plain
from marketplace_poster.bot.handlers.pipeline import package_from_state, run_generation
from marketplace_poster.bot.states import GenerateStates
from marketplace_poster.services.generation import GenerationService

router = Router()


@router.callback_query(GenerateStates.result, F.data == "regen")
@router.callback_query(GenerateStates.result, F.data == "retry")
async def regenerate(
    call: CallbackQuery,
    state: FSMContext,
    generator: GenerationService,
) -> None:
    if call.message is None:
        await call.answer()
        return
    await call.answer("Пересобираю…")
    keep = call.data == "regen"
    await run_generation(call.message, state, generator, keep_variation=keep)


@router.callback_query(GenerateStates.result, F.data.startswith("copy:"))
async def send_copy_chunk(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    package = package_from_state(data)
    if package is None or call.message is None:
        await call.answer("Сначала сгенерируйте пакет", show_alert=True)
        return
    field = (call.data or "").split(":", 1)[1]
    await call.message.answer(field_plain(package, field))
    await call.answer("Текст в чате — долгий тап → копировать")
