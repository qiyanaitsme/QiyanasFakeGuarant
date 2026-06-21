from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.callbacks import Callback

WITHDRAW_METHODS = ("QIWI", "WEBMONEY", "BTC", "TRX", "ETH", "RUSCARD", "NORUSCARD")

STATUS_ICONS = {"pending": "⏳", "completed": "✅", "cancelled": "❌"}


# -- helpers --

def back_button(target: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text="◀️ Назад", callback_data=target)


def _keyboard_with_back(target: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(back_button(target))
    return builder


# -- main menu --

def main_menu(is_admin: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data=Callback.PROFILE),
        InlineKeyboardButton(text="📊 Статистика", callback_data=Callback.STATS),
    )
    builder.row(
        InlineKeyboardButton(text="🤝 Создать сделку", callback_data=Callback.CREATE_DEAL),
        InlineKeyboardButton(text="📋 Мои сделки", callback_data=Callback.MY_DEALS),
    )
    builder.row(
        InlineKeyboardButton(text="💸 Вывод средств", callback_data=Callback.WITHDRAW),
        InlineKeyboardButton(text="🆘 Поддержка", callback_data=Callback.SUPPORT),
    )
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="🛠 Админ-панель", callback_data=Callback.ADMIN)
        )
    return builder.as_markup()


# -- deals --

def deal_filter_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏳ Ожидают", callback_data=Callback.deals_filter("pending")),
        InlineKeyboardButton(text="✅ Завершены", callback_data=Callback.deals_filter("completed")),
        InlineKeyboardButton(text="❌ Отменены", callback_data=Callback.deals_filter("cancelled")),
    )
    builder.row(back_button(Callback.MENU))
    return builder.as_markup()


# -- withdraw --

def withdraw_methods_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for method in WITHDRAW_METHODS:
        builder.add(InlineKeyboardButton(
            text=method, callback_data=Callback.withdraw_method(method)
        ))
    builder.adjust(3)
    builder.row(back_button(Callback.MENU))
    return builder.as_markup()


# -- admin --

def admin_panel() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📈 Статистика платформы", callback_data=Callback.ADMIN_STATS),
        InlineKeyboardButton(text="👥 Пользователи", callback_data=Callback.ADMIN_USERS),
        InlineKeyboardButton(text="📋 Все сделки", callback_data=Callback.ADMIN_DEALS),
        InlineKeyboardButton(text="📝 Лог регистраций", callback_data=Callback.ADMIN_LOG),
    )
    builder.adjust(1)
    builder.row(back_button(Callback.MENU))
    return builder.as_markup()


def admin_user_list(users: list, page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    per_page = 5
    start = page * per_page
    chunk = users[start : start + per_page]

    for u in chunk:
        ban_icon = "🚫" if u["is_banned"] else "✅"
        label = f"{u['username'] or u['user_id']} | {ban_icon}"
        builder.add(InlineKeyboardButton(
            text=label, callback_data=Callback.admin_user(u["user_id"])
        ))

    builder.adjust(1)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=Callback.admin_users_page(page - 1)))
    if start + per_page < len(users):
        nav.append(InlineKeyboardButton(text="➡️", callback_data=Callback.admin_users_page(page + 1)))
    if nav:
        builder.row(*nav)
    builder.row(back_button(Callback.ADMIN))
    return builder.as_markup()


def admin_user_detail(user: dict) -> InlineKeyboardMarkup:
    uid = user["user_id"]
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="💰 Изменить баланс", callback_data=Callback.admin_set_balance(uid)),
        InlineKeyboardButton(text="⭐ Изменить рейтинг", callback_data=Callback.admin_set_rating(uid)),
        InlineKeyboardButton(text="📊 Изменить кол-во сделок", callback_data=Callback.admin_set_txns(uid)),
        InlineKeyboardButton(
            text="🔓 Разбанить" if user["is_banned"] else "🚫 Забанить",
            callback_data=Callback.admin_toggle_ban(uid),
        ),
    )
    builder.adjust(1)
    builder.row(back_button(Callback.ADMIN_USERS))
    return builder.as_markup()


def admin_deals_list(deals: list, show_actions: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in deals:
        icon = STATUS_ICONS.get(d["status"], "❓")
        label = f"{icon} #{d['id']} | {d['amount']}₽ | c:{d['creator_id']}→p:{d['partner_id']}"
        if show_actions and d["status"] == "pending":
            builder.add(
                InlineKeyboardButton(text=f"{label} ✓", callback_data=Callback.admin_confirm(d["id"])),
                InlineKeyboardButton(text="✗", callback_data=Callback.admin_cancel(d["id"])),
            )
        else:
            builder.add(InlineKeyboardButton(
                text=label, callback_data=Callback.admin_deal_info(d["id"])
            ))
    builder.adjust(1)
    builder.row(back_button(Callback.ADMIN))
    return builder.as_markup()


# -- simple "back only" keyboards (used by stats, profile, support, etc.) --

def back_to_menu() -> InlineKeyboardMarkup:
    return _keyboard_with_back(Callback.MENU).as_markup()


def back_to_admin() -> InlineKeyboardMarkup:
    return _keyboard_with_back(Callback.ADMIN).as_markup()


def back_to_my_deals() -> InlineKeyboardMarkup:
    return _keyboard_with_back(Callback.MY_DEALS).as_markup()


def back_to(target: str) -> InlineKeyboardMarkup:
    return _keyboard_with_back(target).as_markup()