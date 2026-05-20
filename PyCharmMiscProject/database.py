import asyncio
import asyncpg
import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._host = os.getenv("DB_HOST", "localhost")
        self._port = int(os.getenv("DB_PORT", 5432))
        self._name = os.getenv("DB_NAME", "iitu_schedule_bot")
        self._user = os.getenv("DB_USER", "postgres")
        self._password = os.getenv("DB_PASSWORD", "")
        logger.info(f"Database initialized: {self._user}@{self._host}:{self._port}/{self._name}")

    def __str__(self):
        return f"Database(host={self._host}, db={self._name}, user={self._user})"

    def __repr__(self):
        return self.__str__()

    async def connect(self):
        try:
            self._pool = await asyncpg.create_pool(
                host=self._host,
                port=self._port,
                database=self._name,
                user=self._user,
                password=self._password,
                min_size=2,
                max_size=10,
            )
            logger.info("✅ PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self):
        if self._pool:
            await self._pool.close()
            logger.info("🔌 PostgreSQL connection pool closed")

    async def execute(self, query: str, *args) -> str:
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def create_tables(self):
        logger.info("📦 Creating database tables...")

        await self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username    VARCHAR(64),
                first_name  VARCHAR(64),
                last_name   VARCHAR(64),
                email       VARCHAR(128),
                phone       VARCHAR(32),
                group_name  VARCHAR(32) DEFAULT 'SE-2310',
                language    VARCHAR(8)  DEFAULT 'ru',
                is_active   BOOLEAN     DEFAULT TRUE,
                is_admin    BOOLEAN     DEFAULT FALSE,
                created_at  TIMESTAMP   DEFAULT NOW(),
                updated_at  TIMESTAMP   DEFAULT NOW()
            );
        """)

        await self.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id          BIGSERIAL PRIMARY KEY,
                day_name    VARCHAR(16) NOT NULL,
                day_number  INTEGER     NOT NULL,
                time_start  VARCHAR(8)  NOT NULL,
                time_end    VARCHAR(8)  NOT NULL,
                subject     VARCHAR(128) NOT NULL,
                teacher     VARCHAR(128),
                room        VARCHAR(64),
                is_online   BOOLEAN     DEFAULT FALSE,
                subject_type VARCHAR(16) DEFAULT 'lecture',
                created_at  TIMESTAMP   DEFAULT NOW()
            );
        """)

        await self.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id          BIGSERIAL PRIMARY KEY,
                user_id     BIGINT      REFERENCES users(telegram_id) ON DELETE CASCADE,
                message     TEXT        NOT NULL,
                remind_at   TIMESTAMP   NOT NULL,
                is_sent     BOOLEAN     DEFAULT FALSE,
                is_active   BOOLEAN     DEFAULT TRUE,
                created_at  TIMESTAMP   DEFAULT NOW()
            );
        """)

        await self.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id          BIGSERIAL PRIMARY KEY,
                user_id     BIGINT      REFERENCES users(telegram_id) ON DELETE CASCADE,
                direction   VARCHAR(8)  NOT NULL CHECK (direction IN ('in', 'out')),
                content     TEXT        NOT NULL,
                command     VARCHAR(64),
                created_at  TIMESTAMP   DEFAULT NOW()
            );
        """)

        await self.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id          BIGSERIAL PRIMARY KEY,
                user_id     BIGINT      REFERENCES users(telegram_id) ON DELETE CASCADE,
                title       VARCHAR(128) NOT NULL,
                body        TEXT        NOT NULL,
                is_read     BOOLEAN     DEFAULT FALSE,
                notif_type  VARCHAR(32) DEFAULT 'info',
                created_at  TIMESTAMP   DEFAULT NOW()
            );
        """)

        await self.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id          BIGSERIAL PRIMARY KEY,
                user_id     BIGINT,
                action      VARCHAR(64) NOT NULL,
                details     TEXT,
                ip_address  VARCHAR(64),
                created_at  TIMESTAMP   DEFAULT NOW()
            );
        """)

        await self._seed_schedule()

        logger.info("✅ All tables created successfully")

    async def _seed_schedule(self):
        # Проверяем, есть ли уже записи
        count = await self.fetchval("SELECT COUNT(*) FROM schedules")
        if count and count > 0:
            logger.info(f"Schedule already seeded ({count} records), skipping.")
            return

        schedule_data = [
            # ПОНЕДЕЛЬНИК (1)
            (1, "Понедельник", "08:00", "08:50", "Python тілінде программалау", "Сапакова С.З.", "Байзак центр, 303-4",
             False, "lecture"),
            (1, "Понедельник", "10:00", "10:50", "SQL-ге кіріспе", "Козина Л.А.", "Негізгі, 700", False, "lecture"),
            (1, "Понедельник", "12:10", "13:00", "Физика", "Ерназаров Т.И.", "Байзак центр, 300-1", False, "lecture"),
            (1, "Понедельник", "20:30", "21:20", "SQL СОӨЖ", "—", "Онлайн", True, "srw"),
            # ВТОРНИК (2)
            (2, "Вторник", "08:00", "09:50", "SQL-ге кіріспе", "Токанова Б.М.", "Негізгі, 706", False, "lab"),
            (2, "Вторник", "10:00", "11:50", "Математикалық анализ", "Самбетова А.", "Байзак центр, 419 б", False,
             "lecture"),
            (2, "Вторник", "15:10", "18:10", "Дене шынықтыру", "Бабекенов Р.Ф.", "Спортзал", False, "pe"),
            # СРЕДА (3)
            (3, "Среда", "08:00", "10:50", "Шет тілі", "Жүнісбаева Ә.С.", "Байзак центр, 206 б", False, "lecture"),
            (3, "Среда", "11:00", "13:00", "Python тілінде программалау", "Чинибаева Т.Т.", "Негізгі, 707/705", False,
             "lab"),
            (3, "Среда", "20:30", "21:20", "Дене шынықтыру СОӨЖ", "—", "Онлайн", True, "srw"),
            # ЧЕТВЕРГ (4)
            (4, "Четверг", "10:00", "11:50", "Математикалық анализ", "Самбетова А.", "Байзак центр, 303-4", False,
             "lecture"),
            (4, "Четверг", "12:10", "14:00", "Физика", "Ерназаров Т.И.", "Негізгі, 210", False, "lecture"),
            (4, "Четверг", "20:30", "21:20", "Математикалық анализ СОӨЖ", "—", "Онлайн", True, "srw"),
            (4, "Четверг", "21:30", "22:20", "Физика СОӨЖ", "—", "Онлайн", True, "srw"),
            # ПЯТНИЦА (5)
            (5, "Пятница", "21:30", "22:20", "Шет тілі СОӨЖ", "—", "Онлайн", True, "srw"),
            # СУББОТА (6)
            (6, "Суббота", "20:30", "21:20", "Python СОӨЖ", "—", "Онлайн", True, "srw"),
        ]
        for row in schedule_data:
            day_num, day_name, t_start, t_end, subject, teacher, room, is_online, stype = row
            await self.execute(
                """INSERT INTO schedules
                   (day_number, day_name, time_start, time_end, subject, teacher, room, is_online, subject_type)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                day_num, day_name, t_start, t_end, subject, teacher, room, is_online, stype
            )

        logger.info(f"✅ Schedule seeded: {len(schedule_data)} records inserted")

    async def get_or_create_user(self, telegram_id: int, username: str = None,
                                 first_name: str = None, last_name: str = None) -> Dict:
        try:
            user = await self.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", telegram_id
            )
            if user:
                # Обновить данные при изменении
                await self.execute(
                    """UPDATE users SET username=$2, first_name=$3, last_name=$4, updated_at=NOW()
                       WHERE telegram_id=$1""",
                    telegram_id, username, first_name, last_name
                )
                return dict(user)
            else:
                await self.execute(
                    """INSERT INTO users (telegram_id, username, first_name, last_name)
                       VALUES ($1, $2, $3, $4)""",
                    telegram_id, username, first_name, last_name
                )
                user = await self.fetchrow(
                    "SELECT * FROM users WHERE telegram_id = $1", telegram_id
                )
                logger.info(f"👤 New user created: {telegram_id} (@{username})")
                return dict(user)
        except Exception as e:
            logger.error(f"get_or_create_user error: {e}")
            return {}

    async def get_user(self, telegram_id: int) -> Optional[Dict]:
        row = await self.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
        return dict(row) if row else None

    async def update_user_email(self, telegram_id: int, email: str):
        await self.execute(
            "UPDATE users SET email=$2, updated_at=NOW() WHERE telegram_id=$1",
            telegram_id, email
        )

    async def update_user_phone(self, telegram_id: int, phone: str):
        await self.execute(
            "UPDATE users SET phone=$2, updated_at=NOW() WHERE telegram_id=$1",
            telegram_id, phone
        )

    async def get_schedule_by_day(self, day_number: int) -> List[Dict]:
        rows = await self.fetch(
            """SELECT * FROM schedules
               WHERE day_number = $1
               ORDER BY time_start""",
            day_number
        )
        return [dict(r) for r in rows]

    async def get_full_week_schedule(self) -> List[Dict]:
        rows = await self.fetch(
            "SELECT * FROM schedules ORDER BY day_number, time_start"
        )
        return [dict(r) for r in rows]

    async def get_all_teachers(self) -> List[str]:
        rows = await self.fetch(
            "SELECT DISTINCT teacher FROM schedules WHERE teacher != '—' ORDER BY teacher"
        )
        return [r["teacher"] for r in rows]

    async def get_all_subjects(self) -> List[str]:
        rows = await self.fetch(
            "SELECT DISTINCT subject FROM schedules ORDER BY subject"
        )
        return [r["subject"] for r in rows]

    async def save_message(self, user_id: int, direction: str,
                           content: str, command: str = None):
        try:
            await self.execute(
                """INSERT INTO messages (user_id, direction, content, command)
                   VALUES ($1, $2, $3, $4)""",
                user_id, direction, content[:2000], command
            )
        except Exception as e:
            logger.error(f"save_message error: {e}")

    async def get_message_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        rows = await self.fetch(
            """SELECT * FROM messages WHERE user_id = $1
               ORDER BY created_at DESC LIMIT $2""",
            user_id, limit
        )
        return [dict(r) for r in rows]

    async def add_reminder(self, user_id: int, message: str, remind_at: datetime):
        await self.execute(
            """INSERT INTO reminders (user_id, message, remind_at)
               VALUES ($1, $2, $3)""",
            user_id, message, remind_at
        )

    async def get_pending_reminders(self) -> List[Dict]:
        rows = await self.fetch(
            """SELECT r.*, u.telegram_id FROM reminders r
               JOIN users u ON r.user_id = u.telegram_id
               WHERE r.is_sent = FALSE AND r.is_active = TRUE
               AND r.remind_at <= NOW()"""
        )
        return [dict(r) for r in rows]

    async def mark_reminder_sent(self, reminder_id: int):
        await self.execute(
            "UPDATE reminders SET is_sent = TRUE WHERE id = $1", reminder_id
        )

    async def get_user_reminders(self, user_id: int) -> List[Dict]:
        rows = await self.fetch(
            """SELECT * FROM reminders WHERE user_id = $1 AND is_active = TRUE
               ORDER BY remind_at""",
            user_id
        )
        return [dict(r) for r in rows]

    async def add_notification(self, user_id: int, title: str,
                               body: str, notif_type: str = "info"):
        await self.execute(
            """INSERT INTO notifications (user_id, title, body, notif_type)
               VALUES ($1, $2, $3, $4)""",
            user_id, title, body, notif_type
        )

    async def get_unread_notifications(self, user_id: int) -> List[Dict]:
        rows = await self.fetch(
            """SELECT * FROM notifications WHERE user_id = $1 AND is_read = FALSE
               ORDER BY created_at DESC""",
            user_id
        )
        return [dict(r) for r in rows]

    async def mark_notifications_read(self, user_id: int):
        await self.execute(
            "UPDATE notifications SET is_read = TRUE WHERE user_id = $1", user_id
        )

    async def log_activity(self, user_id: int, action: str, details: str = None):
        try:
            await self.execute(
                """INSERT INTO activity_logs (user_id, action, details)
                   VALUES ($1, $2, $3)""",
                user_id, action, details
            )
        except Exception as e:
            logger.error(f"log_activity error: {e}")

    async def get_stats(self) -> Dict:
        total_users = await self.fetchval("SELECT COUNT(*) FROM users")
        total_messages = await self.fetchval("SELECT COUNT(*) FROM messages")
        total_reminders = await self.fetchval("SELECT COUNT(*) FROM reminders")
        return {
            "total_users": total_users or 0,
            "total_messages": total_messages or 0,
            "total_reminders": total_reminders or 0,
        }

_db_instance: Optional[Database] = None

def get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance