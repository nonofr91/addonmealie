"""Client for communicating with Nutrition Advisor API."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class NutritionClient:
    """REST client for Nutrition Advisor API."""

    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["X-Addon-Key"] = api_key
        self._client = httpx.Client(timeout=timeout, headers=headers)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "NutritionClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def get_status(self) -> Optional[dict]:
        """Get nutrition advisor status."""
        try:
            resp = self._client.get(f"{self.base_url}/status")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Failed to get nutrition status: %s", exc)
            return None

    def get_recipe_nutrition(self, slug: str) -> Optional[dict]:
        """Get nutrition data for a specific recipe."""
        try:
            resp = self._client.get(f"{self.base_url}/nutrition/recipe/{slug}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Failed to get nutrition for recipe %s: %s", slug, exc)
            return None

    def scan_recipes(self) -> Optional[dict]:
        """Scan Mealie recipes for missing nutrition data."""
        try:
            resp = self._client.get(f"{self.base_url}/nutrition/scan")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Failed to scan recipes: %s", exc)
            return None

    def get_profiles(self) -> Optional[dict]:
        """Get household profiles."""
        try:
            resp = self._client.get(f"{self.base_url}/profiles")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Failed to get profiles: %s", exc)
            return None
