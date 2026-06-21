from aiogram import Router, types, Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from database.connection import get_db
from database.queries import get_user, transfer_funds
from keyboards.keyboards import main_menu
from states.states import TransferForm

router = Router()


@router.message(F.text == "Передать средства", StateFilter(None))
async def handle_send_money_button(message: types.Message, state: FSMContext) -> None:
    await state.set_state(TransferForm.amount_and_recipient)
    await message.answer("Введите сумму и ID пользователя (через пробел):")


@router.message(TransferForm.amount_and_recipient)
async def handle_send_money_input(message: types.Message, state: FSMContext, bot: Bot) -> None:
    data = message.text.split()

    if len(data) != 2:
        await message.answer(
            "Ошибка ввода. Пожалуйста, введите команду в формате: сумма ID_пользователя"
        )
        await state.clear()
        return

    try:
        amount = float(data[0])
    except ValueError:
        await message.answer("Ошибка: некорректная сумма")
        await state.clear()
        return

    recipient_user_id = int(data[1])

    async with get_db() as conn:
        sender = await get_user(conn, message.from_user.id)
        recipient = await get_user(conn, recipient_user_id)

        if sender is None or recipient is None:
            await message.answer("Ошибка: отправитель или получатель не найден")
            await state.clear()
            return

        if sender[2] < amount:
            await message.answer("Ошибка: недостаточно средств на балансе")
            await state.clear()
            return

        await transfer_funds(conn, message.from_user.id, recipient_user_id, amount)

    await message.answer(
        f"Вы успешно отправили {amount} пользователю {recipient_user_id}",
        reply_markup=main_menu(),
    )
    await bot.send_message(recipient_user_id, f"Вы получили {amount} на свой кошелек")
    await state.clear()