from __future__ import annotations

from typing import Any

from app.services.checkout.base import BaseCheckout


class BasicCheckout(BaseCheckout):
    """Basic checkout: name, phone, address (text)."""

    def get_required_fields(self) -> list[str]:
        return ["customer_name", "customer_phone", "address"]

    async def process(self, order_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "customer_name": order_data["customer_name"],
            "customer_phone": order_data["customer_phone"],
            "address": order_data.get("address", ""),
        }





