"""Nutrition data models."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class NutritionSource(str, Enum):
    open_food_facts = "open_food_facts"
    ai_estimate = "ai_estimate"
    manual = "manual"
    unknown = "unknown"


class NutritionFacts(BaseModel):
    """Valeurs nutritionnelles pour 100g ou par portion."""

    calories_kcal: float = Field(0.0, ge=0, description="Énergie en kcal")
    protein_g: float = Field(0.0, ge=0, description="Protéines en grammes")
    fat_g: float = Field(0.0, ge=0, description="Lipides totaux en grammes")
    saturated_fat_g: float = Field(0.0, ge=0, description="Acides gras saturés en grammes")
    carbohydrate_g: float = Field(0.0, ge=0, description="Glucides en grammes")
    sugar_g: float = Field(0.0, ge=0, description="Sucres en grammes")
    fiber_g: float = Field(0.0, ge=0, description="Fibres en grammes")
    sodium_mg: float = Field(0.0, ge=0, description="Sodium en milligrammes")
    source: NutritionSource = NutritionSource.unknown
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Score de confiance 0–1")

    def is_empty(self) -> bool:
        return self.calories_kcal == 0 and self.protein_g == 0 and self.fat_g == 0

    def scale(self, factor: float) -> "NutritionFacts":
        """Retourne une copie mise à l'échelle (ex: g consommés / 100)."""
        return NutritionFacts(
            calories_kcal=round(self.calories_kcal * factor, 2),
            protein_g=round(self.protein_g * factor, 2),
            fat_g=round(self.fat_g * factor, 2),
            saturated_fat_g=round(self.saturated_fat_g * factor, 2),
            carbohydrate_g=round(self.carbohydrate_g * factor, 2),
            sugar_g=round(self.sugar_g * factor, 2),
            fiber_g=round(self.fiber_g * factor, 2),
            sodium_mg=round(self.sodium_mg * factor, 2),
            source=self.source,
            confidence=self.confidence,
        )

    def __add__(self, other: "NutritionFacts") -> "NutritionFacts":
        return NutritionFacts(
            calories_kcal=round(self.calories_kcal + other.calories_kcal, 2),
            protein_g=round(self.protein_g + other.protein_g, 2),
            fat_g=round(self.fat_g + other.fat_g, 2),
            saturated_fat_g=round(self.saturated_fat_g + other.saturated_fat_g, 2),
            carbohydrate_g=round(self.carbohydrate_g + other.carbohydrate_g, 2),
            sugar_g=round(self.sugar_g + other.sugar_g, 2),
            fiber_g=round(self.fiber_g + other.fiber_g, 2),
            sodium_mg=round(self.sodium_mg + other.sodium_mg, 2),
            source=self.source if self.source == other.source else NutritionSource.unknown,
            confidence=round(min(self.confidence, other.confidence), 3),
        )


class IngredientNutrition(BaseModel):
    """Résultat nutritionnel pour un ingrédient d'une recette."""

    raw_text: str = Field(..., description="Texte original de l'ingrédient")
    food_name: str = Field("", description="Nom normalisé de l'aliment")
    quantity_g: float = Field(0.0, ge=0, description="Quantité estimée en grammes")
    nutrition_per_100g: NutritionFacts = Field(default_factory=NutritionFacts)
    nutrition_total: NutritionFacts = Field(default_factory=NutritionFacts)

    def compute_total(self) -> None:
        """Calcule nutrition_total à partir de nutrition_per_100g et quantity_g."""
        self.nutrition_total = self.nutrition_per_100g.scale(self.quantity_g / 100.0)


class RecipeNutritionResult(BaseModel):
    """Résultat nutritionnel complet d'une recette."""

    recipe_slug: str
    recipe_name: str
    servings: int = Field(1, ge=1)
    ingredients: list[IngredientNutrition] = Field(default_factory=list)
    total_recipe: NutritionFacts = Field(default_factory=NutritionFacts)
    per_serving: NutritionFacts = Field(default_factory=NutritionFacts)

    def compute(self) -> None:
        """Agrège les totaux depuis les ingrédients et divise par portions."""
        total = NutritionFacts()
        for ing in self.ingredients:
            ing.compute_total()
            total = total + ing.nutrition_total
        self.total_recipe = total
        factor = 1.0 / max(self.servings, 1)
        self.per_serving = total.scale(factor)

    def to_mealie_nutrition(self) -> dict:
        """Formate pour le champ `nutrition` de l'API Mealie."""
        ps = self.per_serving
        return {
            "calories": str(round(ps.calories_kcal)),
            "proteinContent": str(round(ps.protein_g, 1)),
            "fatContent": str(round(ps.fat_g, 1)),
            "carbohydrateContent": str(round(ps.carbohydrate_g, 1)),
            "fiberContent": str(round(ps.fiber_g, 1)),
            "sugarContent": str(round(ps.sugar_g, 1)),
            "saturatedFatContent": str(round(ps.saturated_fat_g, 1)),
            "sodiumContent": str(round(ps.sodium_mg)),
            "cholesterolContent": None,
            "transFatContent": None,
            "unsaturatedFatContent": None,
        }
