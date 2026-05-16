"""Combined scoring engine for multi-criteria menu evaluation."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from typing import Optional

from ..config import MenuOrchestratorConfig
from ..clients.budget_client import BudgetClient
from ..clients.nutrition_client import NutritionClient

logger = logging.getLogger(__name__)


class CombinedScorer:
    """
    Scores recipes based on multiple criteria: nutrition, budget, variety, season, rating, time.
    
    Formula:
    Score(recipe) = average of available criteria scores (equal weighting)
    
    Where:
    - nutrition_score: score from Nutrition Advisor (0-1)
    - budget_score: inverse of normalized cost (0-1)
    - variety_score: based on menu history (0-1)
    - season_score: 1 if current season, 0 otherwise (or graduated)
    - rating_score: normalized Mealie rating (0-1, 0 is neutral)
    - time_score: based on preparation time (penalized if > 2h)
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
        self.household_profiles: Optional[dict] = None

    def set_household_profiles(self, profiles: dict) -> None:
        """Set household profiles for pathology-aware nutrition scoring."""
        self.household_profiles = profiles

    def score_recipe(
        self,
        recipe_slug: str,
        menu_history: Optional[list[str]] = None,
        current_date: Optional[date] = None,
        recipe_tags: Optional[list[str]] = None,
        recipe_metadata: Optional[dict] = None,
    ) -> dict[str, float]:
        """
        Calculate combined score for a recipe with equal weighting of available criteria.
        
        Args:
            recipe_slug: Recipe slug
            menu_history: List of recipe slugs used in recent menus (for variety)
            current_date: Current date (for seasonality)
            recipe_tags: Recipe tags from Mealie
            recipe_metadata: Full recipe metadata including time and rating
            
        Returns:
            Dictionary with individual scores and combined score
        """
        scores: dict[str, float] = {
            "nutrition": 0.0,
            "budget": 0.0,
            "variety": 0.0,
            "season": 0.0,
            "rating": 0.0,
            "time": 0.0,
            "combined": 0.0,
        }

        # Track which criteria are available
        available_criteria = []

        # Nutrition score
        nutrition_data = self.nutrition_client.get_recipe_nutrition(recipe_slug)
        if nutrition_data:
            # Normalize nutrition score (0-1) with pathology awareness
            scores["nutrition"] = self._normalize_nutrition_score(
                nutrition_data, household_profiles=self.household_profiles
            )
            available_criteria.append("nutrition")

        # Budget score
        cost_data = self.budget_client.get_recipe_cost(recipe_slug)
        if cost_data:
            cost = cost_data.get("total_cost", 0)
            scores["budget"] = self._normalize_cost_score(cost)
            available_criteria.append("budget")

        # Variety score (avoid repetition)
        if menu_history and recipe_slug in menu_history:
            recent_count = menu_history.count(recipe_slug)
            penalty = min(0.8, recent_count * 0.15)
            scores["variety"] = max(0.0, 1.0 - penalty)
        else:
            scores["variety"] = 1.0
        available_criteria.append("variety")

        # Season score (if enabled)
        if self.config.enable_seasonality:
            scores["season"] = self._calculate_season_score(recipe_tags or [], current_date)
        else:
            scores["season"] = 1.0
        available_criteria.append("season")

        # Rating score (Mealie rating: 0-5, 0 is neutral)
        if recipe_metadata:
            rating = recipe_metadata.get("rating", 0)
            scores["rating"] = self._normalize_rating_score(rating)
            available_criteria.append("rating")

        # Time score (penalize if > 2h)
        if recipe_metadata:
            total_time_minutes = self._extract_total_time(recipe_metadata)
            scores["time"] = self._normalize_time_score(total_time_minutes)
            available_criteria.append("time")

        # Calculate combined score as equal average of available criteria
        if available_criteria:
            scores["combined"] = sum(scores[c] for c in available_criteria) / len(available_criteria)
        else:
            scores["combined"] = 0.0

        logger.debug(
            "Recipe %s scores: nutrition=%.2f budget=%.2f variety=%.2f season=%.2f rating=%.2f time=%.2f combined=%.2f",
            recipe_slug,
            scores["nutrition"],
            scores["budget"],
            scores["variety"],
            scores["season"],
            scores["rating"],
            scores["time"],
            scores["combined"],
        )

        return scores

    def _normalize_nutrition_score(self, nutrition_data: dict, household_profiles: Optional[dict] = None) -> float:
        """Normalize nutrition data to 0-1 score with pathology awareness."""
        calories = nutrition_data.get("calories", 0)
        protein = nutrition_data.get("protein", 0)
        sodium = nutrition_data.get("sodium", 0)
        
        if calories == 0:
            return 0.0
        
        # Base score: protein ratio
        target_protein_ratio = 0.25
        actual_protein_ratio = (protein * 4) / calories if calories > 0 else 0
        score = 1.0 - abs(actual_protein_ratio - target_protein_ratio)
        
        # Adjust for medical conditions
        if household_profiles:
            # Check for hypertension (need low sodium)
            has_hypertension = any(
                member.get("medical_conditions", {}).get("hypertension", False)
                for member in household_profiles.values()
                if isinstance(member, dict)
            )
            
            if has_hypertension:
                # Target sodium: < 1500mg per serving for hypertensive patients
                max_sodium = 1500.0
                if sodium > 0:
                    sodium_score = max(0.0, 1.0 - (sodium / max_sodium))
                    # Weight sodium heavily for hypertension
                    score = score * 0.5 + sodium_score * 0.5
        
        return max(0.0, min(1.0, score))

    def _normalize_cost_score(self, cost: float) -> float:
        """Normalize cost to 0-1 score (lower cost = higher score)."""
        # Assume reasonable cost per serving is 2-10 currency units
        max_reasonable_cost = 10.0
        score = 1.0 - (cost / max_reasonable_cost)
        return max(0.0, min(1.0, score))

    def _normalize_rating_score(self, rating: float) -> float:
        """Normalize Mealie rating to 0-1 score. 0 is neutral, 1-5 is progressive."""
        if rating <= 0:
            return 0.5  # Neutral score for unrated or 0-rated recipes
        # Normalize 1-5 to 0.5-1.0 (5 = 1.0, 1 = 0.5)
        return 0.5 + (rating / 10.0)

    def _extract_total_time(self, recipe_metadata: dict) -> float:
        """Extract total preparation time in minutes from recipe metadata."""
        # Try totalTime first, then prepTime + cookTime
        total_time = recipe_metadata.get("totalTime", 0)
        if total_time:
            # Parse ISO format "PT2H30M" or similar
            if isinstance(total_time, str) and total_time.startswith("PT"):
                hours = 0
                minutes = 0
                if "H" in total_time:
                    hours = int(total_time.split("H")[0].replace("PT", ""))
                if "M" in total_time:
                    minutes = int(total_time.split("M")[0].split("H")[-1])
                return hours * 60 + minutes
            elif isinstance(total_time, (int, float)):
                return float(total_time)
        
        # Fallback to prepTime + cookTime
        prep_time = recipe_metadata.get("prepTime", 0)
        cook_time = recipe_metadata.get("cookTime", 0)
        
        def parse_time(t):
            if isinstance(t, str) and t.startswith("PT"):
                hours = 0
                minutes = 0
                if "H" in t:
                    hours = int(t.split("H")[0].replace("PT", ""))
                if "M" in t:
                    minutes = int(t.split("M")[0].split("H")[-1])
                return hours * 60 + minutes
            elif isinstance(t, (int, float)):
                return float(t)
            return 0
        
        return parse_time(prep_time) + parse_time(cook_time)

    def _normalize_time_score(self, total_time_minutes: float) -> float:
        """Normalize time to 0-1 score. Penalize if > 2h (120 minutes)."""
        if total_time_minutes == 0:
            return 1.0  # Unknown time = neutral
        
        max_target_minutes = 120.0  # 2 hours
        if total_time_minutes <= max_target_minutes:
            return 1.0  # Within target = full score
        
        # Penalize progressively beyond 2h (minimum 0.2)
        excess = total_time_minutes - max_target_minutes
        penalty = min(0.8, excess / 120.0)  # Max penalty after 4 hours
        return max(0.2, 1.0 - penalty)

    def _get_current_season(self, d: date) -> str:
        """Return the current astronomical season name."""
        month = d.month
        if month in (3, 4, 5):
            return "spring"
        if month in (6, 7, 8):
            return "summer"
        if month in (9, 10, 11):
            return "autumn"
        return "winter"

    def _calculate_season_score(self, recipe_tags: list[str], current_date: Optional[date]) -> float:
        """
        Calculate season score using recipe tags from Mealie.

        Scoring:
        - Recipe has current season tag → 1.0 (perfect match)
        - Recipe has no season tag → 0.7 (neutral, no penalty)
        - Recipe has a different season tag → 0.1 (out-of-season penalty)
        """
        if not current_date:
            return 1.0

        current_season = self._get_current_season(current_date)
        season_slugs_for_current = set(self.config.season_tags.get(current_season, []))

        recipe_tag_set = {t.lower() for t in recipe_tags}

        if season_slugs_for_current & recipe_tag_set:
            return 1.0

        all_season_slugs = {s for slugs in self.config.season_tags.values() for s in slugs}
        if all_season_slugs & recipe_tag_set:
            return 0.1  # Tagged for a different season

        return 0.7  # No season tag = neutral

    def rank_recipes(
        self,
        recipe_slugs: list[str],
        menu_history: Optional[list[str]] = None,
        current_date: Optional[date] = None,
        limit: Optional[int] = None,
        recipe_metadata: Optional[dict[str, dict]] = None,
    ) -> list[tuple[str, float]]:
        """
        Rank recipes by combined score.
        
        Args:
            recipe_slugs: List of recipe slugs to rank
            menu_history: List of recipe slugs used in recent menus
            current_date: Current date (for seasonality)
            limit: Maximum number of recipes to return
            recipe_metadata: Recipe metadata dict with tags, rating, time
            
        Returns:
            List of (recipe_slug, score) tuples sorted by score descending
        """
        if not recipe_slugs:
            return []

        scored_recipes: list[tuple[str, float]] = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_slug: dict = {}
            for slug in recipe_slugs:
                metadata = recipe_metadata.get(slug, {}) if recipe_metadata else {}
                tags = metadata.get("tags", [])
                future = executor.submit(self.score_recipe, slug, menu_history, current_date, tags, metadata)
                future_to_slug[future] = slug
            for future in as_completed(future_to_slug):
                slug = future_to_slug[future]
                try:
                    scores = future.result()
                    scored_recipes.append((slug, scores["combined"]))
                except Exception as exc:
                    logger.warning("Failed to score recipe %s: %s", slug, exc)
                    scored_recipes.append((slug, 0.0))

        # Sort by score descending
        scored_recipes.sort(key=lambda x: x[1], reverse=True)

        if limit:
            scored_recipes = scored_recipes[:limit]

        return scored_recipes
