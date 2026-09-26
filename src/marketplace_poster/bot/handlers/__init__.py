from aiogram import Router

from marketplace_poster.bot.handlers import collect, result, start


def setup_routers() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(result.router)
    root.include_router(collect.router)
    return root
