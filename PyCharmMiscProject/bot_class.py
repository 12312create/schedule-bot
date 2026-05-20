import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class BaseBot(ABC):
    _instance_count: int = 0

    def __init__(self, bot_name: str, version: str = "1.0.0"):
        self.__bot_name: str = bot_name
        self.__version: str = version
        self.__created_at: datetime = datetime.now()
        self.__is_running: bool = False
        self._command_count: int = 0
        self._error_count: int = 0
        self._logger = logging.getLogger(self.__class__.__name__)

        BaseBot._instance_count += 1
        self._logger.info(f"🤖 {self.__class__.__name__} '{bot_name}' v{version} initialized")

    def __str__(self) -> str:
        status = "Running" if self.__is_running else "Stopped"
        return (
            f"[{self.__class__.__name__}] "
            f"Name: {self.__bot_name} | "
            f"Version: {self.__version} | "
            f"Status: {status} | "
            f"Commands: {self._command_count}"
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.__bot_name}', version='{self.__version}')"

    @property
    def bot_name(self) -> str:
        return self.__bot_name

    @property
    def version(self) -> str:
        return self.__version

    @property
    def is_running(self) -> bool:
        return self.__is_running

    @is_running.setter
    def is_running(self, value: bool):
        self.__is_running = value
        self._logger.info(f"Bot '{self.__bot_name}' is_running set to {value}")

    @property
    def uptime(self) -> str:
        delta = datetime.now() - self.__created_at
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def stats(self) -> Dict:
        return {
            "name": self.__bot_name,
            "version": self.__version,
            "uptime": self.uptime,
            "commands_processed": self._command_count,
            "errors": self._error_count,
            "is_running": self.__is_running,
        }

    @classmethod
    def get_instance_count(cls) -> int:
        return cls._instance_count

    @abstractmethod
    async def handle_message(self, user_id: int, text: str) -> str:
        pass

    @abstractmethod
    async def handle_command(self, user_id: int, command: str) -> str:
        pass

    @abstractmethod
    def get_help_text(self) -> str:
        pass

    def _increment_commands(self):
        self._command_count += 1

    def _increment_errors(self):
        self._error_count += 1

    def log_command(self, user_id: int, command: str):
        self._increment_commands()
        self._logger.info(f"Command '{command}' from user {user_id} (total: {self._command_count})")

    def handle_unknown_command(self, command: str) -> str:
        self._increment_errors()
        return (
            f"❓ Неизвестная команда: `{command}`\n\n"
            f"Используйте /help для просмотра списка команд."
        )

class ScheduleBot(BaseBot):
    DAY_NAMES = {
        1: "Понедельник",
        2: "Вторник",
        3: "Среда",
        4: "Четверг",
        5: "Пятница",
        6: "Суббота",
        7: "Воскресенье",
    }

    SUBJECT_TYPE_EMOJIS = {
        "lecture": "📖",
        "lab": "💻",
        "srw": "📝",
        "pe": "⚽",
        "seminar": "💬",
    }

    def __init__(self):
        super().__init__(bot_name="IITU Schedule Bot", version="1.0.0")
        # Защищённые атрибуты
        self._schedule_cache: Dict[int, List[Dict]] = {}
        self._notification_settings: Dict[int, bool] = {}
        self._logger.info("📅 ScheduleBot initialized with schedule functionality")

    def __str__(self) -> str:
        return (
            f"ScheduleBot | {self.bot_name} v{self.version} | "
            f"Cache: {len(self._schedule_cache)} days | "
            f"Commands: {self._command_count}"
        )

    async def handle_message(self, user_id: int, text: str) -> str:
        self._increment_commands()
        text_lower = text.lower().strip()

        keyword_responses = {
            "сегодня": "Используйте команду /today для расписания на сегодня.",
            "завтра": "Используйте команду /tomorrow для расписания на завтра.",
            "неделя": "Используйте команду /week для расписания на неделю.",
            "помощь": self.get_help_text(),
            "привет": "👋 Привет! Я бот расписания IITU. Используйте /help.",
            "здравствуй": "👋 Здравствуйте! Используйте /help для списка команд.",
        }
        for keyword, response in keyword_responses.items():
            if keyword in text_lower:
                return response

        return (
            f"🤔 Не понимаю: «{text[:50]}»\n\n"
            "Попробуйте одну из команд:\n"
            "/today — сегодня\n"
            "/week — неделя\n"
            "/help — помощь"
        )
    async def handle_command(self, user_id: int, command: str) -> str:
        self.log_command(user_id, command)
        command_map = {
            "/start": "Добро пожаловать в IITU Schedule Bot!",
            "/help": self.get_help_text(),
            "/today": "Используйте Telegram-хендлер для /today",
            "/week": "Используйте Telegram-хендлер для /week",
        }
        return command_map.get(command, self.handle_unknown_command(command))

    def get_help_text(self) -> str:
        return (
            "📚 *Помощь — IITU Schedule Bot*\n\n"
            "*Расписание:*\n"
            "/today — сегодняшние пары\n"
            "/tomorrow — завтрашние пары\n"
            "/week — расписание на неделю\n"
            "/monday … /saturday — конкретный день\n\n"
            "*Информация:*\n"
            "/teachers — список преподавателей\n"
            "/subjects — список предметов\n"
            "/profile — мой профиль\n\n"
            "*Уведомления:*\n"
            "/notifications — настройки уведомлений\n\n"
            "*Прочее:*\n"
            "/help — это сообщение\n"
        )

    def format_schedule_day(self, day_name: str, lessons: List[Dict]) -> str:
        if not lessons:
            return f"📅 *{day_name}*\n\n✅ Пар нет — свободный день!"

        lines = [f"📅 *{day_name}*\n"]
        for i, lesson in enumerate(lessons, 1):
            emoji = self.SUBJECT_TYPE_EMOJIS.get(lesson.get("subject_type", "lecture"), "📖")
            is_online = lesson.get("is_online", False)
            room_icon = "🌐" if is_online else "🏛"
            lines.append(
                f"{emoji} *{lesson['time_start']} – {lesson['time_end']}*\n"
                f"   📚 {lesson['subject']}\n"
                f"   👨‍🏫 {lesson.get('teacher', '—')}\n"
                f"   {room_icon} {lesson.get('room', '—')}\n"
            )
        return "\n".join(lines)

    def format_full_week(self, week_schedule: List[Dict]) -> str:
        days: Dict[int, List[Dict]] = {}
        for lesson in week_schedule:
            d = lesson["day_number"]
            days.setdefault(d, []).append(lesson)

        if not days:
            return "📅 Расписание не найдено."
        result = ["📅 *Расписание на неделю*\n"]
        for day_num in sorted(days.keys()):
            day_name = self.DAY_NAMES.get(day_num, f"День {day_num}")
            result.append(f"━━━ {day_name} ━━━")
            for lesson in days[day_num]:
                is_online = lesson.get("is_online", False)
                icon = "🌐" if is_online else "🏛"
                result.append(
                    f"  {lesson['time_start']} {lesson['subject']}\n"
                    f"  {icon} {lesson.get('room', '—')}"
                )
            result.append("")
        return "\n".join(result)

    def cache_schedule(self, day_number: int, schedule: List[Dict]):
        self._schedule_cache[day_number] = schedule
        self._logger.debug(f"Cached schedule for day {day_number}: {len(schedule)} lessons")

    def get_cached_schedule(self, day_number: int) -> Optional[List[Dict]]:
        return self._schedule_cache.get(day_number)

    def set_notification(self, user_id: int, enabled: bool):
        self._notification_settings[user_id] = enabled

    def is_notification_enabled(self, user_id: int) -> bool:
        return self._notification_settings.get(user_id, True)

class AdminBot(ScheduleBot):

    def __init__(self, admin_ids: List[int] = None):
        super().__init__()
        self.__admin_ids: List[int] = admin_ids or []
        self._broadcast_count: int = 0
        self._logger.info(f"👑 AdminBot initialized with {len(self.__admin_ids)} admins")

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base} | Admins: {len(self.__admin_ids)} | Broadcasts: {self._broadcast_count}"

    async def handle_message(self, user_id: int, text: str) -> str:
        if self.is_admin(user_id):
            if text.lower().startswith("broadcast "):
                return f"📢 Рассылка: {text[10:]}"
            if text.lower() == "stats":
                return str(self.stats)
        return await super().handle_message(user_id, text)

    async def handle_command(self, user_id: int, command: str) -> str:
        if command == "/admin" and not self.is_admin(user_id):
            self._increment_errors()
            return "⛔ Доступ запрещён. Эта команда только для администраторов."
        return await super().handle_command(user_id, command)

    def get_help_text(self) -> str:
        base_help = super().get_help_text()
        admin_help = (
            "\n*👑 Команды администратора:*\n"
            "/admin — панель администратора\n"
            "/stats — статистика бота\n"
            "/broadcast — рассылка всем\n"
            "/users — список пользователей\n"
        )
        return base_help + admin_help
    def is_admin(self, user_id: int) -> bool:
        return user_id in self.__admin_ids

    def add_admin(self, user_id: int):
        if user_id not in self.__admin_ids:
            self.__admin_ids.append(user_id)
            self._logger.info(f"👑 Admin added: {user_id}")

    def remove_admin(self, user_id: int):
        if user_id in self.__admin_ids:
            self.__admin_ids.remove(user_id)
            self._logger.info(f"👋 Admin removed: {user_id}")

    @property
    def admin_count(self) -> int:
        return len(self.__admin_ids)

    def get_admin_stats(self) -> Dict:
        base = self.stats
        base.update({
            "admin_count": self.admin_count,
            "broadcast_count": self._broadcast_count,
        })
        return base

    async def broadcast_message(self, message: str) -> str:
        self._broadcast_count += 1
        self._logger.info(f"📢 Broadcast #{self._broadcast_count}: {message[:50]}...")
        return f"✅ Рассылка #{self._broadcast_count} подготовлена"

class Subject:
    def __init__(self, name: str, teacher: str, room: str,
                 time_start: str, time_end: str, is_online: bool = False):
        self._name = name
        self._teacher = teacher
        self._room = room
        self._time_start = time_start
        self._time_end = time_end
        self._is_online = is_online

    def __str__(self) -> str:
        icon = "🌐" if self._is_online else "🏛"
        return (
            f"📚 {self._name}\n"
            f"   ⏰ {self._time_start} – {self._time_end}\n"
            f"   👨‍🏫 {self._teacher}\n"
            f"   {icon} {self._room}"
        )
    def __repr__(self) -> str:
        return f"Subject(name='{self._name}', time='{self._time_start}-{self._time_end}')"
    @property
    def name(self) -> str:
        return self._name
    @property
    def is_online(self) -> bool:
        return self._is_online
    @property
    def duration_minutes(self) -> int:
        try:
            start_h, start_m = map(int, self._time_start.split(":"))
            end_h, end_m = map(int, self._time_end.split(":"))
            return (end_h * 60 + end_m) - (start_h * 60 + start_m)
        except ValueError:
            return 50

    def to_dict(self) -> Dict:
        return {
            "name": self._name,
            "teacher": self._teacher,
            "room": self._room,
            "time_start": self._time_start,
            "time_end": self._time_end,
            "is_online": self._is_online,
            "duration_minutes": self.duration_minutes,
        }

def demo_oop():
    import asyncio

    print("\n" + "=" * 60)
    print("   ООП ДЕМОНСТРАЦИЯ — IITU Schedule Bot")
    print("=" * 60)
    schedule_bot = ScheduleBot()
    admin_bot = AdminBot(admin_ids=[123456789])

    print(f"\n[ScheduleBot] {schedule_bot}")
    print(f"[AdminBot]    {admin_bot}")
    bots = [schedule_bot, admin_bot]
    print("\n--- Полиморфизм: get_help_text() ---")
    for bot in bots:
        print(f"\n{bot.__class__.__name__}:\n{bot.get_help_text()[:100]}...")
    subj = Subject("Python программалау", "Сапакова С.З.", "303-4", "08:00", "08:50")
    print(f"\n--- Subject __str__ ---\n{subj}")
    print(f"Duration: {subj.duration_minutes} min")
    print(f"Dict: {subj.to_dict()}")
    print(f"\n--- Статистика ---")
    print(f"Instances created: {BaseBot.get_instance_count()}")
    print(f"Admin stats: {admin_bot.get_admin_stats()}")
    print("\n✅ OOP demo completed")

if __name__ == "__main__":
    demo_oop()