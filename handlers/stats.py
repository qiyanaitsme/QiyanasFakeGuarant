from __future__ import annotations

from aiogram import Router, types, F

from database.connection import get_db
from database.queries import get_stats
from keyboards.keyboards import back_to_menu
from utils.callbacks import Callback

router = Router()


@router.callback_query(F.data == Callback.STATS)
async def handle_stats_callback(callback: types.CallbackQuery) -> None:
    async with get_db() as conn:
        stats = await get_stats(conn)

    text = (
        "📊 <b>Статистика платформы</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['users_count']}</b>\n"
        f"⏳ Активных сделок: <b>{stats['pending_deals']}</b>\n"
        f"✅ Завершено сделок: <b>{stats['completed_deals']}</b>\n"
        f"💎 Общий оборот: <b>{stats['total_volume']:.2f} ₽</b>\n"
        f"📅 Сделок сегодня: <b>{stats['today_deals']}</b>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu())
    await callback.answer()