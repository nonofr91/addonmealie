"""Combined scoring engine for multi-criteria menu evaluation."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from ..config import MenuOrchestratorConfig
from ..clients.budget_client import BudgetClient
from ..clients.nutrition_client import NutritionClient

logger = logging.getLogger(__name__)


class CombinedScorer:
    """
    Scores recipes based on multiple criteria: nutrition, budget, variety, season.
    
    Formula:
    Score(recipe) = w1 * nutrition_score + w2 * budget_score + w3 * variety_score + w4 * season_score
    
    Where:
    - nutrition_score: score from Nutrition Advisor (0-1)
    - budget_score: inverse of normalized cost (0-1)
    - variety_score: based on menu history (0-1)
    - season_score: 1 if current season, 0 otherwise (or graduated)
    - w1, w2, w3, w4: weights (default 0.25 each)
    """

    def __init__(
        self,
        config: MenuOrchestratorConfig,
        nutrition_client: NutritionClient,
        budget_client: BudgetClient,
    ) -> None:
        self.config = config
        self.nutrition_client = nutrition_client
        self.budget_client = budget_client

    def score_recipe(
        self,
        recipe_slug: str,
        menu_history: Optional[list[str]] = None,
        current_date: Optional[date] = None,
    ) -> dict[str, float]:
        """
        Calculate combined score for a recipe.
        
        Args:
            recipe_slug: Recipe slug
            menu_history: List of recipe slugs used in recent menus (for variety)
            current_date: Current date (for seasonality)
            
        Returns:
            Dictionary with individual scores and combined score
        """
        scores: dict[str, float] = {
            "nutrition": 0.0,
            "budget": 0.0,
            "variety": 0.0,
            "season": 0.0,
            "combined": 0.0,
        }

        # Nutrition score
        nutrition_data = self.nutrition_client.get_recipe_nutrition(recipe_slug)
        if nutrition_data:
            # Normalize nutrition score (0-1)
            scores["nutrition"] = self._normalize_nutrition_score(nutrition_data)

        # Budget score
        cost_data = self.budget_client.get_recipe_cost(recipe_slug)
        if cost_data:
            # Inverse cost: lower cost = higher score
            cost = cost_data.get("total_cost", 0)
            scores["budget"] = self._normalize_cost_score(cost)

        # Variety score (avoid repetition)
        if menu_history and recipe_slug in menu_history:
            # Penalize recently used recipes with exponential decay
            recent_count = menu_history.count(recipe_slug)
            # Plus la recette a été utilisée récemment, plus la pénalité est forte
            # Formule: 1.0 - (count * 0.15) pour une pénalité progressive
            penalty = min(0.8, recent_count * 0.15)
            scores["variety"] = max(0.0, 1.0 - penalty)
        else:
            scores["variety"] = 1.0  # Points complets pour les nouvelles recettes

        # Season score (if enabled)
        if self.config.enable_seasonality:
            scores["season"] = self._calculate_season_score(recipe_slug, current_date)
        else:
            scores["season"] = 1.0  # Neutral if disabled

        # Calculate combined score
        scores["combined"] = (
            self.config.weight_nutrition * scores["nutrition"]
            + self.config.weight_budget * scores["budget"]
            + self.config.weight_variety * scores["variety"]
            + self.config.weight_season * scores["season"]
        )

        logger.debug(
            "Recipe %s scores: nutrition=%.2f budget=%.2f variety=%.2f season=%.2f combined=%.2f",
            recipe_slug,
            scores["nutrition"],
            scores["budget"],
            scores["variety"],
            scores["season"],
            scores["combined"],
        )

        return scores

    def _normalize_nutrition_score(self, nutrition_data: dict) -> float:
        """Normalize nutrition data to 0-1 score."""
        # Simple heuristic: based on protein content and calorie balance
        calories = nutrition_data.get("calories", 0)
        protein = nutrition_data.get("protein", 0)
        
        if calories == 0:
            return 0.0
        
        # Target: ~25% of calories from protein (4 cal/g)
        target_protein_ratio = 0.25
        actual_protein_ratio = (protein * 4) / calories if calories > 0 else 0
        
        # Score based on how close to target
        score = 1.0 - abs(actual_protein_ratio - target_protein_ratio)
        return max(0.0, min(1.0, score))

    def _normalize_cost_score(self, cost: float) -> float:
        """Normalize cost to 0-1 score (lower cost = higher score)."""
        # Assume reasonable cost per serving is 2-10 currency units
        max_reasonable_cost = 10.0
        score = 1.0 - (cost / max_reasonable_cost)
        return max(0.0, min(1.0, score))

    def _calculate_season_score(self, recipe_slug: str, current_date: Optional[date]) -> float:
        """
        Calculate season score for a recipe.
        
        For now, return neutral score (1.0) until season tags are implemented.
        Will be enhanced when seasonality is added to Nutrition Advisor.
        """
        # TODO: Implement proper seasonality checking once tags are added
        # For now, return neutral score
        return 1.0

    def rank_recipes(
        self,
        recipe_slugs: list[str],
        menu_history: Optional[list[str]] = None,
        current_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> list[tuple[str, float]]:
        """
        Rank recipes by combined score.
        
        Args:
            recipe_slugs: List of recipe slugs to rank
            menu_history: List of recipe slugs used in recent menus
            current_date: Current date (for seasonality)
            limit: Maximum number of recipes to return
            
        Returns:
            List of (recipe_slug, score) tuples sorted by score descending
        """
        scored_recipes: list[tuple[str, float]] = []
        
        for slug in recipe_slugs:
            scores = self.score_recipe(slug, menu_history, current_date)
            scored_recipes.append((slug, scores["combined"]))
        
        # Sort by score descending
        scored_recipes.sort(key=lambda x: x[1], reverse=True)
        
        if limit:
            scored_recipes = scored_recipes[:limit]
        
        return scored_recipes
