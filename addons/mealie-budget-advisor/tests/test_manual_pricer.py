"""Tests for manual price storage."""

from __future__ import annotations

from pathlib import Path

from mealie_budget_advisor.models.pricing import ManualPrice
from mealie_budget_advisor.pricing.manual_pricer import ManualPricer


def test_upsert_and_get(tmp_path: Path) -> None:
    pricer = ManualPricer(tmp_path / "prices.json")
    pricer.upsert(ManualPrice(ingredient_name="Poulet", unit="kg", price_per_unit=9.5))
    loaded = pricer.get("poulet")
    assert loaded is not None
    assert loaded.price_per_unit == 9.5
    # Case-insensitive lookup
    assert pricer.get("POULET") is not None


def test_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "prices.json"
    ManualPricer(path).upsert(ManualPrice(ingredient_name="riz", unit="kg", price_per_unit=2.5))
    fresh = ManualPricer(path)
    assert fresh.get("riz").price_per_unit == 2.5


def test_delete(tmp_path: Path) -> None:
    pricer = ManualPricer(tmp_path / "prices.json")
    pricer.upsert(ManualPrice(ingredient_name="riz", unit="kg", price_per_unit=2.5))
    assert pricer.delete("riz") is True
    assert pricer.get("riz") is None
    assert pricer.delete("riz") is False


def test_list_is_sorted(tmp_path: Path) -> None:
    pricer = ManualPricer(tmp_path / "prices.json")
    pricer.upsert(ManualPrice(ingredient_name="tomate", unit="kg", price_per_unit=3.0))
    pricer.upsert(ManualPrice(ingredient_name="carotte", unit="kg", price_per_unit=1.5))
    names = [p.ingredient_name for p in pricer.list()]
    assert names == ["carotte", "tomate"]
