from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from marketplace_poster.bot.keyboards import platform_keyboard

router = Router()

WELCOME = (
    "Готовый SEO-пакет для Wildberries, Ozon и Авито за пару минут: "
    "заголовок, описание и теги под лимиты площадки.\n\n"
    "Выберите площадку."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=platform_keyboard())


@router.callback_query(F.data == "new")
async def new_product(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if call.message:
        await call.message.answer(WELCOME, reply_markup=platform_keyboard())
    await call.answer()
