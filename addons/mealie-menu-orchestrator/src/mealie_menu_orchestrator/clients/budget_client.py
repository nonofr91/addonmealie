"""Client for communicating with Budget Advisor API."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class BudgetClient:
    """REST client for Budget Advisor API."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-Addon-Key"] = api_key
        self._client = httpx.Client(timeout=timeout, headers=headers)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BudgetClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def get_status(self) -> Optional[dict]:
        """Get budget advisor status."""
        try:
            resp = self._client.get(f"{self.base_url}/status")
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            logger.warning("Failed to get budget status: %s", exc)
            return None

    def get_recipe_cost(self, slug: str) -> Optional[dict]:
        """Get cost data for a specific recipe."""
        try:
            resp = self._client.get(f"{self.base_url}/recipes/{slug}/cost")
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            logger.warning("Failed to get cost for recipe %s: %s", slug, exc)
            return None

    def calculate_menu_cost(self, recipe_ids: list[str]) -> Optional[dict]:
        """Calculate total cost for a list of recipes."""
        try:
            resp = self._client.post(
                f"{self.base_url}/menu/cost",
                json={"recipe_ids": recipe_ids},
            )
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            logger.warning("Failed to calculate menu cost: %s", exc)
            return None

    def get_budget(self) -> Optional[dict]:
        """Get current budget status."""
        try:
            resp = self._client.get(f"{self.base_url}/budget")
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            logger.warning("Failed to get budget: %s", exc)
            return None
