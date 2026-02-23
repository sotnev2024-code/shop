from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseProductLoader(ABC):
    """Abstract base class for product loaders."""

    @abstractmethod
    async def load_products(self) -> List[Dict[str, Any]]:
        """Load products from source."""
        ...

    @abstractmethod
    async def sync_products(self) -> int:
        """Sync products from external source to database. Returns count of synced products."""
        ...





