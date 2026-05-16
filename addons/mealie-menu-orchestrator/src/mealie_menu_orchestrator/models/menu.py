"""Pydantic models for menu planning."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MealType(str, Enum):
    """Types of meals in a day."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SIDE = "side"


class CourseType(str, Enum):
    """Types of courses within a meal."""
    STARTER = "starter"
    MAIN = "main"
    DESSERT = "dessert"
    SIDE = "side"


class MenuGenerationRequest(BaseModel):
    """Request for menu generation."""

    start_date: date = Field(description="Start date for the menu (YYYY-MM-DD)")
    end_date: date = Field(description="End date for the menu (YYYY-MM-DD)")
    household_id: Optional[str] = Field(default=None, description="Household ID for profiles")
    budget_limit: Optional[float] = Field(default=None, description="Budget limit in currency")
    default_household_size: int = Field(default=4, ge=1, description="Default number of people for meals")
    meal_quantity_overrides: Optional[dict[str, int]] = Field(
        default=None,
        description="Override meal quantities by key (e.g., '2026-01-01_dinner': 5)",
    )
    include_breakfast: bool = Field(default=False, description="Include breakfast in menu")
    include_lunch: bool = Field(default=True, description="Include lunch in menu")
    include_dinner: bool = Field(default=True, description="Include dinner in menu")
    meal_composition: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "breakfast": ["main"],
            "lunch": ["starter", "main", "dessert"],
            "dinner": ["starter", "main", "dessert"],
        },
        description=(
            "Courses to generate per meal type. "
            "Keys: breakfast/lunch/dinner. Values: list of starter/main/dessert/side. "
            "Example: {'dinner': ['starter', 'main', 'dessert']}"
        ),
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2026-01-01",
                "end_date": "2026-01-07",
                "budget_limit": 200.0,
                "default_household_size": 4,
                "meal_quantity_overrides": {"2026-01-01_dinner": 5},
                "include_breakfast": False,
                "include_lunch": True,
                "include_dinner": True,
                "meal_composition": {
                    "breakfast": ["main"],
                    "lunch": ["starter", "main", "dessert"],
                    "dinner": ["starter", "main", "dessert"],
                },
            }
        }


class MenuEntry(BaseModel):
    """A single menu entry (recipe for a specific meal on a specific date)."""

    date: date
    meal_type: MealType
    course_type: CourseType = Field(default=CourseType.MAIN, description="Course type within the meal")
    recipe_id: Optional[str] = None
    recipe_slug: Optional[str] = None
    recipe_name: Optional[str] = None
    quantity: int = Field(default=1, description="Number of servings/quantities")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-01-01",
                "meal_type": "dinner",
                "course_type": "main",
                "recipe_id": "uuid",
                "recipe_slug": "carbonara",
                "recipe_name": "Pasta Carbonara",
                "quantity": 2,
            }
        }


class Menu(BaseModel):
    """Complete menu for a date range."""

    id: Optional[str] = None
    start_date: date
    end_date: date
    entries: list[MenuEntry] = Field(default_factory=list)
    total_cost: Optional[float] = None
    total_nutrition: Optional[dict] = None
    scores: Optional[dict[str, float]] = None
    created_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2026-01-01",
                "end_date": "2026-01-07",
                "entries": [],
                "total_cost": 150.0,
                "scores": {"nutrition": 0.85, "budget": 0.9, "variety": 0.7, "season": 0.8},
            }
        }


class MenuQuantitiesUpdate(BaseModel):
    """Request to update quantities for a menu."""

    quantities: dict[str, int] = Field(
        description="Map of entry_id to quantity",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "quantities": {"entry-1": 2, "entry-2": 3},
            }
        }


class MenuPushRequest(BaseModel):
    """Request to push a menu to Mealie mealplan."""

    menu_id: str
