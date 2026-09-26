from io import BytesIO

from aiogram import Bot


async def download_telegram_file(bot: Bot, file_id: str) -> bytes:
    buffer = BytesIO()
    await bot.download(file_id, destination=buffer)
    return buffer.getvalue()
