from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class CheckoutType(str, Enum):
    BASIC = "basic"
    ENHANCED = "enhanced"
    PAYMENT = "payment"
    FULL = "full"


class ProductSource(str, Enum):
    DATABASE = "database"
    MOYSKLAD = "moysklad"
    ONE_C = "one_c"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Dev
    dev_mode: bool = False

    # Shop
    shop_name: str = "Магазин"

    # Bot
    bot_token: str = "YOUR_BOT_TOKEN_HERE"
    webapp_url: str = "http://localhost:3000"
    admin_chat_id: int = 0

    # Modules
    checkout_type: CheckoutType = CheckoutType.BASIC
    product_source: ProductSource = ProductSource.DATABASE
    delivery_enabled: bool = False
    pickup_enabled: bool = True
    promo_enabled: bool = True
    mailing_enabled: bool = True

    # Sync
    sync_interval_minutes: int = 15

    # Support
    support_link: str = ""

    # Integrations
    yandex_maps_key: Optional[str] = None
    payment_provider_token: Optional[str] = None
    moysklad_token: Optional[str] = None
    one_c_endpoint: Optional[str] = None
    one_c_login: Optional[str] = None
    one_c_password: Optional[str] = None

    # Database (SQLite for local dev, PostgreSQL for production)
    database_url: str = "sqlite+aiosqlite:///./shop.db"
    redis_url: str = ""

    # Security
    admin_ids: str = ""
    owner_id: int = 0
    secret_key: str = "change-me-to-random-string"

    @property
    def admin_id_list(self) -> list[int]:
        if not self.admin_ids:
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]


settings = Settings()

