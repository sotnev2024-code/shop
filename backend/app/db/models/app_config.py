from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AppConfig(Base):
    __tablename__ = "app_config"

    id: Mapped[int] = mapped_column(primary_key=True)

    # --- Shop settings (admin-editable) ---
    shop_name: Mapped[str] = mapped_column(String(255), default="My Shop")
    currency: Mapped[str] = mapped_column(String(10), default="RUB")
    store_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    delivery_city: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=None)
    delivery_cost: Mapped[float] = mapped_column(Float, default=0)
    free_delivery_min_amount: Mapped[float] = mapped_column(Float, default=0)
    min_order_amount_pickup: Mapped[float] = mapped_column(Float, default=0)
    min_order_amount_delivery: Mapped[float] = mapped_column(Float, default=0)

    # --- Module toggles (owner-editable) ---
    checkout_type: Mapped[str] = mapped_column(String(50), default="basic")
    product_source: Mapped[str] = mapped_column(String(50), default="database")
    delivery_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    pickup_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    promo_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    mailing_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # --- Integration keys (owner-editable) ---
    moysklad_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    one_c_endpoint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    one_c_login: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=None)
    one_c_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, default=None)
    payment_provider_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    yandex_maps_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    support_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)

    # --- Delivery service toggles (owner-editable, future-proofing) ---
    delivery_sdek_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_pochta_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    delivery_yandex_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Banner display (admin-editable, applies to all banners) ---
    banner_aspect_shape: Mapped[str] = mapped_column(String(20), default="rectangle")
    banner_size: Mapped[str] = mapped_column(String(20), default="medium")

    # --- Category image size in catalog (admin-editable: small, medium, large, xlarge) ---
    category_image_size: Mapped[str] = mapped_column(String(20), default="medium")

    # --- Admins: comma-separated telegram_id; if set, overrides .env ADMIN_IDS ---
    admin_ids: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)

    # --- Bonus system (admin-editable) ---
    bonus_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    bonus_welcome_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    bonus_welcome_amount: Mapped[float] = mapped_column(Float, default=0)
    bonus_purchase_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    bonus_purchase_percent: Mapped[float] = mapped_column(Float, default=0)
    bonus_spend_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    bonus_spend_limit_type: Mapped[str] = mapped_column(String(20), default="percent")
    bonus_spend_limit_value: Mapped[float] = mapped_column(Float, default=0)
