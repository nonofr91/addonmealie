"""Tests pour les modèles Pydantic."""

import pytest
from datetime import datetime

from mealie_budget_advisor.models.budget import BudgetPeriod, BudgetSettings
from mealie_budget_advisor.models.cost import CostBreakdown, IngredientCost, RecipeCost
from mealie_budget_advisor.models.pricing import ManualPrice, OpenPrice, PriceSource


class TestBudgetPeriod:
    """Tests pour BudgetPeriod."""

    def test_period_label(self):
        """Test génération du label de période."""
        period = BudgetPeriod(year=2026, month=4)
        assert period.period_label == "2026-04"

    def test_from_string(self):
        """Test parsing depuis string."""
        period = BudgetPeriod.from_string("2026-04")
        assert period.year == 2026
        assert period.month == 4

    def test_current(self):
        """Test période actuelle."""
        period = BudgetPeriod.current()
        assert 1 <= period.month <= 12
        assert period.year >= 2020


class TestBudgetSettings:
    """Tests pour BudgetSettings."""

    def test_effective_budget(self):
        """Test calcul du budget effectif."""
        budget = BudgetSettings(
            period=BudgetPeriod(year=2026, month=4),
            total_budget=500.0,
            condiments_forfait=20.0,
        )
        assert budget.effective_budget == 480.0

    def test_budget_per_meal(self):
        """Test calcul du budget par repas."""
        budget = BudgetSettings(
            period=BudgetPeriod(year=2026, month=4),
            total_budget=900.0,
            condiments_forfait=0.0,
            meals_per_day=3,
            days_per_month=30,
        )
        assert budget.budget_per_meal == 10.0

    def test_budget_per_day(self):
        """Test calcul du budget par jour."""
        budget = BudgetSettings(
            period=BudgetPeriod(year=2026, month=4),
            total_budget=600.0,
            condiments_forfait=0.0,
            meals_per_day=3,
            days_per_month=30,
        )
        assert budget.budget_per_day == 20.0


class TestIngredientCost:
    """Tests pour IngredientCost."""

    def test_ingredient_cost_creation(self):
        """Test création d'un coût d'ingrédient."""
        cost = IngredientCost(
            ingredient_name="farine",
            original_note="200g de farine",
            quantity=200.0,
            unit="g",
            price_per_unit=0.002,  # 2€/kg
            total_cost=0.40,
            price_source="manual",
            confidence=1.0,
        )
        assert cost.ingredient_name == "farine"
        assert cost.total_cost == 0.40
        assert cost.confidence == 1.0


class TestCostBreakdown:
    """Tests pour CostBreakdown."""

    def test_total_known_cost(self):
        """Test calcul du coût total connu."""
        breakdown = CostBreakdown(ingredients=[
            IngredientCost(
                ingredient_name="farine",
                original_note="200g de farine",
                quantity=200.0,
                unit="g",
                price_per_unit=0.002,
                total_cost=0.40,
                price_source="manual",
                confidence=1.0,
            ),
            IngredientCost(
                ingredient_name="sucre",
                original_note="100g de sucre",
                quantity=100.0,
                unit="g",
                price_per_unit=0.003,
                total_cost=0.30,
                price_source="open_prices",
                confidence=0.8,
            ),
            IngredientCost(
                ingredient_name="épices",
                original_note="épices",
                quantity=1.0,
                unit="unit",
                price_per_unit=0.0,
                total_cost=0.0,
                price_source="unknown",
                confidence=0.0,
            ),
        ])
        assert breakdown.total_known_cost == 0.70
        assert breakdown.total_estimated_cost == 0.70
        assert breakdown.num_known_prices == 2
        assert breakdown.num_total_ingredients == 3
        assert breakdown.coverage_ratio == 2.0 / 3.0


class TestRecipeCost:
    """Tests pour RecipeCost."""

    def test_recipe_cost_creation(self):
        """Test création d'un coût de recette."""
        breakdown = CostBreakdown(ingredients=[
            IngredientCost(
                ingredient_name="farine",
                original_note="200g de farine",
                quantity=200.0,
                unit="g",
                price_per_unit=0.002,
                total_cost=0.40,
                price_source="manual",
                confidence=1.0,
            ),
        ])

        cost = RecipeCost(
            recipe_slug="carbonara",
            recipe_name="Pâtes carbonara",
            servings=4,
            breakdown=breakdown,
        )
        assert cost.recipe_slug == "carbonara"
        assert cost.total_cost == 0.40
        assert cost.cost_per_serving == 0.10
        assert cost.confidence == 1.0


class TestManualPrice:
    """Tests pour ManualPrice."""

    def test_manual_price_creation(self):
        """Test création d'un prix manuel."""
        price = ManualPrice(
            ingredient_name="farine",
            price_per_unit=2.0,
            unit="kg",
            store="Carrefour",
            location="Paris",
        )
        assert price.ingredient_name == "farine"
        assert price.price_per_unit == 2.0
        assert price.unit == "kg"
        assert price.store == "Carrefour"


class TestOpenPrice:
    """Tests pour OpenPrice."""

    def test_open_price_creation(self):
        """Test création d'un prix Open Prices."""
        price = OpenPrice(
            product_name="Farine de blé T55",
            product_code="3254410166800",
            price=1.50,
            currency="EUR",
            quantity=1.0,
            unit="kg",
            store_name="Carrefour",
        )
        assert price.product_name == "Farine de blé T55"
        assert price.price == 1.50
        assert price.price_per_base_unit == 1.50

    def test_price_per_base_unit_conversion(self):
        """Test conversion prix par unité de base."""
        # 500g à 1€ = 2€/kg
        price = OpenPrice(
            product_name="Sucre",
            price=1.0,
            currency="EUR",
            quantity=500.0,
            unit="g",
        )
        assert price.price_per_base_unit == 2.0

        # 2l à 3€ = 1.5€/l
        price = OpenPrice(
            product_name="Lait",
            price=3.0,
            currency="EUR",
            quantity=2.0,
            unit="l",
        )
        assert price.price_per_base_unit == 1.5
