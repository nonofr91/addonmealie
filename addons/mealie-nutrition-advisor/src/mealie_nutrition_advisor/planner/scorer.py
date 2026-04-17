"""Score recipe compatibility with a member profile."""

from __future__ import annotations

import math

from ..models.menu import CompatibilityReport, MealType
from ..models.nutrition import NutritionFacts
from ..models.profile import MemberProfile


def _parse_mealie_nutrition(recipe: dict) -> NutritionFacts:
    """Extrait les NutritionFacts depuis le dict Mealie (champ 'nutrition')."""
    n = recipe.get("nutrition") or {}

    def _float(raw) -> float:
        if raw is None:
            return 0.0
        try:
            return float(str(raw).replace("g", "").replace("mg", "").replace("kcal", "").strip())
        except (ValueError, TypeError):
            return 0.0

    return NutritionFacts(
        calories_kcal=_float(n.get("calories")),
        protein_g=_float(n.get("proteinContent")),
        fat_g=_float(n.get("fatContent")),
        saturated_fat_g=_float(n.get("saturatedFatContent")),
        carbohydrate_g=_float(n.get("carbohydrateContent")),
        sugar_g=_float(n.get("sugarContent")),
        fiber_g=_float(n.get("fiberContent")),
        sodium_mg=_float(n.get("sodiumContent")),
    )


def _score_calories(actual_kcal: float, target_meal_kcal: float) -> float:
    """Score 0–1 : 1 si l'écart est < 10%, décroit exponentiellement."""
    if target_meal_kcal <= 0:
        return 0.5
    ratio = actual_kcal / target_meal_kcal
    return math.exp(-2 * (ratio - 1) ** 2)


def _score_protein(actual_g: float, target_g: float) -> float:
    """Score 0–1 : récompense le respect de l'objectif protéines."""
    if target_g <= 0:
        return 0.5
    ratio = actual_g / target_g
    if ratio >= 1.0:
        return 1.0
    return ratio


class RecipeScorer:
    """Calcule un score de compatibilité recette ↔ profil pour un repas donné."""

    def score(
        self,
        recipe: dict,
        member: MemberProfile,
        meal_type: MealType = MealType.dinner,
    ) -> CompatibilityReport:
        """
        Score de 0 à 1 :
        - 0.5 pondération calories
        - 0.3 pondération protéines
        - 0.2 bonus fibres / pénalité sodium
        """
        slug = recipe.get("slug", "")
        name = recipe.get("name", slug)
        servings_raw = recipe.get("recipeServings") or 1
        try:
            servings = max(int(float(servings_raw)), 1)
        except (ValueError, TypeError):
            servings = 1

        nutrition_total = _parse_mealie_nutrition(recipe)
        if nutrition_total.is_empty():
            return CompatibilityReport(
                recipe_slug=slug,
                recipe_name=name,
                member_name=member.name,
                score=0.0,
                calories_per_serving=0.0,
                notes=["Nutrition non calculée pour cette recette"],
            )

        per_serving = nutrition_total.scale(1.0 / servings)
        target_cal = member.target_calories()

        meal_cal_fractions = {
            MealType.breakfast: 0.25,
            MealType.lunch: 0.35,
            MealType.dinner: 0.35,
            MealType.snack: 0.05,
        }
        meal_target_kcal = target_cal * meal_cal_fractions.get(meal_type, 0.35)
        meal_protein_target = member.recommended_protein_g() * meal_cal_fractions.get(meal_type, 0.35)

        cal_score = _score_calories(per_serving.calories_kcal, meal_target_kcal)
        protein_score = _score_protein(per_serving.protein_g, meal_protein_target)

        fiber_bonus = min(per_serving.fiber_g / 8.0, 1.0) * 0.1
        sodium_penalty = min(per_serving.sodium_mg / 800.0, 1.0) * 0.1

        score = round(0.5 * cal_score + 0.3 * protein_score + fiber_bonus - sodium_penalty, 3)
        score = max(0.0, min(1.0, score))

        cal_fit_pct = round((per_serving.calories_kcal / meal_target_kcal) * 100, 1) if meal_target_kcal else None
        protein_fit_pct = round((per_serving.protein_g / meal_protein_target) * 100, 1) if meal_protein_target else None

        notes = []
        if per_serving.calories_kcal > meal_target_kcal * 1.3:
            notes.append(f"Trop calorique pour ce repas ({round(per_serving.calories_kcal)} kcal vs cible {round(meal_target_kcal)})")
        if per_serving.protein_g < meal_protein_target * 0.5:
            notes.append(f"Faible en protéines ({round(per_serving.protein_g)}g vs cible {round(meal_protein_target)}g)")

        return CompatibilityReport(
            recipe_slug=slug,
            recipe_name=name,
            member_name=member.name,
            score=score,
            calories_per_serving=per_serving.calories_kcal,
            calorie_fit_pct=cal_fit_pct,
            protein_fit_pct=protein_fit_pct,
            notes=notes,
        )

    def score_for_household(self, recipe: dict, members: list[MemberProfile], meal_type: MealType) -> float:
        """Score moyen pour l'ensemble du foyer."""
        if not members:
            return 0.0
        scores = [self.score(recipe, m, meal_type).score for m in members]
        return round(sum(scores) / len(scores), 3)
