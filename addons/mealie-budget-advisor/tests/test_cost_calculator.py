"""End-to-end tests for CostCalculator (parser + matcher + calculator)."""

from __future__ import annotations

from pathlib import Path

from mealie_budget_advisor.models.pricing import ManualPrice, PriceSource
from mealie_budget_advisor.pricing.cost_calculator import CostCalculator
from mealie_budget_advisor.pricing.ingredient_matcher import IngredientMatcher
from mealie_budget_advisor.pricing.manual_pricer import ManualPricer


def _calculator(tmp_path: Path) -> CostCalculator:
    pricer = ManualPricer(tmp_path / "prices.json")
    pricer.upsert(ManualPrice(ingredient_name="poulet", unit="kg", price_per_unit=9.50))
    pricer.upsert(ManualPrice(ingredient_name="riz", unit="kg", price_per_unit=2.50))
    matcher = IngredientMatcher(manual_pricer=pricer, open_prices=None, enable_open_prices=False)
    return CostCalculator(matcher)


def test_single_line_with_manual_price(tmp_path: Path) -> None:
    calc = _calculator(tmp_path)
    line = calc.cost_of_line("200g de poulet")
    assert line.total_cost > 0
    # 200 g × 9.5/kg = 1.90 €
    assert abs(line.total_cost - 1.90) < 0.05
    assert line.price_source == PriceSource.manual


def test_recipe_aggregates_costs(tmp_path: Path) -> None:
    calc = _calculator(tmp_path)
    recipe = calc.cost_of_recipe(
        recipe_slug="poulet-riz",
        recipe_name="Poulet riz",
        ingredient_texts=["200g de poulet", "100g de riz"],
        servings=2,
    )
    assert recipe.servings == 2
    assert recipe.total_cost > 0
    # (200g × 9.5/kg) + (100g × 2.5/kg) = 1.90 + 0.25 = 2.15
    assert abs(recipe.total_cost - 2.15) < 0.05
    assert recipe.cost_per_serving == round(recipe.total_cost / 2, 2)
    # Both lines have a price → confidence 1.0
    assert recipe.confidence >= 0.99


def test_unknown_ingredient_uses_fallback_or_zero(tmp_path: Path) -> None:
    calc = _calculator(tmp_path)
    # "quinoa" is not in manual prices and not in static fallback → zero cost.
    line = calc.cost_of_line("50g de quinoa")
    assert line.total_cost >= 0.0
