from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
from pathlib import Path
from urllib.parse import unquote, parse_qsl
from typing import List, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.app_config import AppConfig
from app.db.models.bonus_transaction import BonusTransaction
from app.bot.bot import is_bot_configured

logger = logging.getLogger(__name__)


def _validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """Validate Telegram Mini App initData using HMAC-SHA256."""
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{k}={unquote(v)}" for k, v in sorted(parsed.items())
        )

        secret_key = hmac.new(
            b"WebAppData", bot_token.encode(), hashlib.sha256
        ).digest()
        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        return parsed
    except Exception:
        return None


async def get_current_user(
    x_init_data: Optional[str] = Header(None, alias="X-Init-Data"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate user from Telegram Mini App initData.
    In dev mode (no bot token), returns a test user.
    """
    # --- DEV MODE: bypass auth for local testing ---
    if settings.dev_mode:
        logger.debug(f"DEV MODE: bypassing auth, using test user (telegram_id=1724263429)")
        result = await db.execute(select(User).where(User.telegram_id == 1724263429))
        user = result.scalar_one_or_none()
        if user is None:
            try:
                user = User(
                    telegram_id=1724263429,
                    first_name="Dev",
                    last_name="User",
                    username="devuser",
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                await _apply_welcome_bonus(db, user)
            except Exception:
                # Race condition: another request already created the user
                await db.rollback()
                result = await db.execute(
                    select(User).where(User.telegram_id == 1724263429)
                )
                user = result.scalar_one_or_none()
                if user is None:
                    raise HTTPException(
                        status_code=500, detail="Failed to create dev user"
                    )
        return user

    # --- PRODUCTION MODE: validate initData ---
    if not x_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Init-Data header",
        )

    validated = _validate_init_data(x_init_data, settings.bot_token)
    if validated is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid initData",
        )

    user_data = json.loads(unquote(validated.get("user", "{}")))
    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No user in initData",
        )

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name"),
            username=user_data.get("username"),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        await _apply_welcome_bonus(db, user)

    return user


async def _apply_welcome_bonus(db: AsyncSession, user: User) -> None:
    """If bonus system is enabled and welcome bonus is on, credit the user."""
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()
    if not config or not getattr(config, "bonus_enabled", False) or not getattr(config, "bonus_welcome_enabled", False):
        return
    amount = float(getattr(config, "bonus_welcome_amount", 0))
    if amount <= 0:
        return
    user.bonus_balance = float(user.bonus_balance or 0) + amount
    tx = BonusTransaction(user_id=user.id, amount=amount, kind="welcome", order_id=None)
    db.add(tx)
    await db.commit()
    await db.refresh(user)


def _parse_admin_ids(s: str) -> List[int]:
    out = []
    for x in (s or "").replace("\n", ",").split(","):
        raw = x.strip().strip('"\'')
        if not raw:
            continue
        try:
            out.append(int(raw))
        except (ValueError, TypeError):
            continue
    return out


def _read_admin_ids_from_env_file() -> List[int]:
    """Читаем ADMIN_IDS напрямую из backend/.env."""
    _env_file = Path(__file__).resolve().parents[2] / ".env"
    ids = []
    if not _env_file.exists():
        return ids
    try:
        raw = _env_file.read_text(encoding="utf-8", errors="ignore")
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip().upper() != "ADMIN_IDS":
                continue
            val = value.strip().strip("'\"").replace("\n", ",")
            for x in re.split(r"[,;\s]+", val):
                x = x.strip()
                if x:
                    try:
                        ids.append(int(x))
                    except ValueError:
                        pass
            break
    except Exception:
        pass
    return ids


async def get_admin_user(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Check that user is an admin. Admin list: .env ADMIN_IDS + os.environ + AppConfig.admin_ids."""
    if settings.dev_mode:
        return user
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()
    admin_ids_raw = getattr(config, "admin_ids", None) if config else None
    from_db = _parse_admin_ids(str(admin_ids_raw or ""))
    from_env = list(settings.admin_id_list)
    env_raw = os.environ.get("ADMIN_IDS") or os.environ.get("admin_ids") or ""
    from_env = list(dict.fromkeys(from_env + _parse_admin_ids(env_raw)))
    from_env = list(dict.fromkeys(from_env + _read_admin_ids_from_env_file()))
    admin_list = list(dict.fromkeys(from_env + from_db))
    try:
        uid = int(user.telegram_id)
    except (TypeError, ValueError):
        uid = None
    if uid is None or (uid not in admin_list and str(uid) not in [str(x) for x in admin_list]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def get_owner_user(
    user: User = Depends(get_current_user),
) -> User:
    """Check that user is the platform owner (super-admin)."""
    if settings.dev_mode:
        return user
    if settings.owner_id == 0 or user.telegram_id != settings.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )
    return user
