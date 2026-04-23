"""Thin Mealie REST client used by the budget addon (read-only)."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30.0


class MealieClient:
    """Mealie REST client — lecture des recettes + écriture des `extras`."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
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
        resp = self._client.get(
            f"{self.base_url}/api/recipes",
            params={"page": page, "perPage": per_page},
        )
        resp.raise_for_status()
        return resp.json().get("items", [])

    def get_all_recipes(self) -> list[dict]:
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
        logger.info("Mealie: %d recettes récupérées", len(all_recipes))
        return all_recipes

    def get_recipe(self, slug: str) -> Optional[dict]:
        try:
            resp = self._client.get(f"{self.base_url}/api/recipes/{slug}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Recette introuvable: %s (%s)", slug, exc)
            return None

    def patch_extras(self, slug: str, extras: dict[str, str]) -> bool:
        """Écrit le champ ``extras`` d'une recette Mealie.

        Mealie remplace le dict ``extras`` lors d'un PATCH : l'appelant
        doit donc fournir la version fusionnée complète (voir
        ``recipe_extras.merge_extras``).
        """
        try:
            resp = self._client.patch(
                f"{self.base_url}/api/recipes/{slug}",
                json={"extras": {k: str(v) for k, v in extras.items()}},
            )
            resp.raise_for_status()
            logger.debug("Extras patchés pour %s", slug)
            return True
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Patch extras échoué pour %s: %s — %s",
                slug,
                exc,
                exc.response.text if exc.response is not None else "",
            )
            return False
        except httpx.HTTPError as exc:
            logger.warning("Patch extras échoué pour %s: %s", slug, exc)
            return False

    @staticmethod
    def extract_ingredient_texts(recipe: dict) -> list[str]:
        """Extract free-form ingredient lines from a Mealie recipe payload."""
        ingredients = recipe.get("recipeIngredient", [])
        out: list[str] = []
        for ing in ingredients:
            if isinstance(ing, str):
                out.append(ing)
            elif isinstance(ing, dict):
                note = ing.get("note") or ""
                display = ing.get("display") or ""
                quantity = ing.get("quantity")
                unit = (ing.get("unit") or {}).get("name") if isinstance(ing.get("unit"), dict) else ing.get("unit")
                food = (ing.get("food") or {}).get("name") if isinstance(ing.get("food"), dict) else None

                # Prefer a rich (quantity + unit + food) reconstruction when available,
                # fall back to the raw note / display otherwise.
                parts: list[str] = []
                if quantity is not None:
                    parts.append(str(quantity))
                if unit:
                    parts.append(str(unit))
                if food:
                    parts.append(str(food))
                reconstructed = " ".join(parts).strip()
                out.append(reconstructed or note or display)
        return [t for t in out if t]

    @staticmethod
    def servings(recipe: dict) -> int:
        raw = recipe.get("recipeServings") or recipe.get("recipeYield") or 1
        try:
            return max(int(float(raw)), 1)
        except (TypeError, ValueError):
            return 1
