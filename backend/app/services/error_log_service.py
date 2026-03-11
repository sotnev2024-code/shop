"""Centralized error logging to database."""

from __future__ import annotations

import traceback
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.error_log import ErrorLog


async def log_error(
    db: AsyncSession,
    message: str,
    level: str = "ERROR",
    *,
    path: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    source: Optional[str] = None,
    traceback_str: Optional[str] = None,
    request_body: Optional[str] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an error to the database."""
    if extra is None:
        extra = {}
    if source:
        extra["source"] = source
    if path is None and source:
        path = source

    log = ErrorLog(
        level=(level or "ERROR")[:20],
        message=(message or "Unknown error")[:500],
        path=path[:255] if path else None,
        method=method[:10] if method else None,
        status_code=status_code,
        client_ip=(client_ip or None)[:50] if client_ip else None,
        user_agent=(user_agent or None)[:255] if user_agent else None,
        request_body=(request_body or None)[:4000] if request_body else None,
        traceback=(traceback_str or None)[:8000] if traceback_str else None,
        extra=extra if extra else None,
    )
    db.add(log)
    await db.commit()


def format_exception_traceback(exc: BaseException) -> str:
    """Format exception to traceback string."""
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
