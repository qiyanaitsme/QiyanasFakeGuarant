from datetime import datetime

import aiosqlite


# ── users ──────────────────────────────────────────────────────────────

async def get_user(conn: aiosqlite.Connection, user_id: int):
    cursor = await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return await cursor.fetchone()


async def create_user(conn: aiosqlite.Connection, user_id: int, username: str) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username, registered_at) VALUES (?, ?, ?)",
        (user_id, username, now),
    )
    await conn.commit()


async def update_balance(conn: aiosqlite.Connection, user_id: int, amount: float) -> None:
    await conn.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
    await conn.commit()


async def update_rating(conn: aiosqlite.Connection, user_id: int, rating: float) -> None:
    await conn.execute("UPDATE users SET rating = ? WHERE user_id = ?", (rating, user_id))
    await conn.commit()


async def update_transactions(conn: aiosqlite.Connection, user_id: int, count: int) -> None:
    await conn.execute("UPDATE users SET num_transactions = ? WHERE user_id = ?", (count, user_id))
    await conn.commit()


async def set_user_banned(conn: aiosqlite.Connection, user_id: int, banned: bool) -> None:
    await conn.execute(
        "UPDATE users SET is_banned = ? WHERE user_id = ?",
        (1 if banned else 0, user_id),
    )
    await conn.commit()


async def get_all_users(conn: aiosqlite.Connection):
    cursor = await conn.execute("SELECT * FROM users ORDER BY id DESC")
    return await cursor.fetchall()


async def get_recent_users(conn: aiosqlite.Connection, limit: int = 20):
    cursor = await conn.execute(
        "SELECT * FROM users ORDER BY id DESC LIMIT ?", (limit,)
    )
    return await cursor.fetchall()


async def get_users_count(conn: aiosqlite.Connection) -> int:
    cursor = await conn.execute("SELECT COUNT(*) FROM users")
    row = await cursor.fetchone()
    return row[0]


# ── deals ──────────────────────────────────────────────────────────────

async def create_deal(
    conn: aiosqlite.Connection, creator_id: int, partner_id: int, amount: float
) -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = await conn.execute(
        "INSERT INTO deals (creator_id, partner_id, amount, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
        (creator_id, partner_id, amount, now),
    )
    await conn.commit()
    return cursor.lastrowid


async def get_deal(conn: aiosqlite.Connection, deal_id: int):
    cursor = await conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,))
    return await cursor.fetchone()


async def get_deals_by_user(conn: aiosqlite.Connection, user_id: int):
    cursor = await conn.execute(
        "SELECT * FROM deals WHERE creator_id = ? OR partner_id = ? ORDER BY id DESC",
        (user_id, user_id),
    )
    return await cursor.fetchall()


async def get_deals_by_status(conn: aiosqlite.Connection, status: str):
    cursor = await conn.execute(
        "SELECT * FROM deals WHERE status = ? ORDER BY id DESC", (status,)
    )
    return await cursor.fetchall()


async def get_all_deals(conn: aiosqlite.Connection):
    cursor = await conn.execute("SELECT * FROM deals ORDER BY id DESC")
    return await cursor.fetchall()


async def update_deal_status(
    conn: aiosqlite.Connection, deal_id: int, status: str
) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await conn.execute(
        "UPDATE deals SET status = ?, completed_at = ? WHERE id = ?",
        (status, now, deal_id),
    )
    await conn.commit()


async def complete_deal(
    conn: aiosqlite.Connection,
    deal_id: int,
    creator_id: int,
    partner_id: int,
    amount: float,
) -> None:
    """Atomically complete deal and update both users' balances and stats."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await conn.execute(
        "UPDATE deals SET status = 'completed', completed_at = ? WHERE id = ?",
        (now, deal_id),
    )
    await conn.execute(
        "UPDATE users SET balance = balance - ?, num_transactions = num_transactions + 1, total_amount = total_amount + ? WHERE user_id = ?",
        (amount, amount, creator_id),
    )
    await conn.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        (amount, partner_id),
    )
    await conn.commit()


# ── stats ──────────────────────────────────────────────────────────────

async def get_stats(conn: aiosqlite.Connection) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")

    cursor = await conn.execute("SELECT COUNT(*) FROM users")
    users_count = (await cursor.fetchone())[0]

    cursor = await conn.execute("SELECT COUNT(*) FROM deals WHERE status = 'pending'")
    pending_deals = (await cursor.fetchone())[0]

    cursor = await conn.execute("SELECT COUNT(*) FROM deals WHERE status = 'completed'")
    completed_deals = (await cursor.fetchone())[0]

    cursor = await conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM deals WHERE status = 'completed'"
    )
    total_volume = (await cursor.fetchone())[0]

    cursor = await conn.execute(
        "SELECT COUNT(*) FROM deals WHERE status = 'completed' AND date(completed_at) = ?",
        (today,),
    )
    today_deals = (await cursor.fetchone())[0]

    return {
        "users_count": users_count,
        "pending_deals": pending_deals,
        "completed_deals": completed_deals,
        "total_volume": total_volume,
        "today_deals": today_deals,
    }