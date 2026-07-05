from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

menu_router = Router()

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Returns the main persistent reply keyboard."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏆 My Squads"), KeyboardButton(text="📅 Matches")],
            [KeyboardButton(text="➕ Join/Create Squad"), KeyboardButton(text="⚙️ Settings")]
        ],
        resize_keyboard=True,
        is_persistent=True
    )
    return keyboard



@menu_router.message(F.text == "⚙️ Settings")
async def handle_settings(message: Message):
    """Handles the settings button."""
    await message.answer("Settings coming soon! (e.g. language selection)")
