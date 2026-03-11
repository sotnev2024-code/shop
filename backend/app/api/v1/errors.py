"""Public API for client-side error reporting."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.error_log_service import log_error

router = APIRouter()


class ErrorReportRequest(BaseModel):
    message: str
    stack: Optional[str] = None
    url: Optional[str] = None
    source: str = "frontend"


@router.post("/errors/report")
async def report_client_error(
    payload: ErrorReportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Accept error reports from frontend (window.onerror, etc). No auth required."""
    try:
        client_ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent")
        await log_error(
            db,
            payload.message[:500],
            "ERROR",
            path="frontend",
            method="POST",
            source="frontend",
            traceback_str=payload.stack[:8000] if payload.stack else None,
            client_ip=client_ip,
            user_agent=ua[:255] if ua else None,
            extra={"url": payload.url[:500] if payload.url else None},
        )
    except Exception:
        pass
    return {"ok": True}
