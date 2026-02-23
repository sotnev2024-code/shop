from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class ThrottleMiddleware(BaseMiddleware):
    """Simple throttle middleware to prevent spam."""

    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self._last_call: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        return await handler(event, data)





