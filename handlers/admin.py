from __future__ import annotations

import logging

from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from config import settings
from database.connection import get_db
from database.queries import (
    get_user,
    get_deal,
    get_stats,
    get_all_users,
    get_deals_by_status,
    get_recent_users,
    update_balance,
    update_rating,
    set_user_banned,
    update_deal_status,
    update_transactions,
    complete_deal,
)
from keyboards.keyboards import (
    admin_panel,
    admin_user_list,
    admin_user_detail,
    admin_deals_list,
    back_to_admin,
    back_to,
)
from states.states import AdminUserForm
from utils.callbacks import Callback, ParsedCallback
from utils.formatting import format_user_detail

logger = logging.getLogger(__name__)
router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id == settings.admin_id


def _guard(callback: types.CallbackQuery) -> bool:
    if not _is_admin(callback.from_user.id):
        callback.answer("❌ Доступ запрещен", show_alert=True)
        return False
    return True


# ── admin panel ────────────────────────────────────────────────────────

@router.callback_query(F.data == Callback.ADMIN)
async def show_admin_panel(callback: types.CallbackQuery) -> None:
    if not _guard(callback):
        return
    await callback.message.edit_text(
        "🛠 <b>Админ-панель</b>\n\nВыберите раздел:",
        reply_markup=admin_panel(),
    )
    await callback.answer()


# ── admin stats ────────────────────────────────────────────────────────

@router.callback_query(F.data == Callback.ADMIN_STATS)
async def show_admin_stats(callback: types.CallbackQuery) -> None:
    if not _guard(callback):
        return

    async with get_db() as conn:
        stats = await get_stats(conn)

    text = (
        "📈 <b>Статистика платформы</b>\n\n"
        f"👥 Пользователей: <b>{stats['users_count']}</b>\n"
        f"⏳ Активных сделок: <b>{stats['pending_deals']}</b>\n"
        f"✅ Завершено: <b>{stats['completed_deals']}</b>\n"
        f"💎 Общий оборот: <b>{stats['total_volume']:.2f} ₽</b>\n"
        f"📅 Сделок сегодня: <b>{stats['today_deals']}</b>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_admin())
    await callback.answer()


# ── admin users ────────────────────────────────────────────────────────

@router.callback_query(F.data == Callback.ADMIN_USERS)
async def show_admin_users(callback: types.CallbackQuery) -> None:
    if not _guard(callback):
        return

    async with get_db() as conn:
        users = await get_all_users(conn)

    await callback.message.edit_text(
        "👥 <b>Пользователи</b>\n\nВыберите пользователя:",
        reply_markup=admin_user_list(users),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(Callback.ADMIN_USERS_PAGE_PREFIX))
async def show_admin_users_page(callback: types.CallbackQuery) -> None:
    if not _guard(callback):
        return

    parsed = ParsedCallback.parse(callback.data)
    page = int(parsed.value)
    async with get_db() as conn:
        users = await get_all_users(conn)

    await callback.message.edit_text(
        "👥 <b>Пользователи</b>\n\nВыберите пользователя:",
        reply_markup=admin_user_list(users, page),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(Callback.ADMIN_USER_PREFIX + "_"))
async def show_admin_user_detail(callback: types.CallbackQuery) -> None:
    if not _guard(callback):
        return

    parsed = ParsedCallback.parse(callback.data)
    target_id = int(parsed.value)

    async with get_db() as conn:
        user = await get_user(conn, target_id)

    if user is None:
        await callback.answer("Пользователь не найден")
        return

    await callback.message.edit_text(
        format_user_detail(dict(user)),
        reply_markup=admin_user_detail(dict(user)),
    )
    await callback.answer()


# ── set balance ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(Callback.ADMIN_SET_BALANCE_PREFIX))
async def start_set_balance(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not _guard(callback):
        return

    parsed = ParsedCallback.parse(callback.data)
    target_id = int(parsed.value)
    await state.update_data(target_id=target_id)
    await state.set_state(AdminUserForm.enter_amount)
    await callback.message.edit_text(
        f"💰 Установка баланса для <code>{target_id}</code>\n\nВведите новую сумму:",
        reply_markup=back_to(Callback.admin_user(target_id)),
    )
    await callback.answer()


@router.message(AdminUserForm.enter_amount)
async def process_set_balance(message: types.Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return

    try:
        amount = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректная сумма. Введите число.")
        await state.clear()
        return

    data = await state.get_data()
    target_id = data["target_id"]
    await state.clear()

    async with get_db() as conn:
        await update_balance(conn, target_id, amount)
        user = await get_user(conn, target_id)

    await message.delete()
    if user:
        logger.info("admin %d set balance for user %d to %.2f", message.from_user.id, target_id, amount)
        await message.answer(
            format_user_detail(dict(user)),
            reply_markup=admin_user_detail(dict(user)),
        )


# ── set rating ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(Callback.ADMIN_SET_RATING_PREFIX))
async def start_set_rating(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not _guard(callback):
        return

    parsed = ParsedCallback.parse(callback.data)
    target_id = int(parsed.value)
    await state.update_data(target_id=target_id)
    await state.set_state(AdminUserForm.enter_rating)
    await callback.message.edit_text(
        f"⭐ Установка рейтинга для <code>{target_id}</code>\n\nВведите новый рейтинг (0-5):",
        reply_markup=back_to(Callback.admin_user(target_id)),
    )
    await callback.answer()


@router.message(AdminUserForm.enter_rating)
async def process_set_rating(message: types.Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        await state.clear()
        return

    try:
        rating = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректное значение. Введите число.")
        return

    if not (0 <= rating <= 5):
        await message.answer("❌ Рейтинг должен быть от 0 до 5.")
        return

    data = await state.get_data()
    target_id = data["target_id"]
    await state.clear()

    async with get_db() as conn:
        await update_rating(conn, target_id, rating)
        user = await get_user(conn, target_id)

    await message.delete()
    if user:
        logger.info("admin %d set rating for user %d to %.1f", message.from_user.id, target_id, rating)
        await message.answer(
            format_user_detail(dict(user)),
            reply_markup=admin_user_detail(dict(user)),
        )


# ── set transactions ───────────────────────────────────────────────────

@router.callback_query(F.data.startswith(Callback.ADMIN_SET_TXNS_PREFIX))
async def start_set_transactions(callback: types.CallbackQuery, state: FSMContext) -> None:
    if not _guard(callback):
        return

    parsed = ParsedCallback.parse(callback.data)
    target_id = int(parsed.value)
    await state.update_data(target_id=target_id)
    await state.set_state(AdminUserForm.enter_transactions)
    await callback.message.edit_text(
        f"📊 Установка кол-ва сделок для <code>{target_id}</code>\n\nВведите новое количество:",
        reply_markup=back_to(Callback.admin_user(target_id)),
    )
    await callback.answer()


@router.message(AdminUserForm.enter_transactions)
async def process_set_transactions(message: types.Message, state: FSMContext) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        await state.clear()
        return

    try:
        count = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Некорректное значение. Введите целое число.")
        return

    if count < 0:
        await message.answer("❌ Количество не может быть отрицательным.")
        return

    data = await state.get_data()
    target_id = data["target_id"]
    await state.clear()

    async with get_db() as conn:
        await update_transactions(conn, target_id, count)
        user = await get_user(conn, target_id)

    await message.delete()
    if user:
        logger.info("admin %d set transactions for user %d to %d", message.from_user.id, target_id, count)
        await message.answer(
            format_user_detail(dict(user)),
            reply_markup=admin_user_detail(dict(user)),
        )


# ── toggle ban ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(Callback.ADMIN_TOGGLE_BAN_PREFIX))
async def toggle_ban(callback: types.CallbackQuery) -> None:
    if not _guard(callback):
        return

    parsed = ParsedCallback.parse(callback.data)
    target_id = int(parsed.value)

    async with get_db() as conn:
        user = await get_user(conn, target_id)
        if user is None:
            await callback.answer("Пользователь не найден")
            return
        new_ban = not bool(user["is_banned"])
        await set_user_banned(conn, target_id, new_ban)
        user = await get_user(conn, target_id)

    verb = "banned" if new_ban else "unbanned"
    logger.info("admin %d %s user %d", callback.from_user.id, verb, target_id)
    await callback.answer(f"Пользователь {target_id} {'забанен' if new_ban else 'разбанен'}")
    await callback.message.edit_text(
        format_user_detail(dict(user)),
        reply_markup=admin_user_detail(dict(user)),
    )


# ── admin deals ────────────────────────────────────────────────────────

@router.callback_query(F.data == Callback.ADMIN_DEALS)
async def show_admin_deals(callback: types.CallbackQuery) -> None:
    if not _guard(callback):
        return

    async with get_db() as conn:
        pending = await get_deals_by_status(conn, "pending")

    if not pending:
        await callback.message.edit_text(
            "📋 <b>Все сделки</b>\n\nНет активных сделок.",
            reply_markup=back_to_admin(),
        )
        return

    await callback.message.edit_text(
        f"📋 <b>Активные сделки</b> ({len(pending)})\n✓ — подтвердить, ✗ — отменить",
        reply_markup=admin_deals_list(pending, show_actions=True),
    )
    await callback.answer()


async def _refresh_deals_list(callback: types.CallbackQuery) -> None:
    async with get_db() as conn:
        pending = await get_deals_by_status(conn, "pending")

    if not pending:
        await callback.message.edit_text(
            "📋 <b>Все сделки</b>\n\nНет активных сделок.",
            reply_markup=back_to_admin(),
        )
    else:
        await callback.message.edit_text(
            f"📋 <b>Активные сделки</b> ({len(pending)})\n✓ — подтвердить, ✗ — отменить",
            reply_markup=admin_deals_list(pending, show_actions=True),
        )


@router.callback_query(F.data.startswith(Callback.ADMIN_CONFIRM_PREFIX))
async def confirm_deal(callback: types.CallbackQuery) -> None:
    if not _guard(callback):
        return

    parsed = ParsedCallback.parse(callback.data)
    deal_id = int(parsed.value)

    async with get_db() as conn:
        deal = await get_deal(conn, deal_id)
        if deal is None or deal["status"] != "pending":
            await callback.answer("Сделка не найдена или уже обработана")
            return

        await complete_deal(conn, deal_id, deal["creator_id"], deal["partner_id"], deal["amount"])

    logger.info("admin %d confirmed deal #%d", callback.from_user.id, deal_id)
    await callback.answer(f"Сделка #{deal_id} подтверждена!")

    await callback.bot.send_message(
        deal["creator_id"],
        f"✅ Сделка <b>#{deal_id}</b> завершена!\n"
        f"Сумма: <b>{deal['amount']:.2f} ₽</b> → пользователю <code>{deal['partner_id']}</code>",
    )
    await callback.bot.send_message(
        deal["partner_id"],
        f"✅ Сделка <b>#{deal_id}</b> завершена!\n"
        f"Вы получили <b>{deal['amount']:.2f} ₽</b> от пользователя <code>{deal['creator_id']}</code>",
    )

    await _refresh_deals_list(callback)


@router.callback_query(F.data.startswith(Callback.ADMIN_CANCEL_PREFIX))
async def cancel_deal(callback: types.CallbackQuery) -> None:
    if not _guard(callback):
        return

    parsed = ParsedCallback.parse(callback.data)
    deal_id = int(parsed.value)

    async with get_db() as conn:
        deal = await get_deal(conn, deal_id)
        if deal is None or deal["status"] != "pending":
            await callback.answer("Сделка не найдена или уже обработана")
            return

        await update_deal_status(conn, deal_id, "cancelled")

    logger.info("admin %d cancelled deal #%d", callback.from_user.id, deal_id)
    await callback.answer(f"Сделка #{deal_id} отменена")

    await callback.bot.send_message(
        deal["creator_id"],
        f"❌ Сделка <b>#{deal_id}</b> отменена администратором.",
    )
    await callback.bot.send_message(
        deal["partner_id"],
        f"❌ Сделка <b>#{deal_id}</b> отменена администратором.",
    )

    await _refresh_deals_list(callback)


# ── admin log ──────────────────────────────────────────────────────────

@router.callback_query(F.data == Callback.ADMIN_LOG)
async def show_admin_log(callback: types.CallbackQuery) -> None:
    if not _guard(callback):
        return

    async with get_db() as conn:
        users = await get_recent_users(conn, 20)

    if not users:
        text = "📝 <b>Лог регистраций</b>\n\nПока никого."
    else:
        lines = ["📝 <b>Лог регистраций</b>\n"]
        for u in users:
            name = u["username"] or u["user_id"]
            lines.append(f"🆕 @{name} — {u['registered_at'] or '—'}")
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=back_to_admin())
    await callback.answer()