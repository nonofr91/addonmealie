"""Tests for BudgetManager (JSON persistence)."""

from __future__ import annotations

from pathlib import Path

from mealie_budget_advisor.budget_manager import BudgetManager
from mealie_budget_advisor.models.budget import BudgetSettings


def _settings(month: str = "2026-04") -> BudgetSettings:
    return BudgetSettings(month=month, total_budget=500, condiments_forfait=20)


def test_roundtrip(tmp_path: Path) -> None:
    mgr = BudgetManager(tmp_path / "budget.json")
    mgr.set(_settings("2026-04"))

    fresh = BudgetManager(tmp_path / "budget.json")
    loaded = fresh.get("2026-04")
    assert loaded is not None
    assert loaded.total_budget == 500
    assert loaded.effective_budget == 480


def test_get_or_default_returns_default_for_missing(tmp_path: Path) -> None:
    mgr = BudgetManager(tmp_path / "budget.json")
    default = mgr.get_or_default("2099-12")
    assert default.month == "2099-12"
    assert default.total_budget == 0


def test_delete(tmp_path: Path) -> None:
    mgr = BudgetManager(tmp_path / "budget.json")
    mgr.set(_settings("2026-04"))
    assert mgr.delete("2026-04") is True
    assert mgr.get("2026-04") is None
    assert mgr.delete("2026-04") is False
