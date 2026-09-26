from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from marketplace_poster.bot.app import create_dispatcher
from marketplace_poster.config import Settings, get_settings
from marketplace_poster.llm.client import build_llm_client
from marketplace_poster.services.generation import GenerationService


def build_app(settings: Settings) -> tuple[Bot, Dispatcher]:
    bot = Bot(token=settings.telegram_bot_token)
    generator = GenerationService(build_llm_client(settings))
    dispatcher = create_dispatcher(generator)
    return bot, dispatcher


async def run_bot() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = get_settings()
    bot, dispatcher = build_app(settings)
    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
