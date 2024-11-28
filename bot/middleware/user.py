from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware, types
from aiogram.types import CallbackQuery, Message
from database import Chat, History, User
from database.connection import PostgresConnection
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession


class UserMiddleware(BaseMiddleware):
    async def setup_chat(self, user: types.User, chat: Optional[types.Chat] = None):
        user_id = str(user.id)
        full_name = user.full_name
        chat_id = str(chat.id if chat else user.id)
        chat_type = chat.type if chat else "private"
        ans = await self.session.select(select(User).where(User.telegram_id == user_id))
        if not (user := ans.scalars().first()):
            async with AsyncSession(self.session.engine) as session:
                user = User(telegram_id=user_id, full_name=full_name)
                session.add(user)
                await session.commit()
                await session.refresh(user)
        ans = await self.session.select(select(Chat).where(Chat.id == chat_id))
        if not (chat := ans.scalars().first()):
            async with AsyncSession(self.session.engine) as session:
                chat = Chat(id=chat_id, type=chat_type)
                session.add(chat)
                await session.commit()
                await session.refresh(chat)

        return user, chat

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        self.session: PostgresConnection = data["session"]
        chat = event.chat if (event and hasattr(event, "chat")) else None
        user, chat = await self.setup_chat(event.from_user, chat)
        data["user"] = User(**user.to_dict())
        if user.is_banned:
            bot = data.get("bot")
            return await bot.send_message(chat.id, "Вы забанены")
        data["chat"] = Chat(**chat.to_dict())
        insert_history = insert(History).values(
            chat_id=chat.id,
            user_id=user.telegram_id,
            command=event.text if hasattr(event, "text") else event.data,
        )
        await self.session.execute(insert_history)
        return await handler(event, data)
