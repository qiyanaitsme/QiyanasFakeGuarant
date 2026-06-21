from __future__ import annotations

from aiogram import Router, types, F

from config import settings
from database.connection import get_db
from database.queries import get_user
from keyboards.keyboards import back_to_menu
from utils.callbacks import Callback
from utils.formatting import format_user_profile

router = Router()


@router.callback_query(F.data == Callback.PROFILE)
async def handle_profile_callback(callback: types.CallbackQuery) -> None:
    user_id = callback.from_user.id

    async with get_db() as conn:
        user = await get_user(conn, user_id)

    if user is None:
        await callback.answer("Профиль не найден. Напиши /start")
        return

    await callback.message.edit_text(
        format_user_profile(dict(user)),
        reply_markup=back_to_menu(),
    )
    await callback.answer()