"""Main nutrition calculator — orchestrates USDA → OFF → AI fallback + cache."""

from __future__ import annotations

import logging
from typing import Optional

from ..models.nutrition import IngredientNutrition, NutritionFacts, RecipeNutritionResult
from .ai_estimator import AIEstimator
from .cache import NutritionCache, _normalize_key
from .ingredient_parser import parse_ingredient
from .open_food_facts import OpenFoodFactsClient
from .usda_client import USDAFoodDataCentralClient

logger = logging.getLogger(__name__)


class NutritionCalculator:
    """
    Calcule les valeurs nutritionnelles d'une recette.

    Stratégie par ingrédient :
    1. Vérifie le cache local
    2. Appel USDA FoodData Central (source gouvernementale stable)
    3. Fallback Open Food Facts si USDA ne retourne rien
    4. Fallback LLM si OFF ne retourne rien
    5. Sauvegarde dans le cache
    """

    def __init__(
        self,
        cache: Optional[NutritionCache] = None,
        usda_client: Optional[USDAFoodDataCentralClient] = None,
        off_client: Optional[OpenFoodFactsClient] = None,
        ai_estimator: Optional[AIEstimator] = None,
    ) -> None:
        self.cache = cache or NutritionCache()
        self.usda_client = usda_client or USDAFoodDataCentralClient()
        self.off_client = off_client or OpenFoodFactsClient()
        self.ai_estimator = ai_estimator or AIEstimator()

    def calculate_recipe(
        self,
        recipe_slug: str,
        recipe_name: str,
        ingredient_texts: list[str],
        servings: int = 1,
    ) -> RecipeNutritionResult:
        """Calcule la nutrition complète d'une recette."""
        logger.info("Calcul nutrition: '%s' (%d ingrédients, %d portions)", recipe_name, len(ingredient_texts), servings)

        result = RecipeNutritionResult(
            recipe_slug=recipe_slug,
            recipe_name=recipe_name,
            servings=max(servings, 1),
        )

        for raw_text in ingredient_texts:
            if not raw_text or not raw_text.strip():
                continue
            ing_nutrition = self._calculate_ingredient(raw_text)
            result.ingredients.append(ing_nutrition)

        result.compute()
        self.cache.save()

        logger.info(
            "✅ %s — %.0f kcal/portion (P:%.1fg F:%.1fg G:%.1fg)",
            recipe_name,
            result.per_serving.calories_kcal,
            result.per_serving.protein_g,
            result.per_serving.fat_g,
            result.per_serving.carbohydrate_g,
        )
        return result

    def _calculate_ingredient(self, raw_text: str) -> IngredientNutrition:
        """Calcule les données nutritionnelles pour un ingrédient."""
        parsed = parse_ingredient(raw_text)
        food_name = parsed.food_name

        facts_per_100g, typical_weight = self._lookup_nutrition(food_name)
        if facts_per_100g is None:
            logger.debug("Aucune donnée pour '%s' — valeurs nulles", food_name)
            facts_per_100g = NutritionFacts()

        # Si le parsed n'a pas de quantité explicite et qu'on a un typical_weight, l'utiliser
        quantity_g = parsed.quantity_g
        if quantity_g == 50.0 and typical_weight and typical_weight > 0:
            logger.debug("Utilisation du poids moyen OFF pour '%s': %s g au lieu de 50 g", food_name, typical_weight)
            quantity_g = typical_weight

        ing = IngredientNutrition(
            raw_text=raw_text,
            food_name=food_name,
            quantity_g=quantity_g,
            nutrition_per_100g=facts_per_100g,
        )
        ing.compute_total()
        return ing

    def _lookup_nutrition(self, food_name: str) -> tuple[Optional[NutritionFacts], Optional[float]]:
        """Cherche dans le cache, puis USDA, puis OFF, puis IA. Retourne (facts, typical_weight_g)."""
        cached = self.cache.get(food_name)
        if cached:
            # Essayer de récupérer le typical_weight depuis le cache
            key = _normalize_key(food_name)
            entry = self.cache._data.get(key)
            typical_weight = entry.get("typical_weight_g") if entry else None
            return cached, typical_weight

        # 1. Essayer USDA (source gouvernementale stable)
        logger.debug("USDA: recherche '%s'", food_name)
        usda_result, _ = self.usda_client.search(food_name)
        if usda_result and not usda_result.is_empty():
            self.cache.set(food_name, usda_result, None)
            return usda_result, None

        # 2. Fallback OFF
        logger.debug("OFF: recherche '%s'", food_name)
        off_result, typical_weight = self.off_client.search(food_name)
        if off_result and not off_result.is_empty():
            self.cache.set(food_name, off_result, typical_weight)
            return off_result, typical_weight

        # 3. Fallback AI
        logger.debug("AI fallback: estimation '%s'", food_name)
        ai_result = self.ai_estimator.estimate(food_name)
        if ai_result and not ai_result.is_empty():
            self.cache.set(food_name, ai_result, None)
            return ai_result, None

        return None, None

    def close(self) -> None:
        self.usda_client.close()
        self.off_client.close()
        self.cache.save()

    def __enter__(self) -> "NutritionCalculator":
        return self

    def __exit__(self, *args) -> None:
        self.close()
