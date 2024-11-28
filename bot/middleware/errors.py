from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message


class ErrorsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        print(handler)
        print(event)
        # try:
        return await handler(event, data)
        # except Exception as e:
        #     await event.answer(f"Произошла ошибка {e}")
