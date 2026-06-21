from __future__ import annotations

from aiogram import Router, types, F

from keyboards.keyboards import back_to_menu
from utils.callbacks import Callback

router = Router()


@router.callback_query(F.data == Callback.SUPPORT)
async def handle_support_callback(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        "🆘 <b>Поддержка</b>\n\n"
        "По всем вопросам обращайтесь к администратору.\n"
        "Он вам обязательно поможет. Наверное.",
        reply_markup=back_to_menu(),
    )
    await callback.answer()