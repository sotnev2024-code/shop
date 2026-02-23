from abc import ABC, abstractmethod
from typing import Any


class BaseCheckout(ABC):
    """Abstract base for checkout strategies."""

    @abstractmethod
    def get_required_fields(self) -> list[str]:
        """Return list of required fields for this checkout type."""
        ...

    @abstractmethod
    async def process(self, order_data: dict[str, Any]) -> dict[str, Any]:
        """Process checkout. Returns result dict."""
        ...





