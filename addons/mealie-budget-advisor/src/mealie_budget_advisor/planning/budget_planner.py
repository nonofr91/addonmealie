"""Budget-aware menu planner: selects recipes whose aggregate cost stays under target."""

from __future__ import annotations

import logging
from typing import Optional

from ..models.budget import BudgetSettings
from ..models.cost import CostBreakdown, RecipeCost
from .budget_scorer import BudgetScorer, ScoredRecipe

logger = logging.getLogger(__name__)


class BudgetPlanner:
    """Greedy planner that fits recipes within a weekly / meal budget target.

    Algorithm:
      1. Cost every candidate recipe.
      2. Score each against the per-meal budget.
      3. Sort by (within_budget desc, score desc, cost_per_serving asc).
      4. Accumulate recipes while remaining budget allows it.
    """

    def __init__(self, scorer: Optional[BudgetScorer] = None) -> None:
        self.scorer = scorer or BudgetScorer()

    def plan(
        self,
        candidates: list[RecipeCost],
        settings: BudgetSettings,
        meals_target: int,
    ) -> CostBreakdown:
        if meals_target <= 0:
            meals_target = settings.meals_per_day * settings.days_per_month

        scored = self.scorer.score_many(candidates, settings)
        scored.sort(key=lambda s: (not s.within_budget, -s.score, s.cost.cost_per_serving))

        budget_target = min(settings.effective_budget, settings.budget_per_meal * meals_target)
        selection: list[RecipeCost] = []
        running_total = 0.0
        for entry in scored:
            per_serving = entry.cost.cost_per_serving
            if per_serving <= 0:
                continue
            if running_total + per_serving > budget_target and len(selection) >= 1:
                continue
            selection.append(entry.cost)
            running_total += per_serving
            if len(selection) >= meals_target:
                break

        delta = round(running_total - budget_target, 2)
        return CostBreakdown(
            total_cost=round(running_total, 2),
            effective_budget=round(budget_target, 2),
            over_budget=running_total > budget_target,
            delta=delta,
            currency=settings.currency,
            recipes=selection,
        )

    def cheaper_alternatives(
        self,
        chosen: RecipeCost,
        candidates: list[RecipeCost],
        limit: int = 5,
    ) -> list[ScoredRecipe]:
        """Suggest cheaper-than-chosen recipes, cheapest first."""
        target = chosen.cost_per_serving
        filtered = [c for c in candidates if 0 < c.cost_per_serving < target and c.recipe_slug != chosen.recipe_slug]
        filtered.sort(key=lambda c: c.cost_per_serving)
        return [
            ScoredRecipe(cost=c, score=round(1.0 - c.cost_per_serving / target, 3), within_budget=True)
            for c in filtered[:limit]
        ]
