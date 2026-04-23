"""Tests for budget / pricing / cost models."""

from __future__ import annotations

import pytest

from mealie_budget_advisor.models.budget import BudgetPeriod, BudgetSettings
from mealie_budget_advisor.models.cost import IngredientCost, RecipeCost
from mealie_budget_advisor.models.pricing import ManualPrice, PriceSource


class TestBudgetSettings:
    def test_effective_budget_subtracts_forfait(self):
        s = BudgetSettings(month="2026-04", total_budget=400, condiments_forfait=20)
        assert s.effective_budget == pytest.approx(380.0)

    def test_budget_per_meal(self):
        s = BudgetSettings(
            month="2026-04",
            total_budget=400,
            condiments_forfait=20,
            meals_per_day=3,
            days_per_month=30,
        )
        # 380 / (3*30) = 4.22..
        assert s.budget_per_meal == pytest.approx(380 / 90)

    def test_budget_per_day(self):
        s = BudgetSettings(month="2026-04", total_budget=400, condiments_forfait=20, days_per_month=30)
        assert s.budget_per_day == pytest.approx(380 / 30)

    def test_days_per_month_boundaries(self):
        # Allow partial-month planning (1..31)
        s = BudgetSettings(month="2026-04", total_budget=100, condiments_forfait=0, days_per_month=7)
        assert s.days_per_month == 7

    def test_rejects_invalid_month(self):
        with pytest.raises(Exception):
            BudgetSettings(month="2026-4", total_budget=100)

    def test_forfait_cannot_exceed_total(self):
        with pytest.raises(Exception):
            BudgetSettings(month="2026-04", total_budget=10, condiments_forfait=20)

    def test_currency_upper(self):
        s = BudgetSettings(month="2026-04", total_budget=100, currency="eur")
        assert s.currency == "EUR"

    def test_to_period(self):
        s = BudgetSettings(month="2026-04", total_budget=100, condiments_forfait=10)
        period = s.to_period()
        assert isinstance(period, BudgetPeriod)
        assert period.effective_budget == pytest.approx(90.0)


class TestManualPrice:
    def test_defaults(self):
        p = ManualPrice(ingredient_name="poulet", unit="kg", price_per_unit=9.50)
        assert p.source == PriceSource.manual
        assert p.currency == "EUR"


class TestRecipeCost:
    def test_zero_cost_by_default(self):
        cost = RecipeCost(recipe_slug="x", recipe_name="x")
        assert cost.total_cost == 0
        assert cost.servings == 1

    def test_ingredient_cost_fields(self):
        line = IngredientCost(
            ingredient_name="poulet",
            original_note="200g de poulet",
            quantity=200.0,
            unit="g",
            price_per_unit=0.01,
            total_cost=2.0,
            price_source=PriceSource.manual,
        )
        assert line.total_cost == pytest.approx(2.0)
