"""Alternatives finder for recipe swapping in menu drafts."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from ..mealie_sync import MealieClient
from ..models.menu import MealType
from ..models.menu_draft import AlternativeRecipe, DraftSlot
from ..models.profile import MemberProfile
from ..planner.allergy_filter import AllergyFilter
from ..planner.scorer import RecipeScorer
from ..planner.variety_scorer import VarietyScorer

logger = logging.getLogger(__name__)

# Maximum number of alternatives to return
MAX_ALTERNATIVES = 5


class AlternativesFinder:
    """Finds alternative recipes for a given slot in a menu draft.
    
    Considers:
    - Profile compatibility (allergies, restrictions)
    - Nutrition requirements
    - Variety (anti-boredom)
    - Seasonality
    """
    
    def __init__(
        self,
        mealie_client: Optional[MealieClient] = None,
        nutrition_scorer: Optional[RecipeScorer] = None,
        variety_scorer: Optional[VarietyScorer] = None,
        allergy_filter: Optional[AllergyFilter] = None,
    ) -> None:
        self.client = mealie_client or MealieClient()
        self.nutrition_scorer = nutrition_scorer or RecipeScorer()
        self.variety_scorer = variety_scorer or VarietyScorer()
        self.allergy_filter = allergy_filter or AllergyFilter()
    
    def find_alternatives(
        self,
        current_recipe_slug: str,
        members: list[MemberProfile],
        meal_type: MealType,
        reference_date: date,
        exclude_slugs: Optional[set[str]] = None,
        min_score: float = 0.5,
    ) -> list[AlternativeRecipe]:
        """Find alternative recipes for a slot.
        
        Args:
            current_recipe_slug: Current recipe slug (excluded from results)
            members: Members present for this meal
            meal_type: Type of meal
            reference_date: Date for seasonality calculation
            exclude_slugs: Additional slugs to exclude
            min_score: Minimum composite score to include
            
        Returns:
            List of AlternativeRecipe sorted by score descending.
        """
        exclude = exclude_slugs or set()
        exclude.add(current_recipe_slug)
        
        logger.info(
            "Finding alternatives for %s on %s for %d members",
            current_recipe_slug, reference_date, len(members)
        )
        
        # Get all recipes
        all_recipes = self.client.get_all_recipes()
        
        # Get detailed info for recipes with nutrition
        from ..menu_drafting.draft_manager import DraftManager
        detailed = DraftManager._fetch_recipe_details(self, all_recipes)
        
        # Filter by allergies/restrictions
        from ..models.profile import HouseholdProfile
        household = HouseholdProfile(members=members)
        safe_recipes, _ = self.allergy_filter.filter_recipes(detailed, household)
        
        # Score candidates
        scored = []
        for recipe in safe_recipes:
            slug = recipe.get("slug", "")
            
            if slug in exclude:
                continue
            
            # Nutrition score
            nutrition_score = self.nutrition_scorer.score_for_household(
                recipe, members, meal_type
            )
            
            # Skip if nutrition compatibility is too low
            if nutrition_score < 0.4:
                continue
            
            # Variety score with nutrition
            composite, breakdown = self.variety_scorer.score_with_nutrition(
                recipe, nutrition_score, meal_type, reference_date
            )
            
            if composite < min_score:
                continue
            
            # Get additional info
            name = recipe.get("name", slug)
            recipe_id = recipe.get("id")
            
            # Get nutrition per serving
            from ..planner.scorer import _parse_mealie_nutrition
            nutrition = _parse_mealie_nutrition(recipe)
            
            servings_raw = recipe.get("recipeServings") or 1
            try:
                servings = max(int(float(servings_raw)), 1)
            except (ValueError, TypeError):
                servings = 1
            
            per_serving = nutrition.scale(1.0 / servings)
            
            # Get seasonal ingredients
            variety_result = self.variety_scorer.score(recipe, nutrition_score, meal_type, reference_date)
            
            # Get main ingredients for display
            main_ingredients = variety_result.seasonal_ingredients[:3]  # Top 3
            
            scored.append({
                "recipe": recipe,
                "slug": slug,
                "name": name,
                "recipe_id": recipe_id,
                "score": composite,
                "breakdown": breakdown,
                "nutrition": per_serving,
                "calories": per_serving.calories_kcal,
                "seasonal_ingredients": main_ingredients,
                "seasonal_score": variety_result.seasonality_score,
            })
        
        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)
        
        # Take top N
        top = scored[:MAX_ALTERNATIVES]
        
        # Build AlternativeRecipe objects
        alternatives = []
        for item in top:
            # Generate reason text
            reason = self._generate_reason(item, meal_type)
            
            alt = AlternativeRecipe(
                recipe_slug=item["slug"],
                recipe_name=item["name"],
                recipe_id=item["recipe_id"],
                score=item["score"],
                score_breakdown=item["breakdown"],
                nutrition_per_serving=item["nutrition"],
                calories_per_serving=item["calories"],
                reason=reason,
                main_ingredients=[si["ingredient"] for si in item["seasonal_ingredients"]],
                seasonal_score=item["seasonal_score"],
            )
            alternatives.append(alt)
        
        logger.info("Found %d alternatives", len(alternatives))
        return alternatives
    
    def _generate_reason(self, item: dict, meal_type: MealType) -> str:
        """Generate human-readable reason for suggestion."""
        breakdown = item["breakdown"]
        seasonal_ingredients = item["seasonal_ingredients"]
        
        reasons = []
        
        # Check scores
        nutrition = breakdown.get("nutrition", 0)
        variety = breakdown.get("variety", 0)
        seasonality = breakdown.get("seasonality", 0)
        
        if nutrition >= 0.8:
            reasons.append("excellent nutritional fit")
        elif nutrition >= 0.6:
            reasons.append("good nutritional match")
        
        if variety >= 0.8:
            reasons.append("high variety (not used recently)")
        elif variety >= 0.6:
            reasons.append("good variety score")
        
        # Check seasonal ingredients
        peak_ingredients = [si for si in seasonal_ingredients if si.get("is_peak")]
        if peak_ingredients:
            ing_names = [si["ingredient"] for si in peak_ingredients[:2]]
            reasons.append(f"peak season: {', '.join(ing_names)}")
        elif seasonal_ingredients:
            ing_names = [si["ingredient"] for si in seasonal_ingredients[:2]]
            reasons.append(f"in season: {', '.join(ing_names)}")
        
        # Meal type suitability
        if meal_type == MealType.breakfast:
            reasons.append("breakfast suitable")
        elif meal_type == MealType.lunch:
            reasons.append("lunch suitable")
        
        if not reasons:
            return "balanced choice"
        
        return "; ".join(reasons[:2])  # Max 2 reasons
    
    def swap_recipe(
        self,
        current_slot: DraftSlot,
        new_recipe_slug: str,
        members: list[MemberProfile],
        meal_type: MealType,
        reference_date: date,
    ) -> Optional[DraftSlot]:
        """Create a new slot with swapped recipe.
        
        Args:
            current_slot: Current slot to replace
            new_recipe_slug: New recipe slug
            members: Members present
            meal_type: Meal type
            reference_date: Date
            
        Returns:
            New DraftSlot or None if swap fails.
        """
        # Fetch new recipe
        new_recipe = self.client.get_recipe(new_recipe_slug)
        if not new_recipe:
            logger.error("Failed to fetch recipe: %s", new_recipe_slug)
            return None
        
        # Score it
        nutrition_score = self.nutrition_scorer.score_for_household(
            new_recipe, members, meal_type
        )
        
        composite, breakdown = self.variety_scorer.score_with_nutrition(
            new_recipe, nutrition_score, meal_type, reference_date
        )
        
        # Get nutrition
        from ..planner.scorer import _parse_mealie_nutrition
        nutrition = _parse_mealie_nutrition(new_recipe)
        
        servings_raw = new_recipe.get("recipeServings") or 1
        try:
            servings = max(int(float(servings_raw)), 1)
        except (ValueError, TypeError):
            servings = 1
        
        per_serving = nutrition.scale(1.0 / servings)
        
        # Create new slot preserving slot_id and locked status
        new_slot = DraftSlot(
            slot_id=current_slot.slot_id,  # Preserve ID
            meal_type=meal_type,
            recipe_slug=new_recipe_slug,
            recipe_name=new_recipe.get("name", new_recipe_slug),
            recipe_id=new_recipe.get("id"),
            servings=len(members),
            score=composite,
            score_breakdown=breakdown,
            nutrition_per_serving=per_serving,
            locked=current_slot.locked,  # Preserve locked status
            user_notes=current_slot.user_notes,  # Preserve notes
        )
        
        logger.info(
            "Swapped recipe in slot %s: %s -> %s (score: %.3f)",
            current_slot.slot_id, current_slot.recipe_name, new_slot.recipe_name, composite
        )
        
        return new_slot
    
    def close(self) -> None:
        """Close resources."""
        self.client.close()
        self.variety_scorer.close()
    
    def __enter__(self) -> "AlternativesFinder":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
