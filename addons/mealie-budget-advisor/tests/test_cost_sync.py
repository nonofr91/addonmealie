"""Tests d'intégration pour la publication des coûts dans ``extras`` de Mealie.

Mealie est mocké : pas besoin de Mealie réel pour ces tests.
"""

from unittest.mock import MagicMock

import pytest

from mealie_budget_advisor.mealie_sync import MealieClient
from mealie_budget_advisor.pricing.cost_calculator import CostCalculator


@pytest.fixture()
def fake_recipe() -> dict:
    return {
        "slug": "poulet-riz",
        "name": "Poulet riz",
        "recipeYield": "2 portions",
        "extras": {
            "autre_addon": "valeur",
        },
        "recipeIngredient": [
            {"note": "200g de poulet"},
            {"note": "100g de riz"},
        ],
    }


@pytest.fixture()
def mock_client(fake_recipe):
    client = MagicMock(spec=MealieClient)
    client.get_recipe.return_value = fake_recipe
    client.get_all_recipes.return_value = [fake_recipe]
    client.patch_extras.return_value = True
    return client


def _build_calculator_with_stub_matcher(recipe: dict) -> CostCalculator:
    """Crée un CostCalculator dont le matcher + Mealie sont tous les deux mockés."""
    calculator = CostCalculator(
        mealie_base_url="http://stub",
        mealie_api_key="stub",
    )

    # Stub matcher.find_price : retourne un prix connu pour tout ingrédient
    calculator.matcher = MagicMock()
    calculator.matcher.parse_ingredient_note.side_effect = lambda note: (100.0, "g", note)
    calculator.matcher.find_price.return_value = (1.00, "manual", 1.0)

    # Stub get_recipe (HTTP directe) pour qu'il retourne la recette fournie
    calculator.get_recipe = MagicMock(return_value=recipe)  # type: ignore[method-assign]
    return calculator


class TestSyncRecipeCost:
    def test_success_preserves_foreign_extras(self, mock_client, fake_recipe):
        calculator = _build_calculator_with_stub_matcher(fake_recipe)

        result = calculator.sync_recipe_cost(
            slug="poulet-riz",
            month="2026-04",
            mealie_client=mock_client,
        )

        assert result["success"] is True
        assert result["patched"] is True
        # L'addon n'a pas écrasé la clé d'un autre addon
        assert result["extras"]["autre_addon"] == "valeur"
        # Les clés addon sont bien écrites
        assert "cout_total" in result["extras"]
        assert result["extras"]["cout_source"] == "auto"
        assert result["extras"]["cout_mois_reference"] == "2026-04"
        mock_client.patch_extras.assert_called_once()

    def test_preserves_user_override_keys(self, mock_client, fake_recipe):
        fake_recipe["extras"]["cout_manuel_par_portion"] = "1.50"
        fake_recipe["extras"]["cout_manuel_raison"] = "promo"

        calculator = _build_calculator_with_stub_matcher(fake_recipe)
        result = calculator.sync_recipe_cost(
            slug="poulet-riz",
            mealie_client=mock_client,
        )

        assert result["success"] is True
        assert result["has_override"] is True
        # Les clés utilisateur sont conservées intactes
        assert result["extras"]["cout_manuel_par_portion"] == "1.50"
        assert result["extras"]["cout_manuel_raison"] == "promo"
        # Source marquée "manuel" à cause de l'override
        assert result["extras"]["cout_source"] == "manuel"

    def test_recipe_not_found(self, mock_client):
        calculator = CostCalculator(
            mealie_base_url="http://stub",
            mealie_api_key="stub",
        )
        calculator.get_recipe = MagicMock(return_value=None)  # type: ignore[method-assign]

        result = calculator.sync_recipe_cost(
            slug="inexistante",
            mealie_client=mock_client,
        )

        assert result["success"] is False
        assert "introuvable" in result["error"]
        mock_client.patch_extras.assert_not_called()

    def test_patch_failure(self, fake_recipe):
        calculator = _build_calculator_with_stub_matcher(fake_recipe)
        client = MagicMock(spec=MealieClient)
        client.patch_extras.return_value = False

        result = calculator.sync_recipe_cost(
            slug="poulet-riz",
            mealie_client=client,
        )

        assert result["success"] is False
        assert result["patched"] is False


class TestRefreshAllCosts:
    def test_summary_counts(self, mock_client, fake_recipe):
        # Ajouter une seconde recette avec override
        recipe_with_override = {
            **fake_recipe,
            "slug": "carbonara",
            "name": "Carbonara",
            "extras": {"cout_manuel_par_portion": "2.00"},
        }
        mock_client.get_all_recipes.return_value = [fake_recipe, recipe_with_override]

        calculator = _build_calculator_with_stub_matcher(fake_recipe)

        # Pour renvoyer la bonne recette selon le slug
        def _get_recipe(slug: str) -> dict:
            return recipe_with_override if slug == "carbonara" else fake_recipe

        calculator.get_recipe = MagicMock(side_effect=_get_recipe)  # type: ignore[method-assign]

        summary = calculator.refresh_all_costs(
            month="2026-04",
            mealie_client=mock_client,
        )

        assert summary["total"] == 2
        assert summary["updated"] == 2
        assert summary["failed"] == 0
        assert summary["overrides_preserved"] == 1
        assert summary["month"] == "2026-04"

    def test_counts_failures(self, fake_recipe):
        client = MagicMock(spec=MealieClient)
        client.get_all_recipes.return_value = [fake_recipe]
        client.patch_extras.return_value = False

        calculator = _build_calculator_with_stub_matcher(fake_recipe)
        summary = calculator.refresh_all_costs(mealie_client=client)

        assert summary["total"] == 1
        assert summary["updated"] == 0
        assert summary["failed"] == 1

    def test_skips_recipe_without_slug(self, fake_recipe):
        client = MagicMock(spec=MealieClient)
        client.get_all_recipes.return_value = [{"name": "sans slug"}, fake_recipe]
        client.patch_extras.return_value = True

        calculator = _build_calculator_with_stub_matcher(fake_recipe)
        summary = calculator.refresh_all_costs(mealie_client=client)

        assert summary["total"] == 2
        assert summary["skipped"] == 1
        assert summary["updated"] == 1


class TestPatchExtrasSerialization:
    def test_values_coerced_to_string(self, monkeypatch):
        import requests

        called_with = {}

        class FakeResponse:
            status_code = 200

            def raise_for_status(self):
                return None

        class FakeSession:
            def __init__(self):
                self.headers = {}

            def patch(self, url, json=None, timeout=None):
                called_with["url"] = url
                called_with["json"] = json
                return FakeResponse()

        monkeypatch.setattr(requests, "Session", FakeSession)
        client = MealieClient(base_url="http://stub", api_key="k")
        assert client.patch_extras("slug", {"cout_total": 2.15, "cout_confiance": 1.0}) is True
        assert called_with["url"].endswith("/api/recipes/slug")
        assert called_with["json"]["extras"]["cout_total"] == "2.15"
        assert called_with["json"]["extras"]["cout_confiance"] == "1.0"
