"""Planner budget-aware pour suggérer des alternatives respectant le budget."""

from __future__ import annotations

import logging
from typing import Optional

from mealie_budget_advisor.models.budget import BudgetSettings
from mealie_budget_advisor.models.cost import RecipeCost

logger = logging.getLogger(__name__)


class BudgetAwarePlanner:
    """Planner qui suggère des alternatives respectant le budget."""

    def __init__(self) -> None:
        """Initialise le planner budget-aware."""
        pass

    def suggest_cheaper_alternatives(
        self,
        current_cost: float,
        budget_per_meal: float,
        alternatives: list[RecipeCost],
        limit: int = 5,
    ) -> list[RecipeCost]:
        """Suggère des alternatives moins chères respectant le budget.

        Args:
            current_cost: Coût actuel de la recette
            budget_per_meal: Budget par repas
            alternatives: Liste des recettes alternatives
            limit: Nombre maximum de suggestions

        Returns:
            Liste des recettes alternatives respectant le budget
        """
        # Filtrer les recettes qui respectent le budget
        budget_friendly = [
            r for r in alternatives
            if r.cost_per_serving <= budget_per_meal
        ]

        # Trier par coût (croissant)
        budget_friendly.sort(key=lambda r: r.cost_per_serving)

        # Retourner les N moins chères
        return budget_friendly[:limit]

    def compare_recipe_to_budget(
        self,
        recipe_cost: RecipeCost,
        budget: BudgetSettings,
    ) -> dict:
        """Compare le coût d'une recette au budget.

        Args:
            recipe_cost: Coût de la recette
            budget: Configuration du budget

        Returns:
            Dictionnaire avec les métriques de comparaison
        """
        cost_per_serving = recipe_cost.cost_per_serving
        budget_per_meal = budget.budget_per_meal

        ratio = (cost_per_serving / budget_per_meal) * 100 if budget_per_meal > 0 else 0

        return {
            "recipe_cost": cost_per_serving,
            "budget_per_meal": budget_per_meal,
            "ratio_pct": round(ratio, 1),
            "within_budget": ratio <= 100,
            "over_budget": round(cost_per_serving - budget_per_meal, 2) if ratio > 100 else 0,
            "savings": round(budget_per_meal - cost_per_serving, 2) if ratio < 100 else 0,
        }

    def generate_cost_report(
        self,
        recipes: list[RecipeCost],
        budget: BudgetSettings,
    ) -> dict:
        """Génère un rapport coût vs budget pour plusieurs recettes.

        Args:
            recipes: Liste des coûts de recettes
            budget: Configuration du budget

        Returns:
            Rapport avec les métriques agrégées
        """
        total_cost = sum(r.total_cost for r in recipes)
        total_servings = sum(r.servings for r in recipes)
        avg_cost_per_serving = total_cost / total_servings if total_servings > 0 else 0

        budget_per_meal = budget.budget_per_meal
        total_budget = budget.effective_budget

        # Nombre de repas possibles avec le budget
        meals_possible = total_budget / avg_cost_per_serving if avg_cost_per_serving > 0 else 0

        # Recettes respectant le budget
        within_budget = [
            r for r in recipes
            if r.cost_per_serving <= budget_per_meal
        ]

        # Recettes dépassant le budget
        over_budget = [
            r for r in recipes
            if r.cost_per_serving > budget_per_meal
        ]

        return {
            "total_recipes": len(recipes),
            "total_cost": round(total_cost, 2),
            "total_servings": total_servings,
            "avg_cost_per_serving": round(avg_cost_per_serving, 2),
            "budget_per_meal": budget_per_meal,
            "total_budget": total_budget,
            "meals_possible": round(meals_possible),
            "within_budget_count": len(within_budget),
            "over_budget_count": len(over_budget),
            "within_budget_pct": round((len(within_budget) / len(recipes)) * 100, 1) if recipes else 0,
        }
