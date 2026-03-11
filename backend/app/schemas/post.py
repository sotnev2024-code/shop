from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PostCreate(BaseModel):
    title: Optional[str] = None
    text: str = ""
    photo_url: Optional[str] = None
    photo_file_id: Optional[str] = None
    button_text: Optional[str] = None
    button_url: Optional[str] = None
    button_color: Optional[str] = None  # blue, green, red, gray
    product_id: Optional[int] = None


class PostUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    photo_url: Optional[str] = None
    photo_file_id: Optional[str] = None
    button_text: Optional[str] = None
    button_url: Optional[str] = None
    button_color: Optional[str] = None
    product_id: Optional[int] = None


class PostResponse(BaseModel):
    id: int
    title: Optional[str] = None
    text: str
    photo_url: Optional[str] = None
    photo_file_id: Optional[str] = None
    button_text: Optional[str] = None
    button_url: Optional[str] = None
    button_color: Optional[str] = None
    product_id: Optional[int] = None
    sent_at: Optional[datetime] = None
    message_id: Optional[int] = None
    channel_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    items: list[PostResponse]
    total: int
