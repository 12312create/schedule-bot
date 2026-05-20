import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart

from inline import (
    get_main_keyboard,
    get_notifications_inline_keyboard,
    get_profile_inline_keyboard,
    get_back_keyboard,
)
from states import ProfileStates, ReminderStates
from aiogram.fsm.context import FSMContext
logger = logging.getLogger(__name__)
router = Router(name="common")

async def _get_db():
    from database.db import get_db
    return get_db()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    try:
        db = await _get_db()
        user_data = await db.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        await db.save_message(user.id, "in", "/start", "/start")
        await db.log_activity(user.id, "start", "Bot started")

        is_new = user_data.get("created_at") and (
            (datetime.now() - user_data["created_at"].replace(tzinfo=None)).seconds < 10
        )
        greeting = "Добро пожаловать" if is_new else "С возвращением"

    except Exception as e:
        logger.error(f"/start DB error: {e}")
        greeting = "Добро пожаловать"

    name = user.first_name or user.username or "Студент"

    text = (
        f"👋 {greeting}, *{name}*!\n\n"
        f"🎓 Я — бот расписания *IITU*.\n\n"
        f"📅 Я помогу тебе:\n"
        f"• Узнать расписание на сегодня и завтра\n"
        f"• Просмотреть расписание на неделю\n"
        f"• Получать напоминания о парах\n"
        f"• Смотреть погоду и новости IITU\n\n"
        f"Используй кнопки ниже или команду /help для начала. 🚀"
    )
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )

@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    try:
        db = await _get_db()
        await db.save_message(message.from_user.id, "in", "/help", "/help")
        await db.log_activity(message.from_user.id, "help")
    except Exception:
        pass
    text = (
        "📚 *Помощь — IITU Schedule Bot*\n\n"
        "━━━ 📅 Расписание ━━━\n"
        "/today — расписание *на сегодня*\n"
        "/tomorrow — расписание *на завтра*\n"
        "/week — расписание *на неделю*\n\n"
        "━━━ 📆 По дням ━━━\n"
        "/monday — понедельник\n"
        "/tuesday — вторник\n"
        "/wednesday — среда\n"
        "/thursday — четверг\n"
        "/friday — пятница\n"
        "/saturday — суббота\n\n"
        "━━━ ℹ️ Информация ━━━\n"
        "/teachers — список преподавателей\n"
        "/subjects — список предметов\n"
        "/profile — мой профиль\n"
        "/notifications — настройки уведомлений\n\n"
        "━━━ ❓ Прочее ━━━\n"
        "/help — это сообщение\n"
        "/start — перезапустить бота\n\n"
        "_Также можно использовать кнопки внизу экрана_ 👇"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )

@router.message(Command("teachers"))
@router.message(F.text == "👨‍🏫 Преподаватели")
async def cmd_teachers(message: Message):
    try:
        db = await _get_db()
        teachers = await db.get_all_teachers()
        await db.log_activity(message.from_user.id, "view_teachers")
        if not teachers:
            await message.answer("ℹ️ Список преподавателей пуст.")
            return
        lines = ["👨‍🏫 *Преподаватели IITU*\n"]
        for i, teacher in enumerate(sorted(teachers), 1):
            lines.append(f"{i}. {teacher}")
        await message.answer(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(),
        )
    except Exception as e:
        logger.error(f"/teachers error: {e}")
        await message.answer("❌ Ошибка при загрузке списка преподавателей.")

@router.message(Command("subjects"))
@router.message(F.text == "📚 Предметы")
async def cmd_subjects(message: Message):
    try:
        db = await _get_db()
        subjects = await db.get_all_subjects()
        await db.log_activity(message.from_user.id, "view_subjects")

        if not subjects:
            await message.answer("ℹ️ Список предметов пуст.")
            return

        lines = ["📚 *Предметы в расписании*\n"]
        for i, subject in enumerate(subjects, 1):
            lines.append(f"{i}. {subject}")

        await message.answer(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(),
        )
    except Exception as e:
        logger.error(f"/subjects error: {e}")
        await message.answer("❌ Ошибка при загрузке списка предметов.")

@router.message(Command("notifications"))
@router.message(F.text == "🔔 Уведомления")
async def cmd_notifications(message: Message):
    try:
        db = await _get_db()
        await db.log_activity(message.from_user.id, "view_notifications")

        unread = await db.get_unread_notifications(message.from_user.id)
        unread_count = len(unread)

        text = (
            "🔔 *Настройки уведомлений*\n\n"
            f"📬 Непрочитанных уведомлений: *{unread_count}*\n\n"
        )

        if unread:
            text += "📋 *Последние уведомления:*\n"
            for notif in unread[:3]:
                text += f"• {notif['title']}: {notif['body'][:60]}\n"
            text += "\n"
            await db.mark_notifications_read(message.from_user.id)

        text += (
            "Выберите действие:\n"
            "🔔 Включить — получать напоминания о парах\n"
            "🔕 Выключить — отключить уведомления"
        )
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_notifications_inline_keyboard(enabled=True),
        )
    except Exception as e:
        logger.error(f"/notifications error: {e}")
        await message.answer("❌ Ошибка настроек уведомлений.")

@router.callback_query(lambda c: c.data in ("notif_on", "notif_off"))
async def callback_notifications(callback: CallbackQuery):
    enabled = callback.data == "notif_on"
    action_text = "включены ✅" if enabled else "отключены 🔕"

    try:
        db = await _get_db()
        await db.add_notification(
            callback.from_user.id,
            "Настройки уведомлений",
            f"Уведомления {action_text}",
            "settings",
        )
        await db.log_activity(
            callback.from_user.id, "toggle_notifications", str(enabled)
        )
    except Exception as e:
        logger.error(f"Notification toggle error: {e}")
    await callback.message.edit_text(
        f"🔔 Уведомления {action_text}\n\n"
        "Вы можете изменить настройки в любое время через /notifications",
        parse_mode="Markdown",
        reply_markup=get_notifications_inline_keyboard(enabled=enabled),
    )
    await callback.answer(f"Уведомления {action_text}")

@router.message(Command("profile"))
@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: Message):
    user = message.from_user
    try:
        db = await _get_db()
        user_data = await db.get_user(user.id)
        await db.log_activity(user.id, "view_profile")
        if not user_data:
            await message.answer(
                "❌ Профиль не найден. Нажмите /start для регистрации."
            )
            return
        created = user_data.get("created_at")
        if created:
            created_str = created.strftime("%d.%m.%Y")
        else:
            created_str = "Неизвестно"
        text = (
            f"👤 *Мой профиль*\n\n"
            f"🆔 ID: `{user.id}`\n"
            f"👤 Имя: {user_data.get('first_name') or '—'} {user_data.get('last_name') or ''}\n"
            f"📱 Username: @{user_data.get('username') or '—'}\n"
            f"✉️ Email: {user_data.get('email') or '—'}\n"
            f"📞 Телефон: {user_data.get('phone') or '—'}\n"
            f"🎓 Группа: {user_data.get('group_name', 'SE-2310')}\n"
            f"📅 Зарегистрирован: {created_str}\n"
        )
        await message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=get_profile_inline_keyboard(),
        )
    except Exception as e:
        logger.error(f"/profile error: {e}")
        await message.answer("❌ Ошибка загрузки профиля.")

@router.callback_query(lambda c: c.data == "edit_email")
async def callback_edit_email(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "✉️ Введите новый email-адрес:\n\n"
        "_Например: student@iitu.edu.kz_",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard(),
    )
    await state.set_state(ProfileStates.waiting_email)
    await callback.answer()

@router.message(ProfileStates.waiting_email)
async def process_email_input(message: Message, state: FSMContext):
    from validators import validate_email, sanitize_input

    email = sanitize_input(message.text or "")

    if not email:
        await message.answer("❌ Email не может быть пустым. Попробуйте ещё раз.")
        return

    if not validate_email(email):
        await message.answer(
            "❌ Некорректный email-адрес.\n"
            "Пример правильного: student@iitu.edu.kz\n\n"
            "Попробуйте ещё раз:"
        )
        return

    try:
        db = await _get_db()
        await db.update_user_email(message.from_user.id, email)
        await state.clear()
        await message.answer(
            f"✅ Email успешно обновлён: `{email}`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(),
        )
    except Exception as e:
        logger.error(f"Email update error: {e}")
        await message.answer("❌ Ошибка сохранения email.")
        await state.clear()

@router.callback_query(lambda c: c.data == "edit_phone")
async def callback_edit_phone(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📱 Введите номер телефона:\n\n"
        "_Например: +77012345678_",
        parse_mode="Markdown",
        reply_markup=get_back_keyboard(),
    )
    await state.set_state(ProfileStates.waiting_phone)
    await callback.answer()

@router.message(ProfileStates.waiting_phone)
async def process_phone_input(message: Message, state: FSMContext):
    from validators import validate_phone, normalize_phone, sanitize_input
    phone = sanitize_input(message.text or "")
    if not phone:
        await message.answer("❌ Номер не может быть пустым.")
        return
    if not validate_phone(phone):
        await message.answer(
            "❌ Некорректный номер телефона.\n"
            "Пример: +77012345678 или 87012345678\n\n"
            "Попробуйте ещё раз:"
        )
        return
    normalized = normalize_phone(phone)
    try:
        db = await _get_db()
        await db.update_user_phone(message.from_user.id, normalized)
        await state.clear()
        await message.answer(
            f"✅ Телефон успешно обновлён: `{normalized}`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(),
        )
    except Exception as e:
        logger.error(f"Phone update error: {e}")
        await message.answer("❌ Ошибка сохранения номера.")
        await state.clear()

@router.callback_query(lambda c: c.data == "msg_history")
async def callback_message_history(callback: CallbackQuery):
    try:
        db = await _get_db()
        history = await db.get_message_history(callback.from_user.id, limit=10)
        if not history:
            await callback.message.answer("📋 История сообщений пуста.")
            await callback.answer()
            return
        lines = ["📋 *Последние 10 сообщений:*\n"]
        for msg in reversed(history):
            direction = "➡️" if msg["direction"] == "in" else "⬅️"
            time_str = msg["created_at"].strftime("%d.%m %H:%M")
            content = msg["content"][:50]
            lines.append(f"{direction} `{time_str}` {content}")

        await callback.message.answer(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(),
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Message history error: {e}")
        await callback.answer("❌ Ошибка загрузки истории", show_alert=True)

@router.callback_query(lambda c: c.data == "weather")
async def callback_weather(callback: CallbackQuery):
    try:
        from weather import get_weather_api
        api = get_weather_api()
        weather = api.get_current_weather()
        text = api.format_weather_message(weather)
        await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error(f"Weather callback error: {e}")
        await callback.answer("❌ Ошибка получения погоды", show_alert=True)

@router.callback_query(lambda c: c.data == "news")
async def callback_news(callback: CallbackQuery):
    await callback.answer("⏳ Загружаю новости...")
    try:
        from bot import get_scraper
        scraper = get_scraper()
        news = scraper.scrape_news(max_items=5)
        text = scraper.format_news_for_bot(news)
        await callback.message.answer(text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"News callback error: {e}")
        await callback.message.answer("❌ Ошибка загрузки новостей.")

@router.message(F.text == "🏠 Главное меню")
async def cmd_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_keyboard(),
    )

@router.callback_query(lambda c: c.data == "cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "❌ Действие отменено.",
        reply_markup=get_main_keyboard(),
    )
    await callback.answer()

@router.message()
async def unknown_message(message: Message):
    from validators import is_empty_input

    text = message.text or ""

    if is_empty_input(text):
        await message.answer(
            "❓ Вы отправили пустое сообщение.\n"
            "Используйте /help для списка команд.",
            reply_markup=get_main_keyboard(),
        )
        return
    if text.startswith("/"):
        await message.answer(
            f"❓ Неизвестная команда: `{text[:30]}`\n\n"
            "Используйте /help для просмотра доступных команд.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(),
        )
        return
    try:
        db = await _get_db()
        await db.save_message(message.from_user.id, "in", text, None)
    except Exception:
        pass
    await message.answer(
        f"🤔 Я не понял: «{text[:50]}»\n\n"
        "Попробуйте:\n"
        "📅 /today — расписание сегодня\n"
        "📆 /week — расписание на неделю\n"
        "❓ /help — список команд",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
    )