"""Tests for the ingredient parser."""

from __future__ import annotations

import pytest

from mealie_budget_advisor.pricing.ingredient_parser import parse_ingredient


class TestParseIngredient:
    def test_parses_grams(self):
        parsed = parse_ingredient("200g de poulet")
        assert parsed.quantity == pytest.approx(200.0)
        assert parsed.unit == "g"
        assert "poulet" in parsed.food_name

    def test_parses_kilograms(self):
        parsed = parse_ingredient("1.5 kg de boeuf")
        assert parsed.quantity == pytest.approx(1500.0)
        assert parsed.unit == "g"

    def test_parses_milliliters(self):
        parsed = parse_ingredient("250 ml de lait")
        assert parsed.quantity == pytest.approx(250.0)
        assert parsed.unit == "ml"

    def test_parses_liter(self):
        parsed = parse_ingredient("1 l d'eau")
        assert parsed.quantity == pytest.approx(1000.0)
        assert parsed.unit == "ml"

    def test_parses_tablespoon(self):
        parsed = parse_ingredient("2 cuillères à soupe d'huile")
        # 2 * 15 ml = 30 ml
        assert parsed.quantity == pytest.approx(30.0)
        assert parsed.unit == "ml"

    def test_count_with_default_weight(self):
        parsed = parse_ingredient("2 oignons")
        # Uses the per-item default weight.
        assert parsed.unit == "g"
        assert parsed.quantity > 0

    def test_fallback_unit(self):
        parsed = parse_ingredient("sel et poivre")
        assert parsed.unit in {"unit", "g"}

    def test_empty_text(self):
        parsed = parse_ingredient("")
        assert parsed.quantity == 0.0

    def test_comma_decimal(self):
        parsed = parse_ingredient("0,5 kg de riz")
        assert parsed.quantity == pytest.approx(500.0)
        assert parsed.unit == "g"
