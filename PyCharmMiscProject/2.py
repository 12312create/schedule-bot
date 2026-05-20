import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.text:
            user = event.from_user
            logger.info(
                f"📥 MSG from {user.id} (@{user.username}): '{event.text[:80]}'"
            )
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            logger.info(
                f"🔘 CALLBACK from {user.id} (@{user.username}): '{event.data}'"
            )
        result = await handler(event, data)
        return result

class AntiFloodMiddleware(BaseMiddleware):

    def __init__(self, rate_limit: float = 0.5):
        self._rate_limit = rate_limit
        self._user_timestamps: Dict[int, float] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        import time

        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id:
            now = time.monotonic()
            last = self._user_timestamps.get(user_id, 0)
            if now - last < self._rate_limit:
                logger.debug(f"🚫 Rate limit for user {user_id}")
                if isinstance(event, Message):
                    await event.answer("⏳ Подождите немного перед следующим запросом.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⏳ Подождите немного.", show_alert=False)
                return
            self._user_timestamps[user_id] = now

        return await handler(event, data)