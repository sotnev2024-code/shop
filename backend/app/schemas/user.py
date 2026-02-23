from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    telegram_id: int
    first_name: str = ""
    last_name: Optional[str] = None
    username: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    phone: Optional[str] = None
    address: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponse(UserBase):
    id: int
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}





