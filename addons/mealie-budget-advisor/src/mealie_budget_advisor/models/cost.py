"""Modèles pour le calcul des coûts de recettes."""

from typing import Any, Optional

from pydantic import BaseModel, Field, computed_field


class IngredientCost(BaseModel):
    """Coût d'un ingrédient dans une recette."""

    ingredient_name: str = Field(..., description="Nom normalisé de l'ingrédient")
    original_note: str = Field(..., description="Texte original de l'ingrédient dans la recette")
    quantity: float = Field(default=0.0, description="Quantité parsée")
    unit: str = Field(default="unit", description="Unité (g, kg, ml, l, cup, tbsp, tsp, unit)")
    price_per_unit: float = Field(default=0.0, description="Prix par unité de base (€)")
    total_cost: float = Field(default=0.0, description="Coût total pour cette quantité (€)")
    display_quantity: str = Field(default="", description="Quantité lisible en français")
    priced_quantity: str = Field(default="", description="Quantité réellement valorisée")
    pricing_detail: str = Field(default="", description="Détail lisible du calcul de prix")
    price_source: str = Field(
        default="unknown",
        description="Source du prix: open_prices | manual | estimated | unknown"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confiance dans l'estimation (0-1)"
    )
    product_name: Optional[str] = Field(
        default=None, description="Nom du produit matché (si trouvé)"
    )
    product_code: Optional[str] = Field(
        default=None, description="Code EAN du produit (si disponible)"
    )


class CostBreakdown(BaseModel):
    """Détail du coût d'une recette."""

    ingredients: list[IngredientCost] = Field(default_factory=list)

    @computed_field
    @property
    def total_known_cost(self) -> float:
        """Somme des coûts connus (exclut les unknown)."""
        return sum(
            ing.total_cost for ing in self.ingredients
            if ing.price_source != "unknown"
        )

    @computed_field
    @property
    def total_estimated_cost(self) -> float:
        """Somme de tous les coûts (avec estimations)."""
        return sum(ing.total_cost for ing in self.ingredients)

    @computed_field
    @property
    def num_known_prices(self) -> int:
        """Nombre d'ingrédients avec prix connu."""
        return sum(
            1 for ing in self.ingredients
            if ing.price_source != "unknown"
        )

    @computed_field
    @property
    def num_total_ingredients(self) -> int:
        """Nombre total d'ingrédients."""
        return len(self.ingredients)

    @computed_field
    @property
    def coverage_ratio(self) -> float:
        """Ratio d'ingrédients avec prix connu (0-1)."""
        if self.num_total_ingredients == 0:
            return 0.0
        return round(self.num_known_prices / self.num_total_ingredients, 2)


class RecipeCost(BaseModel):
    """Coût complet d'une recette."""

    recipe_slug: str = Field(..., description="Slug de la recette dans Mealie")
    recipe_name: str = Field(..., description="Nom de la recette")
    servings: int = Field(default=1, ge=1, description="Nombre de portions de la recette")

    breakdown: CostBreakdown = Field(default_factory=CostBreakdown)

    override_per_serving: Optional[float] = Field(
        default=None,
        description="Override manuel du coût par portion (lu depuis extras.cout_manuel_par_portion).",
    )
    override_total: Optional[float] = Field(
        default=None,
        description="Override manuel du coût total (lu depuis extras.cout_manuel_total).",
    )
    override_reason: Optional[str] = Field(
        default=None,
        description="Raison de l'override manuel (extras.cout_manuel_raison).",
    )

    @computed_field
    @property
    def computed_total_cost(self) -> float:
        """Coût total calculé (sans override)."""
        return self.breakdown.total_estimated_cost

    @computed_field
    @property
    def computed_cost_per_serving(self) -> float:
        """Coût par portion calculé (sans override)."""
        if self.servings == 0:
            return 0.0
        return round(self.computed_total_cost / self.servings, 2)

    @computed_field
    @property
    def total_cost(self) -> float:
        """Coût total effectif (override manuel prioritaire s'il existe)."""
        if self.override_total is not None:
            return round(self.override_total, 2)
        if self.override_per_serving is not None:
            return round(self.override_per_serving * max(self.servings, 1), 2)
        return self.computed_total_cost

    @computed_field
    @property
    def cost_per_serving(self) -> float:
        """Coût par portion effectif (override manuel prioritaire s'il existe)."""
        if self.override_per_serving is not None:
            return round(self.override_per_serving, 2)
        if self.override_total is not None and self.servings:
            return round(self.override_total / max(self.servings, 1), 2)
        return self.computed_cost_per_serving

    @computed_field
    @property
    def has_override(self) -> bool:
        """Vrai si un override manuel a été appliqué."""
        return self.override_per_serving is not None or self.override_total is not None

    @computed_field
    @property
    def confidence(self) -> float:
        """Confiance globale basée sur le coverage des prix (1.0 si override manuel)."""
        if self.has_override:
            return 1.0
        return self.breakdown.coverage_ratio

    @computed_field
    @property
    def price_sources_breakdown(self) -> dict[str, int]:
        """Répartition des sources de prix."""
        sources: dict[str, int] = {}
        for ing in self.breakdown.ingredients:
            src = ing.price_source
            sources[src] = sources.get(src, 0) + 1
        return sources
