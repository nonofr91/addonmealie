"""Tests for the budget planner."""

from __future__ import annotations

from mealie_budget_advisor.models.budget import BudgetSettings
from mealie_budget_advisor.models.cost import RecipeCost
from mealie_budget_advisor.planning.budget_planner import BudgetPlanner
from mealie_budget_advisor.planning.budget_scorer import BudgetScorer


def _mk(slug: str, per_serving: float) -> RecipeCost:
    return RecipeCost(
        recipe_slug=slug,
        recipe_name=slug,
        servings=1,
        total_cost=per_serving,
        cost_per_serving=per_serving,
    )


def test_scorer_rewards_cheaper_recipes_within_budget():
    scorer = BudgetScorer()
    cheap = scorer.score(_mk("a", 2.0), budget_per_meal=5.0)
    pricey = scorer.score(_mk("b", 6.0), budget_per_meal=5.0)
    assert cheap.within_budget is True
    assert pricey.within_budget is False
    assert cheap.score > pricey.score


def test_planner_respects_budget():
    settings = BudgetSettings(
        month="2026-04",
        total_budget=60,
        condiments_forfait=0,
        meals_per_day=3,
        days_per_month=10,
    )
    candidates = [_mk(f"r{i}", price) for i, price in enumerate([1.5, 2.0, 2.5, 3.0, 4.0, 8.0])]
    planner = BudgetPlanner()
    report = planner.plan(candidates, settings, meals_target=5)
    assert len(report.recipes) >= 1
    assert report.total_cost <= settings.effective_budget + 0.01


def test_cheaper_alternatives_ordered():
    chosen = _mk("x", 5.0)
    candidates = [_mk("a", 1.0), _mk("b", 3.0), _mk("c", 4.0), _mk("d", 6.0), _mk("x", 5.0)]
    planner = BudgetPlanner()
    alts = planner.cheaper_alternatives(chosen, candidates, limit=3)
    assert [a.cost.recipe_slug for a in alts] == ["a", "b", "c"]
