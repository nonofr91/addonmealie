"""Orchestrator for mealie-nutrition-advisor addon."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from .configs.nutrition_config import NutritionConfig, NutritionConfigError
from .nutrition_mealie_sync import MealieClient
from .nutrition.calculator import NutritionCalculator

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("mealie-nutrition")


class NutritionOrchestratorError(Exception):
    """Orchestrator execution error."""


class NutritionOrchestrator:
    """Orchestrator for nutrition enrichment operations."""

    def __init__(self, config: Optional[NutritionConfig] = None) -> None:
        self.config = config or NutritionConfig()
        self._calculator: Optional[NutritionCalculator] = None

    def _get_calculator(self) -> NutritionCalculator:
        """Get or create nutrition calculator."""
        if self._calculator is None:
            self._calculator = NutritionCalculator()
        return self._calculator

    def scan_recipes(self) -> dict[str, Any]:
        """Scan Mealie recipes to find those without nutrition data."""
        try:
            with MealieClient(
                base_url=self.config.mealie_base_url,
                api_key=self.config.mealie_api_key
            ) as client:
                recipes = client.get_recipes()
                
                without_nutrition = []
                with_nutrition = []
                
                for recipe in recipes:
                    slug = recipe.get("slug", "")
                    name = recipe.get("name", slug)
                    nutrition = recipe.get("nutrition", {})
                    
                    # Check if nutrition data exists and is meaningful
                    has_nutrition = bool(nutrition.get("calories") and float(nutrition.get("calories", 0)) > 0)
                    
                    if has_nutrition:
                        with_nutrition.append({"slug": slug, "name": name})
                    else:
                        without_nutrition.append({"slug": slug, "name": name})
                
                return {
                    "success": True,
                    "total": len(recipes),
                    "without_nutrition": without_nutrition,
                    "with_nutrition": with_nutrition,
                    "to_enrich": len(without_nutrition),
                }
        except Exception as exc:
            logger.error("Scan failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def enrich_all(self, force: bool = False) -> dict[str, Any]:
        """Enrich all recipes without nutrition (or all if force=True)."""
        try:
            scan_result = self.scan_recipes()
            if not scan_result.get("success"):
                return scan_result
            
            if force:
                recipes_to_enrich = scan_result["with_nutrition"] + scan_result["without_nutrition"]
            else:
                recipes_to_enrich = scan_result["without_nutrition"]
            
            enriched = []
            skipped = []
            failed = []
            
            with MealieClient(
                base_url=self.config.mealie_base_url,
                api_key=self.config.mealie_api_key
            ) as client:
                calculator = self._get_calculator()
                
                for recipe in recipes_to_enrich:
                    slug = recipe["slug"]
                    name = recipe["name"]
                    
                    try:
                        # Get recipe details
                        recipe_details = client.get_recipe(slug)
                        if not recipe_details:
                            failed.append({"slug": slug, "name": name, "error": "Recipe not found"})
                            continue
                        
                        # Extract ingredients
                        ingredient_texts = [
                            ing.get("note", ing.get("originalText", ing.get("display", ing.get("food", {}).get("name", ""))))
                            for ing in recipe_details.get("recipeIngredient", [])
                        ]
                        
                        logger.debug("Ingredients extracted for '%s': %s", name, ingredient_texts)
                        
                        if not ingredient_texts:
                            skipped.append({"slug": slug, "name": name, "reason": "No ingredients"})
                            continue
                        
                        # Calculate nutrition
                        result = calculator.calculate_recipe(slug, name, ingredient_texts)
                        
                        # Update Mealie with nutrition data
                        client.patch_nutrition(slug, {
                            "calories": str(result.total_recipe.calories_kcal),
                            "proteinContent": str(result.total_recipe.protein_g),
                            "fatContent": str(result.total_recipe.fat_g),
                            "carbohydrateContent": str(result.total_recipe.carbohydrate_g),
                            "fiberContent": str(result.total_recipe.fiber_g) if hasattr(result.total_recipe, 'fiber_g') else None,
                            "sodiumContent": str(result.total_recipe.sodium_mg) if hasattr(result.total_recipe, 'sodium_mg') else None,
                            "saturatedFatContent": str(result.total_recipe.saturated_fat_g) if hasattr(result.total_recipe, 'saturated_fat_g') else None,
                            "sugarContent": str(result.total_recipe.sugar_g) if hasattr(result.total_recipe, 'sugar_g') else None,
                        })
                        
                        enriched.append({
                            "slug": slug,
                            "name": name,
                            "calories": result.total_recipe.calories_kcal,
                        })
                        logger.info("Enriched: %s", name)
                        
                    except Exception as exc:
                        logger.error("Failed to enrich %s: %s", name, exc)
                        failed.append({"slug": slug, "name": name, "error": str(exc)})
            
            return {
                "success": True,
                "total": len(recipes_to_enrich),
                "enriched": enriched,
                "skipped": skipped,
                "failed": failed,
            }
        except Exception as exc:
            logger.error("Enrich all failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def enrich_recipe(self, slug: str) -> dict[str, Any]:
        """Enrich a single recipe by slug."""
        try:
            with MealieClient(
                base_url=self.config.mealie_base_url,
                api_key=self.config.mealie_api_key
            ) as client:
                # Get recipe details
                recipe_details = client.get_recipe(slug)
                if not recipe_details:
                    return {"success": False, "error": "Recipe not found"}
                
                name = recipe_details.get("name", slug)
                
                # Extract ingredients
                ingredient_texts = [
                    ing.get("note", ing.get("originalText", ing.get("display", ing.get("food", {}).get("name", ""))))
                    for ing in recipe_details.get("recipeIngredient", [])
                ]
                
                if not ingredient_texts:
                    return {"success": False, "error": "No ingredients found"}
                
                # Calculate nutrition
                calculator = self._get_calculator()
                result = calculator.calculate_recipe(slug, name, ingredient_texts)
                
                # Update Mealie with nutrition data
                client.patch_nutrition(slug, {
                    "calories": str(result.total_recipe.calories_kcal),
                    "proteinContent": str(result.total_recipe.protein_g),
                    "fatContent": str(result.total_recipe.fat_g),
                    "carbohydrateContent": str(result.total_recipe.carbohydrate_g),
                    "fiberContent": str(result.total_recipe.fiber_g) if hasattr(result.total_recipe, 'fiber_g') else None,
                    "sodiumContent": str(result.total_recipe.sodium_mg) if hasattr(result.total_recipe, 'sodium_mg') else None,
                    "saturatedFatContent": str(result.total_recipe.saturated_fat_g) if hasattr(result.total_recipe, 'saturated_fat_g') else None,
                    "sugarContent": str(result.total_recipe.sugar_g) if hasattr(result.total_recipe, 'sugar_g') else None,
                })
                
                return {
                    "success": True,
                    "slug": slug,
                    "name": name,
                    "calories": result.total_recipe.calories_kcal,
                    "protein": result.total_recipe.protein_g,
                    "fat": result.total_recipe.fat_g,
                    "carbohydrates": result.total_recipe.carbohydrate_g,
                }
        except Exception as exc:
            logger.error("Failed to enrich recipe %s: %s", slug, exc)
            return {"success": False, "error": str(exc)}

    def get_status(self) -> dict[str, Any]:
        """Get status of nutrition addon."""
        try:
            scan_result = self.scan_recipes()
            
            return {
                "success": True,
                "mealie_base_url": self.config.mealie_base_url,
                "ai_provider": self.config.ai_provider,
                "use_ai_estimation": self.config.use_ai_estimation,
                "total_recipes": scan_result.get("total", 0),
                "recipes_without_nutrition": scan_result.get("to_enrich", 0),
                "recipes_with_nutrition": scan_result.get("total", 0) - scan_result.get("to_enrich", 0),
            }
        except Exception as exc:
            logger.error("Get status failed: %s", exc)
            return {"success": False, "error": str(exc)}
