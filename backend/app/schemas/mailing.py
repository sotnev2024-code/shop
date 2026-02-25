from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


AudienceType = Literal["all", "has_orders", "has_cart", "has_favorites", "no_orders"]


class MailingRequest(BaseModel):
    name: Optional[str] = None
    audience: AudienceType = "all"
    text: str
    image_url: Optional[str] = None
    button_text: Optional[str] = None
    button_url: Optional[str] = None


class MailingResponse(BaseModel):
    sent: int
    failed: int
    total: int
