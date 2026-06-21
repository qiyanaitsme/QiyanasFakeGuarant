from __future__ import annotations

from aiogram import Router, types, F

from config import settings
from keyboards.keyboards import main_menu
from utils.callbacks import Callback

router = Router()


@router.callback_query(F.data == Callback.MENU)
async def handle_menu_callback(callback: types.CallbackQuery) -> None:
    is_admin = callback.from_user.id == settings.admin_id
    await callback.message.edit_text(
        "🏦 <b>GarantBot</b> — главное меню",
        reply_markup=main_menu(is_admin=is_admin),
    )
    await callback.answer()


@router.callback_query(F.data == Callback.CLOSE)
async def handle_close_callback(callback: types.CallbackQuery) -> None:
    await callback.message.delete()
    await callback.answer()