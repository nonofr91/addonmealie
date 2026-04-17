"""Sync computed nutrition data back to Mealie via REST API."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

from .models.nutrition import RecipeNutritionResult
from .nutrition.calculator import NutritionCalculator

logger = logging.getLogger(__name__)

MEALIE_BASE_URL = os.environ.get("MEALIE_BASE_URL", "http://localhost:9000")
MEALIE_API_KEY = os.environ.get("MEALIE_API_KEY", "")
REQUEST_TIMEOUT = 30.0


class MealieClient:
    """Thin REST client for Mealie — reads recipes and patches nutrition."""

    def __init__(self, base_url: str = MEALIE_BASE_URL, api_key: str = MEALIE_API_KEY) -> None:
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
        """Liste les recettes (résumé)."""
        resp = self._client.get(
            f"{self.base_url}/api/recipes",
            params={"page": page, "perPage": per_page},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])

    def get_all_recipes(self) -> list[dict]:
        """Récupère toutes les recettes (paginate automatiquement)."""
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
        """Récupère le détail d'une recette par slug."""
        try:
            resp = self._client.get(f"{self.base_url}/api/recipes/{slug}")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Recette introuvable: %s (%s)", slug, exc)
            return None

    def patch_nutrition(self, slug: str, nutrition_payload: dict) -> bool:
        """Patch le champ nutrition d'une recette."""
        try:
            # Ajouter l'unité "kcal" à la valeur calories pour l'affichage correct
            if "calories" in nutrition_payload:
                calories_value = nutrition_payload["calories"]
                if isinstance(calories_value, (int, float)):
                    nutrition_payload["calories"] = f"{calories_value} kcal"
                elif isinstance(calories_value, str) and calories_value.replace(".", "").isdigit():
                    nutrition_payload["calories"] = f"{calories_value} kcal"
            
            # Patch uniquement nutrition pour ne pas affecter l'affichage des autres champs
            resp = self._client.patch(
                f"{self.base_url}/api/recipes/{slug}",
                json={"nutrition": nutrition_payload},
            )
            resp.raise_for_status()
            logger.debug("Nutrition patchée: %s", slug)
            return True
        except httpx.HTTPStatusError as exc:
            logger.warning("Patch nutrition échoué pour '%s': %s", slug, exc)
            return False

    def create_mealplan_bulk(self, entries: list[dict]) -> bool:
        """Crée plusieurs entrées de planning en une requête."""
        try:
            resp = self._client.post(
                f"{self.base_url}/api/households/mealplans/bulk",
                json=entries,
            )
            resp.raise_for_status()
            return True
        except httpx.HTTPStatusError as exc:
            logger.warning("Création mealplan échouée: %s", exc)
            return False


def _extract_ingredient_texts(recipe: dict) -> list[str]:
    """Extrait les textes d'ingrédients depuis le format Mealie."""
    ingredients = recipe.get("recipeIngredient", [])
    texts: list[str] = []
    for ing in ingredients:
        if isinstance(ing, str):
            texts.append(ing)
        elif isinstance(ing, dict):
            note = ing.get("note", "")
            display = ing.get("display", "")
            texts.append(note or display or "")
    return [t for t in texts if t.strip()]


def _has_nutrition(recipe: dict) -> bool:
    """Retourne True si la recette a déjà une nutrition non vide."""
    nutrition = recipe.get("nutrition") or {}
    calories = nutrition.get("calories")
    return bool(calories and str(calories).strip() not in ("", "0", "null"))


class MealieNutritionSync:
    """Orchestrateur d'enrichissement nutritionnel pour les recettes Mealie."""

    def __init__(
        self,
        mealie_client: Optional[MealieClient] = None,
        calculator: Optional[NutritionCalculator] = None,
    ) -> None:
        self.client = mealie_client or MealieClient()
        self.calculator = calculator or NutritionCalculator()

    def enrich_all(self, force: bool = False) -> dict:
        """
        Enrichit toutes les recettes Mealie.

        Args:
            force: Si True, recalcule même les recettes qui ont déjà une nutrition.

        Returns:
            Rapport {total, enriched, skipped, failed}.
        """
        recipes = self.client.get_all_recipes()
        report = {"total": len(recipes), "enriched": 0, "skipped": 0, "failed": 0}

        for i, recipe_summary in enumerate(recipes, 1):
            slug = recipe_summary.get("slug", "")
            name = recipe_summary.get("name", slug)
            logger.info("[%d/%d] %s", i, len(recipes), name)

            if not force and _has_nutrition(recipe_summary):
                logger.debug("  ↷ nutrition existante, ignorée (--force pour recalculer)")
                report["skipped"] += 1
                continue

            recipe_detail = self.client.get_recipe(slug)
            if not recipe_detail:
                report["failed"] += 1
                continue

            ingredient_texts = _extract_ingredient_texts(recipe_detail)
            if not ingredient_texts:
                logger.debug("  ↷ aucun ingrédient exploitable")
                report["skipped"] += 1
                continue

            servings_raw = recipe_detail.get("recipeServings") or recipe_detail.get("recipeYieldQuantity") or 1
            try:
                servings = int(float(servings_raw))
            except (ValueError, TypeError):
                servings = 1

            try:
                result: RecipeNutritionResult = self.calculator.calculate_recipe(
                    recipe_slug=slug,
                    recipe_name=name,
                    ingredient_texts=ingredient_texts,
                    servings=servings,
                )
                mealie_nutrition = result.to_mealie_nutrition()
                ok = self.client.patch_nutrition(slug, mealie_nutrition)
                if ok:
                    report["enriched"] += 1
                    print(
                        f"  ✅ {name}: {round(result.per_serving.calories_kcal)} kcal/portion "
                        f"(P:{round(result.per_serving.protein_g)}g "
                        f"F:{round(result.per_serving.fat_g)}g "
                        f"G:{round(result.per_serving.carbohydrate_g)}g)"
                    )
                else:
                    report["failed"] += 1
            except Exception as exc:
                logger.error("Erreur calcul pour '%s': %s", name, exc)
                report["failed"] += 1

        self.calculator.cache.save()
        return report

    def close(self) -> None:
        self.client.close()
        self.calculator.close()

    def __enter__(self) -> "MealieNutritionSync":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
