from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from marketplace_poster.bot.handlers import setup_routers
from marketplace_poster.services.generation import GenerationService


def create_dispatcher(generator: GenerationService) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.workflow_data.update(generator=generator)
    dispatcher.include_router(setup_routers())
    return dispatcher
