from __future__ import annotations

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from config import settings
from database.connection import get_db
from database.queries import (
    get_user,
    create_deal,
    get_deals_by_user,
)
from keyboards.keyboards import back_to_menu, back_to, deal_filter_menu
from states.states import DealForm
from utils.callbacks import Callback, ParsedCallback

router = Router()

STATUS_LABELS = {
    "pending": "⏳ Ожидает",
    "completed": "✅ Завершена",
    "cancelled": "❌ Отменена",
}


# ── create deal ────────────────────────────────────────────────────────

@router.callback_query(F.data == Callback.CREATE_DEAL)
async def start_create_deal(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DealForm.partner_id)
    await callback.message.edit_text(
        "🤝 <b>Новая сделка</b>\n\nВведите ID пользователя-партнера:",
        reply_markup=back_to_menu(),
    )
    await callback.answer()


@router.message(DealForm.partner_id)
async def process_partner_id(message: types.Message, state: FSMContext) -> None:
    try:
        partner_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректный ID. Введите числовой ID пользователя.")
        return

    if partner_id == message.from_user.id:
        await message.answer("❌ Нельзя создать сделку с самим собой. Введите другой ID.")
        return

    async with get_db() as conn:
        partner = await get_user(conn, partner_id)

    if partner is None:
        await message.answer("❌ Пользователь с таким ID не найден. Попробуйте снова.")
        return

    await state.update_data(partner_id=partner_id)
    await state.set_state(DealForm.amount)
    await message.answer(
        f"👤 Партнер: <code>{partner_id}</code>\n\nВведите сумму сделки в рублях:",
        reply_markup=back_to_menu(),
    )


@router.message(DealForm.amount)
async def process_amount(message: types.Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректная сумма. Введите число.")
        return

    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше нуля.")
        return

    data = await state.get_data()
    partner_id = data["partner_id"]
    creator_id = message.from_user.id

    async with get_db() as conn:
        creator = await get_user(conn, creator_id)
        if creator is None or creator["balance"] < amount:
            balance = creator["balance"] if creator else 0
            await message.answer(
                f"❌ Недостаточно средств на балансе.\nВаш баланс: <b>{balance:.2f} ₽</b>",
            )
            await state.clear()
            return

        deal_id = await create_deal(conn, creator_id, partner_id, amount)

    await state.clear()
    await message.answer(
        f"✅ <b>Сделка #{deal_id} создана!</b>\n\n"
        f"💰 Сумма: <b>{amount:.2f} ₽</b>\n"
        f"👤 Партнер: <code>{partner_id}</code>\n"
        f"📌 Статус: ⏳ ожидает подтверждения администратора",
        reply_markup=back_to_menu(),
    )

    await message.bot.send_message(
        settings.admin_id,
        f"🔔 <b>Новая сделка #{deal_id}</b>\n"
        f"Создатель: <code>{creator_id}</code>\n"
        f"Партнер: <code>{partner_id}</code>\n"
        f"Сумма: <b>{amount:.2f} ₽</b>",
    )


# ── my deals ───────────────────────────────────────────────────────────

@router.callback_query(F.data == Callback.MY_DEALS)
async def show_deals_filter(callback: types.CallbackQuery) -> None:
    await callback.message.edit_text(
        "📋 <b>Мои сделки</b>\n\nВыберите фильтр:",
        reply_markup=deal_filter_menu(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(Callback.DEALS_FILTER_PREFIX))
async def show_filtered_deals(callback: types.CallbackQuery) -> None:
    parsed = ParsedCallback.parse(callback.data)
    status = parsed.value
    user_id = callback.from_user.id

    async with get_db() as conn:
        all_user_deals = await get_deals_by_user(conn, user_id)

    filtered = [d for d in all_user_deals if d["status"] == status]
    label = STATUS_LABELS.get(status, status)

    if not filtered:
        text = f"📋 Сделки: {label}\n\nУ вас нет сделок в этом статусе."
    else:
        lines = [f"📋 Сделки: {label}\n"]
        for d in filtered[:10]:
            direction = "→" if d["creator_id"] == user_id else "←"
            lines.append(f"#{d['id']} {direction} {d['amount']:.0f}₽ | {d['created_at']}")
        text = "\n".join(lines)

    await callback.message.edit_text(
        text, reply_markup=back_to(Callback.MY_DEALS)
    )
    await callback.answer()