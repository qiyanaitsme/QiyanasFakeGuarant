from __future__ import annotations

from aiogram import Router, types
from aiogram.filters import Command

from config import settings
from database.connection import get_db
from database.queries import get_user, create_user
from keyboards.keyboards import main_menu

router = Router()


@router.message(Command("start"))
async def start_command(message: types.Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name or "unknown"

    async with get_db() as conn:
        user = await get_user(conn, user_id)
        if user is None:
            await create_user(conn, user_id, username)
            await message.bot.send_message(
                settings.admin_id,
                f"🆕 Новый пользователь: @{username} (ID: {user_id})",
            )

    is_admin = user_id == settings.admin_id
    await message.answer(
        "🏦 <b>GarantBot</b> — твой безопасный авто-гарант сделок.\n\n"
        "Я обеспечиваю честные переводы между пользователями. "
        "Создавай сделку, указывай получателя и сумму — а я прослежу за исполнением.",
        reply_markup=main_menu(is_admin=is_admin),
    )