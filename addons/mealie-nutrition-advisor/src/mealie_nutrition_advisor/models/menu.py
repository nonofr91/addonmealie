"""Menu planning models."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .nutrition import NutritionFacts


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


class MealSlot(BaseModel):
    """Un repas dans le planning."""

    meal_type: MealType
    recipe_slug: str
    recipe_id: Optional[str] = None
    recipe_name: str
    servings: int = 1
    nutrition_per_serving: NutritionFacts = Field(default_factory=NutritionFacts)
    score: float = Field(0.0, ge=0.0, le=1.0, description="Score de compatibilité profil")
    notes: str = ""


class DayMenu(BaseModel):
    """Menu d'une journée."""

    date: date
    slots: list[MealSlot] = Field(default_factory=list)

    def total_nutrition(self) -> NutritionFacts:
        total = NutritionFacts()
        for slot in self.slots:
            total = total + slot.nutrition_per_serving.scale(float(slot.servings))
        return total

    def total_calories(self) -> float:
        return self.total_nutrition().calories_kcal


class WeekMenu(BaseModel):
    """Menu hebdomadaire."""

    week_label: str = Field(..., description="ex: 2026-W16")
    days: list[DayMenu] = Field(default_factory=list)
    member_names: list[str] = Field(default_factory=list, description="Membres ciblés")

    def average_daily_calories(self) -> float:
        if not self.days:
            return 0.0
        return round(sum(d.total_calories() for d in self.days) / len(self.days), 1)

    def to_mealie_mealplan_entries(self) -> list[dict]:
        """Formate pour l'API Mealie mealplan bulk."""
        entries = []
        for day in self.days:
            for slot in day.slots:
                entry = {
                    "date": day.date.isoformat(),
                    "entry_type": slot.meal_type.value,
                }
                if slot.recipe_id:
                    entry["recipe_id"] = slot.recipe_id
                else:
                    entry["title"] = slot.recipe_name
                entries.append(entry)
        return entries


class CompatibilityReport(BaseModel):
    """Rapport de compatibilité d'une recette avec un profil."""

    recipe_slug: str
    recipe_name: str
    member_name: str
    score: float = Field(0.0, ge=0.0, le=1.0)
    calories_per_serving: float = 0.0
    calorie_fit_pct: Optional[float] = None
    protein_fit_pct: Optional[float] = None
    blocked_by_allergy: bool = False
    blocked_by_restriction: bool = False
    blocking_reason: str = ""
    notes: list[str] = Field(default_factory=list)
