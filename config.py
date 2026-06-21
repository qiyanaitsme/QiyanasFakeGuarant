from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    db_path: Path = field(default_factory=lambda: Path(__file__).parent / "database.db")

    @classmethod
    def from_env(cls) -> Settings:
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise RuntimeError("BOT_TOKEN is not set in .env or environment")

        admin_raw = os.getenv("ADMIN_ID")
        if not admin_raw:
            raise RuntimeError("ADMIN_ID is not set in .env or environment")

        try:
            admin_id = int(admin_raw)
        except ValueError:
            raise RuntimeError(f"ADMIN_ID must be an integer, got: {admin_raw}")

        return cls(bot_token=token, admin_id=admin_id)


settings = Settings.from_env()