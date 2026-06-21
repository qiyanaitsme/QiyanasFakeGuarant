from __future__ import annotations

from aiogram import Router, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from database.connection import get_db
from database.queries import get_user
from keyboards.keyboards import WITHDRAW_METHODS, back_to_menu, back_to, withdraw_methods_menu
from states.states import WithdrawForm
from utils.callbacks import Callback, ParsedCallback

router = Router()


@router.callback_query(F.data == Callback.WITHDRAW, StateFilter(None))
async def start_withdraw(callback: types.CallbackQuery, state: FSMContext) -> None:
    async with get_db() as conn:
        user = await get_user(conn, callback.from_user.id)

    if user is None or user["balance"] < 1:
        await callback.answer("Недостаточно средств для вывода.", show_alert=True)
        return

    await state.set_state(WithdrawForm.choose_method)
    await callback.message.edit_text(
        "💸 <b>Вывод средств</b>\n\nВыберите способ:",
        reply_markup=withdraw_methods_menu(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith(Callback.WITHDRAW_METHOD_PREFIX), WithdrawForm.choose_method)
async def process_withdraw_method(callback: types.CallbackQuery, state: FSMContext) -> None:
    parsed = ParsedCallback.parse(callback.data)
    method = parsed.value
    await state.update_data(payment_method=method)
    await state.set_state(WithdrawForm.enter_address)
    await callback.message.edit_text(
        f"💸 Вывод на <b>{method}</b>\n\nВведите сумму и адрес кошелька через пробел:",
        reply_markup=back_to_menu(),
    )
    await callback.answer()


@router.message(WithdrawForm.enter_address)
async def process_withdraw_address(message: types.Message, state: FSMContext) -> None:
    parts = message.text.split(maxsplit=1)

    if len(parts) != 2:
        await message.answer("❌ Введите сумму и адрес через пробел.")
        return

    try:
        amount = float(parts[0])
    except ValueError:
        await message.answer("❌ Некорректная сумма.")
        return

    async with get_db() as conn:
        user = await get_user(conn, message.from_user.id)

    if user is None or user["balance"] < amount:
        await message.answer("❌ Недостаточно средств.")
        await state.clear()
        return

    data = await state.get_data()
    method = data.get("payment_method", "?")

    await message.answer(
        f"✅ <b>Заявка на вывод оформлена</b>\n\n"
        f"💰 Сумма: <b>{amount:.2f} ₽</b>\n"
        f"📱 Метод: <b>{method}</b>\n"
        f"📌 Статус: ожидайте обработки\n\n"
        f"<i>Средства не придут. Хихи.</i>",
    )
    await state.clear()