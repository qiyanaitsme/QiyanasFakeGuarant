from __future__ import annotations

from typing import Any


def format_user_detail(user: dict[str, Any]) -> str:
    ban_status = "🚫 Забанен" if user["is_banned"] else "✅ Активен"
    return (
        f"👤 <b>Пользователь {user['user_id']}</b>\n\n"
        f"Имя: @{user['username'] or '—'}\n"
        f"Баланс: <b>{user['balance']:.2f} ₽</b>\n"
        f"Рейтинг: <b>{user['rating']:.1f}</b>\n"
        f"Сделок: <b>{user['num_transactions']}</b>\n"
        f"Оборот: <b>{user['total_amount']:.2f} ₽</b>\n"
        f"Статус: {ban_status}\n"
        f"Регистрация: {user['registered_at'] or '—'}"
    )


def format_user_profile(user: dict[str, Any]) -> str:
    return (
        f"👤 <b>Профиль</b>\n\n"
        f"🆔 ID: <code>{user['user_id']}</code>\n"
        f"💰 Баланс: <b>{user['balance']:.2f} ₽</b>\n"
        f"⭐ Рейтинг: <b>{user['rating']:.1f}</b>\n"
        f"📊 Сделок: <b>{user['num_transactions']}</b>\n"
        f"💎 Оборот: <b>{user['total_amount']:.2f} ₽</b>\n"
        f"📅 Регистрация: {user['registered_at'] or '—'}"
    )