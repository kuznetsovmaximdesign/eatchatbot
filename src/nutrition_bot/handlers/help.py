"""Help message handler."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
@router.message(F.text.casefold() == "ℹ️ справка".casefold())
async def send_help(message: Message) -> None:
    await message.answer(
        "Просто напиши, что съел, например: 'курица 150, рис 80'.\n"
        "Цифры — это граммы. Можно отправлять фото, я уточню детали."
    )
