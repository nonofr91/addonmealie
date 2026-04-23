"""Calculateur de coût pour les recettes Mealie."""

import logging
from typing import Optional

import requests

from ..models.cost import CostBreakdown, IngredientCost, RecipeCost
from .ingredient_matcher import IngredientMatcher
from .manual_pricer import ManualPricer
from .open_prices_client import OpenPricesClient

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calcule le coût des recettes en combinant toutes les sources de prix."""

    def __init__(
        self,
        mealie_base_url: Optional[str] = None,
        mealie_api_key: Optional[str] = None,
        ingredient_matcher: Optional[IngredientMatcher] = None,
    ) -> None:
        self.mealie_base_url = (mealie_base_url or "http://localhost:9925").rstrip("/")
        self.mealie_api_key = mealie_api_key or ""

        # Initialiser le matcher avec ses dépendances
        if ingredient_matcher:
            self.matcher = ingredient_matcher
        else:
            manual = ManualPricer()
            open_prices = OpenPricesClient()
            self.matcher = IngredientMatcher(manual, open_prices)

        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "Authorization": f"Bearer {self.mealie_api_key}" if self.mealie_api_key else "",
        })

    def get_recipe(self, slug: str) -> Optional[dict]:
        """Récupère une recette depuis Mealie."""
        try:
            response = self._session.get(
                f"{self.mealie_base_url}/api/recipes/{slug}",
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur récupération recette {slug}: {e}")
            return None

    def calculate_cost(
        self,
        recipe_slug: str,
        use_open_prices: bool = True,
    ) -> Optional[RecipeCost]:
        """Calcule le coût d'une recette.

        Args:
            recipe_slug: Slug de la recette dans Mealie
            use_open_prices: Utiliser Open Prices comme fallback

        Returns:
            RecipeCost ou None si erreur
        """
        recipe = self.get_recipe(recipe_slug)
        if not recipe:
            return None

        recipe_name = recipe.get("name", recipe_slug)
        servings = self._extract_servings(recipe)

        # Extraire les ingrédients
        ingredients = recipe.get("recipeIngredient", [])
        if not ingredients:
            logger.warning(f"Recette {recipe_slug} sans ingrédients")

        breakdown = CostBreakdown(ingredients=[])
        total_confidence = 0.0

        for ing_data in ingredients:
            note = self._extract_note(ing_data)
            if not note:
                continue

            # Parser la note
            quantity, unit, name = self.matcher.parse_ingredient_note(note)

            # Trouver le prix
            price, source, confidence = self.matcher.find_price(
                name, quantity, unit, use_open_prices
            )

            total_confidence += confidence

            ing_cost = IngredientCost(
                ingredient_name=name,
                original_note=note,
                quantity=quantity,
                unit=unit,
                price_per_unit=self._calculate_price_per_unit(price, quantity),
                total_cost=price,
                price_source=source,
                confidence=confidence,
            )
            breakdown.ingredients.append(ing_cost)

        # Calculer la confiance moyenne
        if breakdown.ingredients:
            avg_confidence = total_confidence / len(breakdown.ingredients)
        else:
            avg_confidence = 0.0

        return RecipeCost(
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            servings=servings,
            breakdown=breakdown,
        )

    def calculate_batch_costs(
        self,
        slugs: list[str],
        use_open_prices: bool = True,
    ) -> list[RecipeCost]:
        """Calcule les coûts pour plusieurs recettes.

        Args:
            slugs: Liste des slugs de recettes
            use_open_prices: Utiliser Open Prices

        Returns:
            Liste des RecipeCost (erreurs ignorées)
        """
        results = []
        for slug in slugs:
            cost = self.calculate_cost(slug, use_open_prices)
            if cost:
                results.append(cost)
        return results

    def _extract_servings(self, recipe: dict) -> int:
        """Extrait le nombre de portions d'une recette."""
        servings_raw = recipe.get("recipeServings") or recipe.get("recipeYield") or "1"
        try:
            # Peut être "4 portions" ou juste "4"
            import re
            numbers = re.findall(r'\d+', str(servings_raw))
            if numbers:
                return max(1, int(numbers[0]))
        except (ValueError, TypeError):
            pass
        return 1

    def _extract_note(self, ingredient_data: dict) -> str:
        """Extrait le texte d'un ingrédient."""
        # Format Mealie v1: {note: "2 cuillères d'huile"}
        # Format Mealie v2: {display: "2 cuillères d'huile", food: {...}}
        note = ingredient_data.get("note", "")
        if not note:
            # Essayer d'autres champs
            note = ingredient_data.get("display", "")
        if not note and ingredient_data.get("food"):
            # Construire depuis l'objet food + quantité
            food = ingredient_data.get("food", {})
            food_name = food.get("name", "")
            quantity = ingredient_data.get("quantity", "")
            unit = ingredient_data.get("unit", {}).get("name", "")
            if food_name:
                note = f"{quantity} {unit} {food_name}".strip()
        return note

    def _calculate_price_per_unit(self, total_price: float, quantity: float) -> float:
        """Calcule le prix par unité."""
        if quantity == 0:
            return 0.0
        return round(total_price / quantity, 4)

    def compare_recipes_by_cost(
        self,
        slugs: list[str],
        per_serving: bool = True,
    ) -> list[tuple[str, float]]:
        """Compare plusieurs recettes par coût.

        Args:
            slugs: Liste des slugs
            per_serving: Comparer par portion (vs total)

        Returns:
            Liste triée (slug, coût)
        """
        costs = []
        for slug in slugs:
            cost = self.calculate_cost(slug)
            if cost:
                price = cost.cost_per_serving if per_serving else cost.total_cost
                costs.append((slug, price))

        return sorted(costs, key=lambda x: x[1])
