"""Tests unitaires pour ``recipe_extras`` (sérialisation + override manuel)."""

from datetime import datetime, timezone

from mealie_budget_advisor.models.cost import (
    CostBreakdown,
    IngredientCost,
    RecipeCost,
)
from mealie_budget_advisor.recipe_extras import (
    ADDON_KEYS,
    USER_KEYS,
    build_addon_extras,
    merge_extras,
    read_override,
)


def _make_cost(total: float = 2.15, servings: int = 2, confidence: float = 1.0) -> RecipeCost:
    # total/servings=1.075 → round to 1.08 in computed_cost_per_serving
    per_ing = total
    breakdown = CostBreakdown(
        ingredients=[
            IngredientCost(
                ingredient_name="poulet",
                original_note="200g de poulet",
                quantity=200.0,
                unit="g",
                price_per_unit=per_ing / 200.0,
                total_cost=per_ing,
                price_source="manual",
                confidence=confidence,
            )
        ]
    )
    return RecipeCost(
        recipe_slug="poulet-riz",
        recipe_name="Poulet riz",
        servings=servings,
        breakdown=breakdown,
    )


class TestBuildAddonExtras:
    def test_all_keys_are_french_addon_keys(self):
        cost = _make_cost()
        computed_at = datetime(2026, 4, 23, 12, 0, 0, tzinfo=timezone.utc)
        extras = build_addon_extras(cost, month="2026-04", computed_at=computed_at)

        assert set(extras.keys()) == ADDON_KEYS
        # Pas de clés utilisateur écrites par l'addon
        assert not (set(extras.keys()) & USER_KEYS)

    def test_values_are_strings(self):
        cost = _make_cost()
        extras = build_addon_extras(cost)
        assert all(isinstance(v, str) for v in extras.values())

    def test_numeric_formatting_2_decimals(self):
        cost = _make_cost(total=2.40, servings=2)
        extras = build_addon_extras(cost)
        assert extras["cout_total"] == "2.40"
        assert extras["cout_par_portion"] == "1.20"
        assert extras["cout_confiance"] == "1.00"

    def test_default_month_is_current(self):
        cost = _make_cost()
        extras = build_addon_extras(cost)
        month = extras["cout_mois_reference"]
        assert len(month) == 7 and month[4] == "-"

    def test_source_auto_by_default(self):
        cost = _make_cost()
        extras = build_addon_extras(cost)
        assert extras["cout_source"] == "auto"

    def test_source_manual(self):
        cost = _make_cost()
        extras = build_addon_extras(cost, source="manuel")
        assert extras["cout_source"] == "manuel"

    def test_computed_at_iso_z(self):
        cost = _make_cost()
        computed_at = datetime(2026, 4, 23, 12, 0, 0, tzinfo=timezone.utc)
        extras = build_addon_extras(cost, computed_at=computed_at)
        assert extras["cout_calcule_le"] == "2026-04-23T12:00:00Z"


class TestMergeExtras:
    def test_preserves_user_keys(self):
        existing = {
            "cout_manuel_par_portion": "1.50",
            "cout_manuel_raison": "promo leclerc",
        }
        new = build_addon_extras(_make_cost())
        merged = merge_extras(existing, new)
        assert merged["cout_manuel_par_portion"] == "1.50"
        assert merged["cout_manuel_raison"] == "promo leclerc"

    def test_preserves_foreign_keys(self):
        """Clés non préfixées ``cout_`` (d'autres addons) doivent être conservées."""
        existing = {"nutrition_calories": "250", "custom_tag": "vegan"}
        new = build_addon_extras(_make_cost())
        merged = merge_extras(existing, new)
        assert merged["nutrition_calories"] == "250"
        assert merged["custom_tag"] == "vegan"

    def test_overwrites_addon_keys(self):
        existing = {"cout_total": "99.99", "cout_devise": "USD"}
        new = build_addon_extras(_make_cost(total=2.15, servings=2))
        merged = merge_extras(existing, new)
        assert merged["cout_total"] == "2.15"
        assert merged["cout_devise"] == "EUR"

    def test_handles_none_existing(self):
        new = build_addon_extras(_make_cost())
        merged = merge_extras(None, new)
        assert merged["cout_total"] == new["cout_total"]

    def test_handles_empty_existing(self):
        new = build_addon_extras(_make_cost())
        merged = merge_extras({}, new)
        assert set(merged.keys()) == set(new.keys())


class TestReadOverride:
    def test_no_extras(self):
        assert not read_override(None).has_override
        assert not read_override({}).has_override

    def test_per_serving_only(self):
        ov = read_override({"cout_manuel_par_portion": "1.50"})
        assert ov.per_serving == 1.50
        assert ov.total is None
        assert ov.has_override

    def test_total_only(self):
        ov = read_override({"cout_manuel_total": "6.00"})
        assert ov.total == 6.00
        assert ov.per_serving is None
        assert ov.has_override

    def test_virgule_decimale(self):
        ov = read_override({"cout_manuel_par_portion": "1,07"})
        assert ov.per_serving == 1.07

    def test_ignores_invalid_values(self):
        ov = read_override({"cout_manuel_par_portion": "not-a-number"})
        assert ov.per_serving is None
        assert not ov.has_override

    def test_reason(self):
        ov = read_override({
            "cout_manuel_par_portion": "1.50",
            "cout_manuel_raison": "promo Carrefour",
        })
        assert ov.reason == "promo Carrefour"

    def test_empty_reason_is_none(self):
        ov = read_override({"cout_manuel_par_portion": "1.50", "cout_manuel_raison": "   "})
        assert ov.reason is None


class TestRecipeCostWithOverride:
    def test_override_per_serving_takes_priority(self):
        cost = RecipeCost(
            recipe_slug="r",
            recipe_name="r",
            servings=4,
            breakdown=CostBreakdown(),
            override_per_serving=1.25,
        )
        assert cost.cost_per_serving == 1.25
        assert cost.total_cost == 5.00
        assert cost.has_override is True
        assert cost.confidence == 1.0

    def test_override_total_derives_per_serving(self):
        cost = RecipeCost(
            recipe_slug="r",
            recipe_name="r",
            servings=4,
            breakdown=CostBreakdown(),
            override_total=8.00,
        )
        assert cost.total_cost == 8.00
        assert cost.cost_per_serving == 2.00
        assert cost.has_override is True
