"""Reply keyboards used by the Telegram bot."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Текущие итоги")],
        [KeyboardButton(text="✅ Подвести итог дня")],
        [KeyboardButton(text="ℹ️ Справка")],
    ],
    resize_keyboard=True,
)
