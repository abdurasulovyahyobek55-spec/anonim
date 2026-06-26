from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message

from database.models import UserDB
from utils.helpers import generate_unique_code


class UserLoggingMiddleware(BaseMiddleware):
    """Har bir xabarda foydalanuvchi ma'lumotlarini avtomatik saqlash."""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user = event.from_user
        
        # Foydalanuvchi mavjudligini tekshirish
        existing = await UserDB.get_user(user.id)
        
        if not existing:
            # Yangi foydalanuvchi — unikal kod bilan saqlash
            code = generate_unique_code()
            await UserDB.save_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                unique_code=code
            )
        else:
            # Mavjud foydalanuvchi — ma'lumotlarni yangilash
            await UserDB.save_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )

        return await handler(event, data)
