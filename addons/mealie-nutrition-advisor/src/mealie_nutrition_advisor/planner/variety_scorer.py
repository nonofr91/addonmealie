"""Variety scorer combining anti-boredom and seasonality scoring."""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from ..models.menu import MealType
from ..models.seasonality import IngredientSeasonality, SeasonalCalendar, get_current_season
from .history_tracker import HistoryTracker, VarietyMetrics

logger = logging.getLogger(__name__)

# Default weights for composite scoring
DEFAULT_NUTRITION_WEIGHT = 0.40
DEFAULT_VARIETY_WEIGHT = 0.30
DEFAULT_SEASONALITY_WEIGHT = 0.30

# Seasonality calendar path
SEASONAL_CALENDAR_PATH = Path(__file__).parent.parent.parent.parent / "config" / "seasonal_calendar.json"


class VarietyScoreResult:
    """Result of variety scoring for a recipe."""
    
    def __init__(
        self,
        recipe_slug: str,
        recipe_name: str,
        variety_score: float,
        seasonality_score: float,
        recency_score: float,
        family_penalty: float,
        days_since_last_used: Optional[int],
        seasonal_ingredients: list[dict],
        recipe_family: Optional[str],
    ) -> None:
        self.recipe_slug = recipe_slug
        self.recipe_name = recipe_name
        self.variety_score = variety_score  # 0-1 composite
        self.seasonality_score = seasonality_score  # 0-1
        self.recency_score = recency_score  # 0-1
        self.family_penalty = family_penalty  # 0-1 (1 = no penalty)
        self.days_since_last_used = days_since_last_used
        self.seasonal_ingredients = seasonal_ingredients
        self.recipe_family = recipe_family
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "recipe_slug": self.recipe_slug,
            "recipe_name": self.recipe_name,
            "variety_score": round(self.variety_score, 3),
            "seasonality_score": round(self.seasonality_score, 3),
            "recency_score": round(self.recency_score, 3),
            "family_penalty": round(self.family_penalty, 3),
            "days_since_last_used": self.days_since_last_used,
            "seasonal_ingredients": self.seasonal_ingredients,
            "recipe_family": self.recipe_family,
        }


class VarietyScorer:
    """Scores recipes for variety (anti-boredom) and seasonality.
    
    Combines:
    - Recency penalty (recently used = lower score)
    - Family penalty (similar recipes recently = lower score)
    - Seasonality bonus (in-season ingredients = higher score)
    """
    
    def __init__(
        self,
        history_tracker: Optional[HistoryTracker] = None,
        seasonal_calendar: Optional[SeasonalCalendar] = None,
        nutrition_weight: float = DEFAULT_NUTRITION_WEIGHT,
        variety_weight: float = DEFAULT_VARIETY_WEIGHT,
        seasonality_weight: float = DEFAULT_SEASONALITY_WEIGHT,
    ) -> None:
        self.history = history_tracker or HistoryTracker()
        self.calendar = seasonal_calendar or self._load_seasonal_calendar()
        
        # Normalize weights to sum to 1.0
        total = nutrition_weight + variety_weight + seasonality_weight
        self.nutrition_weight = nutrition_weight / total
        self.variety_weight = variety_weight / total
        self.seasonality_weight = seasonality_weight / total
        
        self._variety_metrics: Optional[VarietyMetrics] = None
    
    def _load_seasonal_calendar(self) -> SeasonalCalendar:
        """Load seasonal calendar from config file."""
        try:
            if SEASONAL_CALENDAR_PATH.exists():
                data = json.loads(SEASONAL_CALENDAR_PATH.read_text(encoding="utf-8"))
                calendar = SeasonalCalendar.model_validate(data)
                logger.info("Loaded seasonal calendar with %d ingredients", len(calendar.ingredients))
                return calendar
        except Exception as exc:
            logger.warning("Failed to load seasonal calendar: %s", exc)
        
        # Return empty calendar if loading fails
        return SeasonalCalendar(version="1.0", ingredients=[])
    
    def refresh_metrics(self) -> None:
        """Refresh variety metrics from Mealie history."""
        self._variety_metrics = self.history.compute_variety_metrics()
        logger.debug("Variety metrics refreshed")
    
    def _get_recipe_family(self, recipe_name: str, recipe_slug: str) -> Optional[str]:
        """Determine recipe family from name or slug."""
        from .history_tracker import RECIPE_FAMILIES
        
        text = f"{recipe_name} {recipe_slug}".lower()
        
        for family, keywords in RECIPE_FAMILIES.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return family
        
        return None
    
    def _extract_ingredients(self, recipe: dict) -> list[str]:
        """Extract ingredient names from recipe."""
        ingredients = recipe.get("recipeIngredient", [])
        names: list[str] = []
        
        for ing in ingredients:
            if isinstance(ing, dict):
                # Try to get food name if available
                food = ing.get("food")
                if food and isinstance(food, dict):
                    food_name = food.get("name", "")
                    if food_name:
                        names.append(food_name.lower())
                
                # Fallback to note or display
                note = ing.get("note", "").lower()
                if note:
                    # Extract simple ingredient name from note
                    # e.g., "500g de carottes" -> "carottes"
                    words = note.replace("de ", "").replace("d'", "").replace("du ", "").split()
                    if words:
                        names.append(words[-1])
            elif isinstance(ing, str):
                names.append(ing.lower())
        
        return names
    
    def score_recency(
        self,
        recipe_slug: str,
        recipe_name: str,
    ) -> tuple[float, Optional[int]]:
        """Score recency (anti-repetition).
        
        Returns:
            Tuple of (score 0-1, days since last used or None)
        """
        days_since = self.history.days_since_last_used(recipe_slug)
        
        if days_since is None:
            # Never used - perfect score
            return 1.0, None
        
        # Score based on days since last use
        # 0-7 days: 0.0-0.2 (penalty)
        # 8-14 days: 0.3-0.5
        # 15-21 days: 0.6-0.8
        # 22+ days: 0.9-1.0
        
        if days_since <= 7:
            score = 0.0 + (days_since / 7) * 0.2
        elif days_since <= 14:
            score = 0.3 + ((days_since - 7) / 7) * 0.2
        elif days_since <= 21:
            score = 0.6 + ((days_since - 14) / 7) * 0.2
        elif days_since <= 28:
            score = 0.8 + ((days_since - 21) / 7) * 0.1
        else:
            score = 1.0
        
        return round(score, 3), days_since
    
    def score_family_penalty(
        self,
        recipe_name: str,
        recipe_slug: str,
    ) -> float:
        """Score family penalty (avoid similar recipes).
        
        Returns:
            Score 0-1 where 1 = no penalty, 0 = max penalty
        """
        if self._variety_metrics is None:
            self.refresh_metrics()
        
        family = self._get_recipe_family(recipe_name, recipe_slug)
        if family is None:
            return 1.0  # No family = no penalty
        
        # Check recent family usage
        count_7d = self._variety_metrics.get_family_usage_count(family, days=7)
        count_14d = self._variety_metrics.get_family_usage_count(family, days=14)
        
        # Penalty calculation
        # 0 uses in 7 days: no penalty
        # 1 use: slight penalty
        # 2+ uses: increasing penalty
        if count_7d == 0:
            if count_14d == 0:
                return 1.0  # No recent usage
            else:
                return 0.8  # Used 8-14 days ago
        elif count_7d == 1:
            return 0.5  # Used once this week
        elif count_7d == 2:
            return 0.2  # Used twice this week
        else:
            return 0.0  # Used 3+ times this week
    
    def score_seasonality(
        self,
        recipe: dict,
        reference_date: Optional[date] = None,
    ) -> tuple[float, list[dict]]:
        """Score seasonality of ingredients.
        
        Returns:
            Tuple of (score 0-1, list of seasonal ingredient details)
        """
        ingredients = self._extract_ingredients(recipe)
        
        if not ingredients:
            return 0.5, []  # Neutral score if no ingredients
        
        scores = []
        seasonal_details = []
        
        for ing_name in ingredients:
            score_info = self.calendar.get_score(ing_name, reference_date)
            scores.append(score_info.score)
            
            if score_info.score != 0.5:  # Only include if we have specific data
                seasonal_details.append({
                    "ingredient": ing_name,
                    "score": round(score_info.score, 2),
                    "is_peak": score_info.is_peak,
                    "is_available": score_info.is_available,
                    "current_season": score_info.current_season.value,
                })
        
        # Average score
        avg_score = sum(scores) / len(scores) if scores else 0.5
        
        return round(avg_score, 3), seasonal_details
    
    def score(
        self,
        recipe: dict,
        nutrition_score: float = 0.7,  # Pre-computed nutrition score
        meal_type: MealType = MealType.dinner,
        reference_date: Optional[date] = None,
    ) -> VarietyScoreResult:
        """Calculate complete variety score for a recipe.
        
        Args:
            recipe: Recipe dict from Mealie API
            nutrition_score: Pre-computed nutrition compatibility score (0-1)
            meal_type: Type of meal
            reference_date: Date for seasonality calculation (default: today)
            
        Returns:
            VarietyScoreResult with all scoring details.
        """
        slug = recipe.get("slug", "")
        name = recipe.get("name", slug)
        
        # Ensure metrics are fresh
        if self._variety_metrics is None:
            self.refresh_metrics()
        
        # Calculate component scores
        recency_score, days_since = self.score_recency(slug, name)
        family_penalty = self.score_family_penalty(name, slug)
        seasonality_score, seasonal_ingredients = self.score_seasonality(recipe, reference_date)
        
        # Calculate composite variety score
        # Variety = recency * family_penalty (both contribute to variety)
        # Then blend with seasonality
        variety_component = (recency_score * 0.6 + family_penalty * 0.4)
        variety_score = (variety_component * 0.6 + seasonality_score * 0.4)
        
        # Get recipe family
        recipe_family = self._get_recipe_family(name, slug)
        
        result = VarietyScoreResult(
            recipe_slug=slug,
            recipe_name=name,
            variety_score=round(variety_score, 3),
            seasonality_score=seasonality_score,
            recency_score=recency_score,
            family_penalty=family_penalty,
            days_since_last_used=days_since,
            seasonal_ingredients=seasonal_ingredients,
            recipe_family=recipe_family,
        )
        
        logger.debug(
            "Variety score for %s: %.3f (recency: %.3f, family: %.3f, season: %.3f)",
            name, variety_score, recency_score, family_penalty, seasonality_score
        )
        
        return result
    
    def score_with_nutrition(
        self,
        recipe: dict,
        nutrition_score: float,
        meal_type: MealType = MealType.dinner,
        reference_date: Optional[date] = None,
    ) -> tuple[float, dict]:
        """Calculate combined score with nutrition, variety, and seasonality.
        
        Args:
            recipe: Recipe dict
            nutrition_score: Nutrition compatibility score (0-1)
            meal_type: Type of meal
            reference_date: Date reference
            
        Returns:
            Tuple of (composite_score 0-1, score_breakdown dict)
        """
        variety_result = self.score(recipe, nutrition_score, meal_type, reference_date)
        
        # Composite score
        composite = (
            self.nutrition_weight * nutrition_score +
            self.variety_weight * variety_result.variety_score +
            self.seasonality_weight * variety_result.seasonality_score
        )
        
        breakdown = {
            "nutrition": round(nutrition_score, 3),
            "variety": round(variety_result.variety_score, 3),
            "seasonality": round(variety_result.seasonality_score, 3),
            "composite": round(composite, 3),
            "nutrition_weight": round(self.nutrition_weight, 2),
            "variety_weight": round(self.variety_weight, 2),
            "seasonality_weight": round(self.seasonality_weight, 2),
        }
        
        return round(composite, 3), breakdown
    
    def get_season_info(self) -> dict:
        """Get current season information."""
        current = get_current_season()
        return {
            "current_season": current.value,
            "calendar_version": self.calendar.version,
            "calendar_ingredients_count": len(self.calendar.ingredients),
        }
    
    def close(self) -> None:
        """Close resources."""
        self.history.close()
    
    def __enter__(self) -> "VarietyScorer":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
