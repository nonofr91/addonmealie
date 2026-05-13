"""Configuration for mealie-menu-orchestrator addon."""

from __future__ import annotations

import os
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class MenuOrchestratorConfig(BaseSettings):
    """Configuration for Menu Orchestrator addon."""

    # Mealie connection
    mealie_base_url: str = Field(default="http://localhost:9000", description="Mealie base URL")
    mealie_api_key: str = Field(default="", description="Mealie API key")

    # Nutrition Advisor connection
    nutrition_advisor_url: str = Field(
        default="http://localhost:8001", description="Nutrition Advisor API URL"
    )
    nutrition_advisor_key: Optional[str] = Field(
        default=None, description="Nutrition Advisor API key (if required)"
    )

    # Budget Advisor connection
    budget_advisor_url: str = Field(
        default="http://localhost:8003", description="Budget Advisor API URL"
    )
    budget_advisor_key: Optional[str] = Field(
        default=None, description="Budget Advisor API key (if required)"
    )

    # API server
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8004, description="API server port")
    api_url: Optional[str] = Field(default=None, description="Full API URL (overrides api_host:api_port if set)")
    addon_secret_key: Optional[str] = Field(
        default=None, description="Secret key for API authentication"
    )

    # Feature flags
    enable_menu_generation: bool = Field(default=True, description="Enable menu generation")
    enable_variety_tracking: bool = Field(default=True, description="Enable menu variety tracking")
    enable_seasonality: bool = Field(default=False, description="Enable seasonality filtering (requires season tags on recipes)")
    enable_course_filtering: bool = Field(default=False, description="Filter recipes by course type category (requires course categories on recipes)")

    # Scoring weights (default equal weights)
    weight_nutrition: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for nutrition score")
    weight_budget: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for budget score")
    weight_variety: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for variety score")
    weight_season: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for season score")

    # Default quantities for weekly menus
    default_weekly_quantities: dict = Field(
        default_factory=lambda: {
            "breakfast": 1,
            "lunch": 1,
            "dinner": 1,
        },
        description="Default quantities per meal type",
    )

    # Course type → Mealie category slugs mapping
    # Slugs are lowercased and compared case-insensitively
    course_categories: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "starter": ["entree", "entrée", "entrees", "entrées", "starter", "starters"],
            "main": ["plat-principal", "plat principal", "plats", "main", "main-course"],
            "dessert": ["dessert", "desserts"],
            "side": ["accompagnement", "accompagnements", "side", "sides"],
        },
        description="Mealie category slugs/names for each course type (case-insensitive)",
    )

    # Season → Mealie tag slugs mapping
    season_tags: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "spring": ["printemps", "spring"],
            "summer": ["ete", "été", "summer"],
            "autumn": ["automne", "autumn", "fall"],
            "winter": ["hiver", "winter"],
        },
        description="Mealie tag slugs/names for each season (case-insensitive)",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @field_validator("nutrition_advisor_url", "budget_advisor_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        """Remove trailing slash from URLs."""
        return v.rstrip("/")

    def to_dict(self) -> dict:
        """Convert config to dictionary (for UI display)."""
        return {
            "mealie_base_url": self.mealie_base_url,
            "nutrition_advisor_url": self.nutrition_advisor_url,
            "budget_advisor_url": self.budget_advisor_url,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "enable_menu_generation": self.enable_menu_generation,
            "enable_variety_tracking": self.enable_variety_tracking,
            "enable_seasonality": self.enable_seasonality,
            "weight_nutrition": self.weight_nutrition,
            "weight_budget": self.weight_budget,
            "weight_variety": self.weight_variety,
            "weight_season": self.weight_season,
        }
