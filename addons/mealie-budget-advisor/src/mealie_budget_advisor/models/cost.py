"""Recipe and ingredient cost models."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from .pricing import PriceSource


class IngredientCost(BaseModel):
    """Estimated cost of a single ingredient line."""

    ingredient_name: str = Field(..., description="Nom normalisé")
    original_note: str = Field(..., description="Texte original de l'ingrédient")
    quantity: float = Field(..., ge=0, description="Quantité parsée")
    unit: str = Field("g", description="Unité de base (g, ml, unit)")
    price_per_unit: float = Field(0.0, ge=0, description="Prix par unité de base")
    total_cost: float = Field(0.0, ge=0, description="Coût total pour cette quantité")
    price_source: PriceSource = PriceSource.estimated


class RecipeCost(BaseModel):
    """Aggregated cost of a recipe."""

    recipe_slug: str
    recipe_name: str
    servings: int = Field(1, ge=1)
    total_cost: float = Field(0.0, ge=0)
    cost_per_serving: float = Field(0.0, ge=0)
    currency: str = "EUR"
    ingredient_breakdown: list[IngredientCost] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0, le=1, description="Fraction d'ingrédients avec prix résolu")
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CostBreakdown(BaseModel):
    """Report comparing total cost of a selection vs. a budget target."""

    total_cost: float = Field(0.0, ge=0)
    effective_budget: float = Field(0.0, ge=0)
    over_budget: bool = False
    delta: float = 0.0
    currency: str = "EUR"
    recipes: list[RecipeCost] = Field(default_factory=list)
