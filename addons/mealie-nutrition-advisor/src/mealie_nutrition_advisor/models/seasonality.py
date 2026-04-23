"""Seasonality models for ingredient seasonal scoring."""

from __future__ import annotations

from enum import Enum
from typing import Optional
from datetime import date

from pydantic import BaseModel, Field


class IngredientSeason(str, Enum):
    """Seasons for ingredients."""
    spring = "spring"      # March-May
    summer = "summer"    # June-August
    autumn = "autumn"    # September-November
    winter = "winter"    # December-February
    all_year = "all_year"  # Available year-round


class SeasonalScore(BaseModel):
    """Seasonal score for an ingredient at a given date."""
    
    ingredient: str = Field(..., description="Normalized ingredient name")
    current_season: IngredientSeason = Field(..., description="Current season at reference date")
    ingredient_peak_seasons: list[IngredientSeason] = Field(default_factory=list, description="Seasons when ingredient is at peak")
    score: float = Field(0.5, ge=0.0, le=1.0, description="Seasonal score: 1.0=in season, 0.5=available, 0.2=out of season/import")
    is_peak: bool = Field(False, description="Whether ingredient is at peak season now")
    is_available: bool = Field(True, description="Whether ingredient is generally available")


class IngredientSeasonality(BaseModel):
    """Seasonality data for a single ingredient."""
    
    name: str = Field(..., description="Normalized ingredient name")
    name_fr: Optional[str] = Field(None, description="French name if different")
    peak_seasons: list[IngredientSeason] = Field(default_factory=list, description="Seasons when at peak quality/price")
    available_seasons: list[IngredientSeason] = Field(default_factory=list, description="Seasons when available but not peak")
    storage_friendly: bool = Field(False, description="Whether stores well out of season (potatoes, carrots...)")
    mostly_import: bool = Field(False, description="Whether mostly imported when not in season")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    def get_score_for_date(self, reference_date: Optional[date] = None) -> SeasonalScore:
        """Calculate seasonal score for a given date (default: today)."""
        ref = reference_date or date.today()
        current_season = _date_to_season(ref)
        
        if IngredientSeason.all_year in self.peak_seasons:
            return SeasonalScore(
                ingredient=self.name,
                current_season=current_season,
                ingredient_peak_seasons=self.peak_seasons,
                score=1.0,
                is_peak=True,
                is_available=True,
            )
        
        is_peak = current_season in self.peak_seasons
        is_available = is_peak or current_season in self.available_seasons
        
        if is_peak:
            score = 1.0
        elif is_available:
            score = 0.7 if self.storage_friendly else 0.5
        elif self.storage_friendly:
            score = 0.6  # Storage-friendly items still OK out of season
        elif self.mostly_import:
            score = 0.2  # Imported out of season
        else:
            score = 0.4  # Generally available with lower quality
        
        return SeasonalScore(
            ingredient=self.name,
            current_season=current_season,
            ingredient_peak_seasons=self.peak_seasons,
            score=score,
            is_peak=is_peak,
            is_available=is_available,
        )


class SeasonalCalendar(BaseModel):
    """Calendar of seasonal ingredients."""
    
    version: str = Field("1.0", description="Data version")
    last_updated: Optional[date] = Field(None, description="Last update date")
    ingredients: list[IngredientSeasonality] = Field(default_factory=list, description="Ingredient seasonality data")
    
    def get_ingredient(self, name: str) -> Optional[IngredientSeasonality]:
        """Get seasonality data for an ingredient by name (case-insensitive)."""
        name_lower = name.lower().strip()
        for ing in self.ingredients:
            if ing.name.lower() == name_lower or (ing.name_fr and ing.name_fr.lower() == name_lower):
                return ing
        return None
    
    def get_score(self, ingredient_name: str, reference_date: Optional[date] = None) -> SeasonalScore:
        """Get seasonal score for an ingredient (returns neutral score if not found)."""
        ing = self.get_ingredient(ingredient_name)
        if ing:
            return ing.get_score_for_date(reference_date)
        
        # Unknown ingredient: return neutral score
        ref = reference_date or date.today()
        return SeasonalScore(
            ingredient=ingredient_name,
            current_season=_date_to_season(ref),
            ingredient_peak_seasons=[],
            score=0.5,  # Neutral for unknown
            is_peak=False,
            is_available=True,
        )


def _date_to_season(d: date) -> IngredientSeason:
    """Convert date to season (Northern Hemisphere)."""
    month = d.month
    if month in [3, 4, 5]:
        return IngredientSeason.spring
    elif month in [6, 7, 8]:
        return IngredientSeason.summer
    elif month in [9, 10, 11]:
        return IngredientSeason.autumn
    else:  # 12, 1, 2
        return IngredientSeason.winter


def get_current_season(reference_date: Optional[date] = None) -> IngredientSeason:
    """Get current season (default: today)."""
    return _date_to_season(reference_date or date.today())
