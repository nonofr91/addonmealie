"""In-memory storage for menus (temporary - can be enhanced with persistent storage)."""

from __future__ import annotations

import logging
from typing import Optional

from .models.menu import Menu

logger = logging.getLogger(__name__)


class MenuStorage:
    """In-memory storage for menus (temporary implementation)."""

    def __init__(self) -> None:
        self._menus: dict[str, Menu] = {}

    def save(self, menu: Menu) -> None:
        """Save a menu to storage."""
        if not menu.id:
            logger.warning("Cannot save menu without ID")
            return
        self._menus[menu.id] = menu
        logger.debug("Saved menu %s with %d entries", menu.id, len(menu.entries))

    def get(self, menu_id: str) -> Optional[Menu]:
        """Get a menu by ID."""
        return self._menus.get(menu_id)

    def delete(self, menu_id: str) -> bool:
        """Delete a menu by ID."""
        if menu_id in self._menus:
            del self._menus[menu_id]
            logger.debug("Deleted menu %s", menu_id)
            return True
        return False

    def list_all(self) -> list[Menu]:
        """List all menus."""
        return list(self._menus.values())


# Global storage instance
_storage: Optional[MenuStorage] = None


def get_storage() -> MenuStorage:
    """Get the global storage instance."""
    global _storage
    if _storage is None:
        _storage = MenuStorage()
    return _storage
