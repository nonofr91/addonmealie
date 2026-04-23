"""Score recipes against a per-meal budget target."""

from __future__ import annotations

from dataclasses import dataclass

from ..models.budget import BudgetSettings
from ..models.cost import RecipeCost


@dataclass
class ScoredRecipe:
    cost: RecipeCost
    score: float  # higher is better
    within_budget: bool


class BudgetScorer:
    """Assign a "fit" score to a recipe for a given budget target."""

    def score(self, cost: RecipeCost, budget_per_meal: float) -> ScoredRecipe:
        """Return a score in [0, 1]. Recipes below target keep full score;
        recipes above target are penalized proportionally."""
        per_serving = cost.cost_per_serving
        if budget_per_meal <= 0 or per_serving <= 0:
            score = 0.5  # neutral when data missing
            return ScoredRecipe(cost=cost, score=score, within_budget=per_serving <= budget_per_meal)
        if per_serving <= budget_per_meal:
            # Cheaper recipes get a very small bonus so ordering stays sensible.
            head_room = max(budget_per_meal - per_serving, 0.0)
            score = 1.0 - 0.2 * (1.0 - min(head_room / budget_per_meal, 1.0))
            return ScoredRecipe(cost=cost, score=round(score, 3), within_budget=True)
        overage = (per_serving - budget_per_meal) / budget_per_meal
        score = max(0.0, 1.0 - overage)
        return ScoredRecipe(cost=cost, score=round(score, 3), within_budget=False)

    def score_many(self, costs: list[RecipeCost], settings: BudgetSettings) -> list[ScoredRecipe]:
        return [self.score(c, settings.budget_per_meal) for c in costs]
