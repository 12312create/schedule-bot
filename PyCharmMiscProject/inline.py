from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📅 Завтра")],
            [KeyboardButton(text="📆 Вся неделя")],
            [KeyboardButton(text="👨‍🏫 Преподаватели"), KeyboardButton(text="📚 Предметы")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True
    )
    return keyboard

def days_inline() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Пн", callback_data="day_0"),
            InlineKeyboardButton(text="Вт", callback_data="day_1"),
            InlineKeyboardButton(text="Ср", callback_data="day_2"),
        ],
        [
            InlineKeyboardButton(text="Чт", callback_data="day_3"),
            InlineKeyboardButton(text="Пт", callback_data="day_4"),
            InlineKeyboardButton(text="Сб", callback_data="day_5"),
        ],
    ])
    return keyboard