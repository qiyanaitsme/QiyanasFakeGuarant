from contextlib import asynccontextmanager

import sqlite3

import aiosqlite

from config import settings

DB_PATH = settings.db_path


async def create_tables() -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                username TEXT DEFAULT '',
                balance REAL DEFAULT 0,
                rating REAL DEFAULT 0,
                num_transactions INTEGER DEFAULT 0,
                total_amount REAL DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                registered_at TEXT DEFAULT ''
            )"""
        )
        for col, col_def in [
            ("username", "TEXT DEFAULT ''"),
            ("is_banned", "INTEGER DEFAULT 0"),
            ("registered_at", "TEXT DEFAULT ''"),
        ]:
            try:
                await conn.execute(f"ALTER TABLE users ADD COLUMN {col} {col_def}")
            except sqlite3.OperationalError:
                pass  # column already exists — not an error

        await conn.execute(
            """CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                partner_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT '',
                completed_at TEXT DEFAULT ''
            )"""
        )
        await conn.commit()


@asynccontextmanager
async def get_db():
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        yield conn