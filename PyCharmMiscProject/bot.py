import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

async def main():
    print("=" * 60)
    print("   IITU Schedule Bot — Starting Up")
    print("=" * 60)
    from dotenv import load_dotenv
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("❌ BOT_TOKEN не найден в .env файле!")
        sys.exit(1)

    logger.info("✅ BOT_TOKEN загружен")

    from aiogram import Bot, Dispatcher
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.filters import CommandStart, Command
    from aiogram.types import Message, CallbackQuery
    from inline import main_keyboard, days_inline
    from schedule import get_schedule, TEACHERS, SUBJECTS
    from database import save_user, save_message, save_activity

    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    @dp.message(CommandStart())
    async def cmd_start(message: Message):
        save_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )
        save_activity(message.from_user.id, "start")

        await message.answer(
            f"👋 Привет, *{message.from_user.first_name}*!\n\n"
            "🎓 Я бот расписания *IITU*\n\n"
            "Используй кнопки ниже 👇",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

    @dp.message(Command("help"))
    @dp.message(lambda m: m.text == "❓ Помощь")
    async def cmd_help(message: Message):
        save_message(message.from_user.id, "/help")
        save_activity(message.from_user.id, "help")

        await message.answer(
            "📚 *Команды бота:*\n\n"
            "/today — сегодня\n"
            "/tomorrow — завтра\n"
            "/week — вся неделя\n"
            "/monday — понедельник\n"
            "/tuesday — вторник\n"
            "/wednesday — среда\n"
            "/thursday — четверг\n"
            "/friday — пятница\n"
            "/saturday — суббота\n"
            "/teachers — преподаватели\n"
            "/subjects — предметы",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

    @dp.message(Command("today"))
    @dp.message(lambda m: m.text == "📅 Сегодня")
    async def cmd_today(message: Message):
        save_message(message.from_user.id, "/today")
        save_activity(message.from_user.id, "view_today")

        days = {0: "Понедельник", 1: "Вторник", 2: "Среда",
                3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье"}
        today = datetime.now().weekday()
        await message.answer(
            f"📅 *{days[today]}*\n\n{get_schedule(today)}",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

    @dp.message(Command("tomorrow"))
    @dp.message(lambda m: m.text == "📅 Завтра")
    async def cmd_tomorrow(message: Message):
        save_message(message.from_user.id, "/tomorrow")
        save_activity(message.from_user.id, "view_tomorrow")

        days = {0: "Понедельник", 1: "Вторник", 2: "Среда",
                3: "Четверг", 4: "Пятница", 5: "Суббота", 6: "Воскресенье"}
        tomorrow = (datetime.now() + timedelta(days=1)).weekday()
        await message.answer(
            f"📅 *{days[tomorrow]}*\n\n{get_schedule(tomorrow)}",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

    @dp.message(Command("week"))
    @dp.message(lambda m: m.text == "📆 Вся неделя")
    async def cmd_week(message: Message):
        save_message(message.from_user.id, "/week")
        save_activity(message.from_user.id, "view_week")

        await message.answer(
            "📆 *Расписание на неделю*\n\nВыбери день 👇",
            parse_mode="Markdown",
            reply_markup=days_inline()
        )

    @dp.message(Command("monday"))
    async def cmd_monday(message: Message):
        save_activity(message.from_user.id, "view_monday")
        await message.answer(f"📅 *Понедельник*\n\n{get_schedule(0)}", parse_mode="Markdown", reply_markup=main_keyboard())

    @dp.message(Command("tuesday"))
    async def cmd_tuesday(message: Message):
        save_activity(message.from_user.id, "view_tuesday")
        await message.answer(f"📅 *Вторник*\n\n{get_schedule(1)}", parse_mode="Markdown", reply_markup=main_keyboard())

    @dp.message(Command("wednesday"))
    async def cmd_wednesday(message: Message):
        save_activity(message.from_user.id, "view_wednesday")
        await message.answer(f"📅 *Среда*\n\n{get_schedule(2)}", parse_mode="Markdown", reply_markup=main_keyboard())

    @dp.message(Command("thursday"))
    async def cmd_thursday(message: Message):
        save_activity(message.from_user.id, "view_thursday")
        await message.answer(f"📅 *Четверг*\n\n{get_schedule(3)}", parse_mode="Markdown", reply_markup=main_keyboard())

    @dp.message(Command("friday"))
    async def cmd_friday(message: Message):
        save_activity(message.from_user.id, "view_friday")
        await message.answer(f"📅 *Пятница*\n\n{get_schedule(4)}", parse_mode="Markdown", reply_markup=main_keyboard())

    @dp.message(Command("saturday"))
    async def cmd_saturday(message: Message):
        save_activity(message.from_user.id, "view_saturday")
        await message.answer(f"📅 *Суббота*\n\n{get_schedule(5)}", parse_mode="Markdown", reply_markup=main_keyboard())

    @dp.message(Command("teachers"))
    @dp.message(lambda m: m.text == "👨‍🏫 Преподаватели")
    async def cmd_teachers(message: Message):
        save_message(message.from_user.id, "/teachers")
        save_activity(message.from_user.id, "view_teachers")

        text = "👨‍🏫 *Преподаватели:*\n\n" + "\n".join(TEACHERS)
        await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard())

    @dp.message(Command("subjects"))
    @dp.message(lambda m: m.text == "📚 Предметы")
    async def cmd_subjects(message: Message):
        save_message(message.from_user.id, "/subjects")
        save_activity(message.from_user.id, "view_subjects")

        text = "📚 *Предметы:*\n\n" + "\n".join(SUBJECTS)
        await message.answer(text, parse_mode="Markdown", reply_markup=main_keyboard())

    @dp.callback_query(lambda c: c.data.startswith("day_"))
    async def callback_day(callback: CallbackQuery):
        days = {0: "Понедельник", 1: "Вторник", 2: "Среда",
                3: "Четверг", 4: "Пятница", 5: "Суббота"}
        day_num = int(callback.data.split("_")[1])
        save_activity(callback.from_user.id, f"view_day_{day_num}")

        await callback.message.answer(
            f"📅 *{days[day_num]}*\n\n{get_schedule(day_num)}",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        await callback.answer()

    @dp.message()
    async def unknown(message: Message):
        save_message(message.from_user.id, f"unknown: {message.text}")
        save_activity(message.from_user.id, "unknown_command")

        await message.answer(
            f"❓ Не понимаю: «{message.text[:50]}»\n\n"
            "Напиши /help или используй кнопки 👇",
            reply_markup=main_keyboard()
        )

    logger.info("✅ Все обработчики зарегистрированы")
    print("\n🤖 Бот успешно запущен! Нажмите Ctrl+C для остановки.\n")

    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
    finally:
        await bot.session.close()
        logger.info("👋 Бот завершил работу")

if __name__ == "__main__":
    asyncio.run(main())