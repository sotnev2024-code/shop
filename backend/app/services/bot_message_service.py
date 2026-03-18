"""Bot message templates: storage, defaults, variable substitution."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.app_config import AppConfig


DEFAULT_TEMPLATES = {
    "welcome": {
        "text": "Добро пожаловать! Нажмите кнопку ниже, чтобы открыть магазин 👇",
        "button_text": "🛍 Открыть магазин",
        "button_style": "primary",
    },
    "product_not_found": {
        "text": "Товар не найден 😔",
    },
    "product": {
        "template": "<b>{product_name}</b>\n📂 {product_categories}\n💰 <b>{product_price}</b>\n{product_old_price_line}\n{product_description}\n{product_stock_warning}",
        "button_product_text": "🔍 Посмотреть товар",
        "button_shop_text": "🛍 Открыть магазин",
        "button_product_style": "primary",
        "button_shop_style": None,
    },
    "error": {
        "text": "Произошла ошибка. Попробуйте позже.",
    },
    "order_status_changed": {
        "text": "Статус вашего заказа #{order_id} изменён на: {order_status}",
    },
    "daily_matches": {
        "text": "⚽ Матчи на {date}\n\n{matches_list}",
        "buttons": [
            [{"text": "Открыть матчи", "url": f"{settings.tme_app_url}?startapp=football", "style": "primary"}],
        ],
    },
}

# Variables per context for UI reference
VARIABLES_BY_CONTEXT = {
    "welcome": ["{user_name}", "{shop_name}"],
    "product_not_found": ["{shop_name}"],
    "product": [
        "{product_name}",
        "{product_price}",
        "{product_old_price}",
        "{product_old_price_line}",
        "{product_description}",
        "{product_categories}",
        "{product_stock_warning}",
        "{shop_name}",
    ],
    "error": ["{shop_name}"],
    "order_status_changed": [
        "{order_id}",
        "{order_status}",
        "{order_status_label}",
        "{shop_name}",
        "{user_name}",
        "{tracking_number}",
    ],
    "daily_matches": ["{date}", "{matches_list}", "{matches_count}", "{shop_name}"],
}

# Human-readable status labels
ORDER_STATUS_LABELS = {
    "new": "Новый",
    "paid": "Оплачен",
    "processing": "В обработке",
    "shipped": "Отправлен",
    "done": "Выполнен",
    "cancelled": "Отменён",
}


def substitute_variables(text: str, context: Dict[str, Any]) -> str:
    """Replace {var} placeholders in text with context values."""
    if not text:
        return ""
    result = text
    for key, value in context.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, str(value) if value is not None else "")
    # Remove any remaining unmatched {var} (replace with empty)
    result = re.sub(r"\{[a-zA-Z_]+\}", "", result)
    return result


async def get_templates(db: AsyncSession) -> Dict[str, Any]:
    """Get bot message templates from AppConfig, merged with defaults."""
    result = await db.execute(select(AppConfig).limit(1))
    config = result.scalar_one_or_none()
    raw = getattr(config, "bot_message_templates", None) if config else None
    if not raw or not str(raw).strip():
        return dict(DEFAULT_TEMPLATES)
    try:
        custom = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return dict(DEFAULT_TEMPLATES)
    merged = {}
    for key, default_val in DEFAULT_TEMPLATES.items():
        if key in custom and isinstance(custom[key], dict):
            merged[key] = {**default_val, **custom[key]}
        else:
            merged[key] = dict(default_val)
    return merged


async def get_template(db: AsyncSession, key: str) -> Dict[str, Any]:
    """Get a single template by key."""
    templates = await get_templates(db)
    return templates.get(key, DEFAULT_TEMPLATES.get(key, {}))


def get_default_templates() -> Dict[str, Any]:
    """Return default templates (for API /admin/bot-templates/defaults)."""
    return dict(DEFAULT_TEMPLATES)


def get_variables_by_context() -> Dict[str, list]:
    """Return variables available per context (for UI)."""
    return dict(VARIABLES_BY_CONTEXT)


def get_order_status_label(status: str) -> str:
    """Return human-readable label for order status."""
    return ORDER_STATUS_LABELS.get(status, status)
