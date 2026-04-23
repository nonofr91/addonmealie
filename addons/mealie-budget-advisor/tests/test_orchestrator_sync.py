"""Intégration orchestrator ↔ MealieClient pour la synchro des coûts."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from mealie_budget_advisor import mealie_sync as mealie_sync_module
from mealie_budget_advisor.config import BudgetConfig
from mealie_budget_advisor.models.pricing import ManualPrice
from mealie_budget_advisor.orchestrator import BudgetOrchestrator
from mealie_budget_advisor.recipe_extras import (
    KEY_MANUEL_PAR_PORTION,
    KEY_MANUEL_RAISON,
    KEY_PAR_PORTION,
    KEY_SOURCE,
    KEY_TOTAL,
)


# ----------------------------------------------------------------- Mealie mock


class _MockMealieClient:
    """Remplace ``MealieClient`` en mémoire pour les tests."""

    _RECIPES: dict = {}
    patch_log: list[tuple[str, dict]] = []

    def __init__(self, base_url: str, api_key: str) -> None:  # noqa: D401
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def close(self):
        return None

    def get_recipe(self, slug: str):
        return _MockMealieClient._RECIPES.get(slug)

    def get_all_recipes(self):
        return list(_MockMealieClient._RECIPES.values())

    def patch_extras(self, slug: str, extras: dict) -> bool:
        _MockMealieClient.patch_log.append((slug, dict(extras)))
        _MockMealieClient._RECIPES[slug]["extras"] = dict(extras)
        return True

    @staticmethod
    def extract_ingredient_texts(recipe: dict) -> list[str]:
        return list(recipe.get("recipeIngredient", []))

    @staticmethod
    def servings(recipe: dict) -> int:
        return int(recipe.get("recipeServings", 1) or 1)


@pytest.fixture
def orchestrator(tmp_path: Path, monkeypatch):
    """Orchestrator isolé (fichiers prix en tmp_path, Mealie mocké)."""
    os.environ["MEALIE_BASE_URL"] = "http://fake"
    os.environ["MEALIE_API_KEY"] = "fake-key"

    config = BudgetConfig.load()
    # Rediriger les dossiers data/config vers tmp
    config._data_dir = tmp_path / "data"
    config._config_dir = tmp_path / "config"
    config._data_dir.mkdir(parents=True, exist_ok=True)
    config._config_dir.mkdir(parents=True, exist_ok=True)
    config._enable_open_prices = False

    # Patch du MealieClient dans les modules qui l'utilisent
    monkeypatch.setattr(mealie_sync_module, "MealieClient", _MockMealieClient)
    from mealie_budget_advisor import orchestrator as orch_module
    monkeypatch.setattr(orch_module, "MealieClient", _MockMealieClient)

    _MockMealieClient._RECIPES = {}
    _MockMealieClient.patch_log = []

    orch = BudgetOrchestrator(config=config)
    orch.manual_pricer.upsert(ManualPrice(ingredient_name="poulet", unit="kg", price_per_unit=9.50))
    orch.manual_pricer.upsert(ManualPrice(ingredient_name="riz", unit="kg", price_per_unit=2.50))
    return orch


# ----------------------------------------------------------------- tests


def test_sync_recipe_cost_ecrit_cout_par_portion_dans_extras(orchestrator):
    _MockMealieClient._RECIPES["poulet-riz"] = {
        "slug": "poulet-riz",
        "name": "Poulet riz",
        "recipeServings": 2,
        "recipeIngredient": ["200g de poulet", "100g de riz"],
        "extras": {"nutrition_calories": "450"},
    }

    result = orchestrator.sync_recipe_cost("poulet-riz", month="2026-04")

    assert result["written"] is True
    assert result["month"] == "2026-04"

    # Un patch a bien été envoyé
    assert len(_MockMealieClient.patch_log) == 1
    slug, extras = _MockMealieClient.patch_log[0]
    assert slug == "poulet-riz"

    # Clés addon présentes, valeurs correctes
    assert extras[KEY_TOTAL] == "2.15"
    assert extras[KEY_PAR_PORTION] == "1.07"
    assert extras[KEY_SOURCE] == "auto"
    # Clé tierce préservée
    assert extras["nutrition_calories"] == "450"


def test_sync_preserve_override_manuel_existant(orchestrator):
    _MockMealieClient._RECIPES["poulet-riz"] = {
        "slug": "poulet-riz",
        "name": "Poulet riz",
        "recipeServings": 2,
        "recipeIngredient": ["200g de poulet", "100g de riz"],
        "extras": {
            KEY_MANUEL_PAR_PORTION: "1.50",
            KEY_MANUEL_RAISON: "promo",
        },
    }

    result = orchestrator.sync_recipe_cost("poulet-riz", month="2026-04")

    assert result["override_preserved"] is True
    slug, extras = _MockMealieClient.patch_log[-1]
    assert extras[KEY_MANUEL_PAR_PORTION] == "1.50"
    assert extras[KEY_MANUEL_RAISON] == "promo"
    # Mais le calcul auto est quand même publié
    assert extras[KEY_PAR_PORTION] == "1.07"


def test_cost_recipe_utilise_override_par_portion(orchestrator):
    _MockMealieClient._RECIPES["poulet-riz"] = {
        "slug": "poulet-riz",
        "name": "Poulet riz",
        "recipeServings": 2,
        "recipeIngredient": ["200g de poulet", "100g de riz"],
        "extras": {KEY_MANUEL_PAR_PORTION: "3.00"},
    }

    cost = orchestrator.cost_recipe("poulet-riz")
    # 3.00 par portion * 2 portions = 6.00 total (override écrase le calcul 2.15)
    assert cost.cost_per_serving == 3.00
    assert cost.total_cost == 6.00


def test_refresh_all_costs_parcourt_toutes_les_recettes(orchestrator):
    _MockMealieClient._RECIPES.update(
        {
            "poulet-riz": {
                "slug": "poulet-riz",
                "name": "Poulet riz",
                "recipeServings": 2,
                "recipeIngredient": ["200g de poulet", "100g de riz"],
                "extras": {},
            },
            "riz-seul": {
                "slug": "riz-seul",
                "name": "Riz nature",
                "recipeServings": 1,
                "recipeIngredient": ["100g de riz"],
                "extras": {},
            },
            "vide": {
                "slug": "vide",
                "name": "Vide",
                "recipeServings": 1,
                "recipeIngredient": [],
                "extras": {},
            },
        }
    )

    report = orchestrator.refresh_all_costs(month="2026-04")

    assert report["month"] == "2026-04"
    assert report["updated"] == 2
    assert report["skipped"] == 1  # recette vide
    assert report["failed"] == []
    assert report["total"] == 3


def test_refresh_all_costs_compte_les_overrides(orchestrator):
    _MockMealieClient._RECIPES.update(
        {
            "avec-override": {
                "slug": "avec-override",
                "name": "Plat",
                "recipeServings": 2,
                "recipeIngredient": ["200g de poulet"],
                "extras": {KEY_MANUEL_PAR_PORTION: "1.50"},
            },
            "sans-override": {
                "slug": "sans-override",
                "name": "Plat",
                "recipeServings": 1,
                "recipeIngredient": ["100g de riz"],
                "extras": {},
            },
        }
    )

    report = orchestrator.refresh_all_costs()

    assert report["updated"] == 2
    assert report["override_preserved"] == 1
