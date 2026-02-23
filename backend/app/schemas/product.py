from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    sort_order: int
    is_active: bool
    parent_id: Optional[int] = None
    image_url: Optional[str] = None
    children: list["CategoryResponse"] = []

    model_config = {"from_attributes": True}


CategoryResponse.model_rebuild()


class CategoryCreate(BaseModel):
    name: str
    slug: str
    sort_order: int = 0
    is_active: bool = True
    parent_id: Optional[int] = None
    image_url: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    parent_id: Optional[int] = None
    image_url: Optional[str] = None


class ProductMediaResponse(BaseModel):
    id: int
    media_type: str  # "image" | "video"
    url: str = Field(validation_alias="file_path")
    sort_order: int

    model_config = {"from_attributes": True, "populate_by_name": True}


class ModificationTypeShort(BaseModel):
    id: int
    name: str


class ProductVariantShort(BaseModel):
    value: str
    quantity: int


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    old_price: Optional[float] = None
    image_url: Optional[str] = None
    is_available: bool = True
    stock_quantity: int = 0
    category_id: Optional[int] = None
    external_id: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    old_price: Optional[float] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    stock_quantity: Optional[int] = None
    category_id: Optional[int] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    category: Optional[CategoryResponse] = None
    is_favorite: bool = False
    media: list[ProductMediaResponse] = []
    modification_type: Optional[ModificationTypeShort] = None
    variants: list[ProductVariantShort] = []

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    per_page: int


# ---- Bulk price update (admin) ----

class BulkPriceRequest(BaseModel):
    scope: str  # "all" | "product_ids" | "price_equals" | "price_range" | "category"
    product_ids: Optional[list[int]] = None
    price_equals: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    category_id: Optional[int] = None
    operation: str  # "add_amount" | "subtract_amount" | "add_percent" | "subtract_percent" | "set_to"
    value: float
    round_to_nearest: Optional[float] = None


class BulkPriceResponse(BaseModel):
    updated_count: int
    product_ids: list[int]


# ---- Modification types (admin) ----

class ModificationValueResponse(BaseModel):
    id: int
    modification_type_id: int
    value: str
    sort_order: int

    model_config = {"from_attributes": True}


class ModificationValueCreate(BaseModel):
    value: str
    sort_order: int = 0


class ModificationTypeResponse(BaseModel):
    id: int
    name: str
    sort_order: int
    values: list[ModificationValueResponse] = []

    model_config = {"from_attributes": True}


class ModificationTypeCreate(BaseModel):
    name: str
    sort_order: int = 0
    values: list[str] = []  # e.g. ["S", "M", "L"]


class ModificationTypeUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None


# ---- Product variants ----

class ProductVariantResponse(BaseModel):
    id: int
    product_id: int
    modification_type_id: int
    value: str
    quantity: int

    model_config = {"from_attributes": True}


class ProductVariantCreate(BaseModel):
    modification_type_id: int
    value: str
    quantity: int = 0


class ProductVariantUpdate(BaseModel):
    value: Optional[str] = None
    quantity: Optional[int] = None

