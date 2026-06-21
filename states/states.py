from aiogram.fsm.state import State, StatesGroup


class DealForm(StatesGroup):
    partner_id = State()
    amount = State()


class WithdrawForm(StatesGroup):
    choose_method = State()
    enter_address = State()


class AdminUserForm(StatesGroup):
    enter_amount = State()
    enter_rating = State()
    enter_transactions = State()