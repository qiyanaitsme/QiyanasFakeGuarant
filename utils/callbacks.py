from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar


class Callback:
    """Registry of all callback data strings with factory methods and a parser."""

    # -- menu --
    MENU: ClassVar[str] = "menu"
    CLOSE: ClassVar[str] = "close"
    PROFILE: ClassVar[str] = "profile"
    STATS: ClassVar[str] = "stats"
    CREATE_DEAL: ClassVar[str] = "create_deal"
    MY_DEALS: ClassVar[str] = "my_deals"
    WITHDRAW: ClassVar[str] = "withdraw"
    SUPPORT: ClassVar[str] = "support"

    # -- admin --
    ADMIN: ClassVar[str] = "admin"
    ADMIN_STATS: ClassVar[str] = "admin_stats"
    ADMIN_USERS: ClassVar[str] = "admin_users"
    ADMIN_DEALS: ClassVar[str] = "admin_deals"
    ADMIN_LOG: ClassVar[str] = "admin_log"

    # -- deals filter --
    DEALS_FILTER_PREFIX: ClassVar[str] = "deals_filter"

    @staticmethod
    def deals_filter(status: str) -> str:
        return f"deals_filter_{status}"

    # -- withdraw --
    WITHDRAW_METHOD_PREFIX: ClassVar[str] = "withdraw_method"

    @staticmethod
    def withdraw_method(method: str) -> str:
        return f"withdraw_method_{method}"

    # -- admin users --
    ADMIN_USER_PREFIX: ClassVar[str] = "admin_user"
    ADMIN_USERS_PAGE_PREFIX: ClassVar[str] = "admin_users_page"

    @staticmethod
    def admin_user(user_id: int) -> str:
        return f"admin_user_{user_id}"

    @staticmethod
    def admin_users_page(page: int) -> str:
        return f"admin_users_page_{page}"

    # -- admin user actions --
    ADMIN_SET_BALANCE_PREFIX: ClassVar[str] = "admin_set_balance"
    ADMIN_SET_RATING_PREFIX: ClassVar[str] = "admin_set_rating"
    ADMIN_SET_TXNS_PREFIX: ClassVar[str] = "admin_set_txns"
    ADMIN_TOGGLE_BAN_PREFIX: ClassVar[str] = "admin_toggle_ban"

    @staticmethod
    def admin_set_balance(user_id: int) -> str:
        return f"admin_set_balance_{user_id}"

    @staticmethod
    def admin_set_rating(user_id: int) -> str:
        return f"admin_set_rating_{user_id}"

    @staticmethod
    def admin_set_txns(user_id: int) -> str:
        return f"admin_set_txns_{user_id}"

    @staticmethod
    def admin_toggle_ban(user_id: int) -> str:
        return f"admin_toggle_ban_{user_id}"

    # -- admin deals --
    ADMIN_CONFIRM_PREFIX: ClassVar[str] = "admin_confirm"
    ADMIN_CANCEL_PREFIX: ClassVar[str] = "admin_cancel"
    ADMIN_DEAL_INFO_PREFIX: ClassVar[str] = "admin_deal_info"

    @staticmethod
    def admin_confirm(deal_id: int) -> str:
        return f"admin_confirm_{deal_id}"

    @staticmethod
    def admin_cancel(deal_id: int) -> str:
        return f"admin_cancel_{deal_id}"

    @staticmethod
    def admin_deal_info(deal_id: int) -> str:
        return f"admin_deal_info_{deal_id}"


@dataclass(frozen=True)
class ParsedCallback:
    """Result of parsing a callback data string."""
    action: str
    value: int | str | None = None

    @classmethod
    def parse(cls, data: str) -> ParsedCallback:
        """Parse a callback data string into action and optional value.

            "admin_user_123"       -> action="admin_user", value=123
            "admin_confirm_42"     -> action="admin_confirm", value=42
            "deals_filter_pending" -> action="deals_filter", value="pending"
            "admin_stats"          -> action="admin_stats", value=None
        """
        int_prefixes = (
            "admin_user_", "admin_set_balance_", "admin_set_rating_",
            "admin_set_txns_", "admin_toggle_ban_",
            "admin_confirm_", "admin_cancel_", "admin_deal_info_",
            "admin_users_page_",
        )
        str_prefixes = ("deals_filter_", "withdraw_method_")

        for prefix in int_prefixes:
            if data.startswith(prefix) and data[len(prefix):].isdigit():
                return cls(action=prefix.rstrip("_"), value=int(data[len(prefix):]))

        for prefix in str_prefixes:
            if data.startswith(prefix):
                return cls(action=prefix.rstrip("_"), value=data[len(prefix):])

        return cls(action=data)