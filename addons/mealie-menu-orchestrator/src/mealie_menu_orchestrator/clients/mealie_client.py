"""Client for communicating with Mealie API."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class MealieClient:
    """REST client for Mealie API."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MealieClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def get_recipes(self, page: int = 1, per_page: int = 100) -> list[dict]:
        """List recipes (summary)."""
        resp = self._client.get(
            f"{self.base_url}/api/recipes",
            params={"page": page, "perPage": per_page},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])

    def get_all_recipes(self) -> list[dict]:
        """Get all recipes (paginate automatically)."""
        all_recipes: list[dict] = []
        page = 1
        while True:
            batch = self.get_recipes(page=page, per_page=100)
            if not batch:
                break
            all_recipes.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        logger.info("Mealie: %d recipes retrieved", len(all_recipes))
        return all_recipes

    def get_recipe(self, slug: str) -> Optional[dict]:
        """Get recipe detail by slug."""
        try:
            resp = self._client.get(f"{self.base_url}/api/recipes/{slug}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Recipe not found: %s (%s)", slug, exc)
            return None

    def create_mealplan(self, entry: dict) -> bool:
        """Create a mealplan entry."""
        try:
            payload = {
                "date": entry.get("date"),
                "entryType": entry.get("entry_type", "dinner"),
            }
            if entry.get("recipe_id"):
                payload["recipeId"] = entry["recipe_id"]
            if entry.get("title"):
                payload["title"] = entry["title"]

            resp = self._client.post(
                f"{self.base_url}/api/households/mealplans",
                json=payload,
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPStatusError as exc:
            logger.warning("Mealplan creation failed: %s", exc)
            return False

    def get_mealplans(self, start_date: str, end_date: str) -> list[dict]:
        """Get mealplans for a date range."""
        try:
            resp = self._client.get(
                f"{self.base_url}/api/households/mealplans",
                params={"startDate": start_date, "endDate": end_date},
            )
            resp.raise_for_status()
            return resp.json().get("items", [])
        except httpx.HTTPStatusError as exc:
            logger.warning("Failed to get mealplans: %s", exc)
            return []
