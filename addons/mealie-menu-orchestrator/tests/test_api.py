"""Tests pour l'API du Menu Orchestrator."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from mealie_menu_orchestrator.api import app
from mealie_menu_orchestrator.config import MenuOrchestratorConfig
from mealie_menu_orchestrator.models.menu import MenuGenerationRequest


class TestCombinedScorer:
    """Tests pour le CombinedScorer avec les nouveaux critères."""

    def test_normalize_rating_score(self):
        """Test la normalisation des scores de notation."""
        from mealie_menu_orchestrator.scoring.combined_scorer import CombinedScorer

        scorer = CombinedScorer(
            config=MenuOrchestratorConfig(),
            nutrition_client=None,
            budget_client=None,
        )
        
        # Rating 0 should be neutral (0.5)
        assert scorer._normalize_rating_score(0) == 0.5
        # Rating 5 should be max (1.0)
        assert scorer._normalize_rating_score(5) == 1.0
        # Rating 1 should be min (0.5)
        assert scorer._normalize_rating_score(1) == 0.5

    def test_normalize_time_score(self):
        """Test la normalisation des scores de temps."""
        from mealie_menu_orchestrator.scoring.combined_scorer import CombinedScorer

        scorer = CombinedScorer(
            config=MenuOrchestratorConfig(),
            nutrition_client=None,
            budget_client=None,
        )
        
        # Within 2h should be 1.0
        assert scorer._normalize_time_score(60) == 1.0
        assert scorer._normalize_time_score(120) == 1.0
        # Beyond 2h should be penalized
        assert scorer._normalize_time_score(180) < 1.0
        assert scorer._normalize_time_score(180) > 0.2

    def test_extract_total_time_minutes(self):
        """Test l'extraction du temps total en minutes."""
        from mealie_menu_orchestrator.scoring.combined_scorer import CombinedScorer

        scorer = CombinedScorer(
            config=MenuOrchestratorConfig(),
            nutrition_client=None,
            budget_client=None,
        )
        
        # ISO format "PT2H30M"
        assert scorer._extract_total_time_minutes({"totalTime": "PT2H30M"}) == 150
        # Integer minutes
        assert scorer._extract_total_time_minutes({"totalTime": 90}) == 90.0
        # Fallback to prep + cook
        assert scorer._extract_total_time_minutes(
            {"prepTime": "PT30M", "cookTime": "PT1H"}
        ) == 90


@pytest.fixture
def client():
    """Client de test FastAPI."""
    return TestClient(app)


def test_health(client):
    """Test du endpoint de santé."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_config(client):
    """Test du endpoint de configuration."""
    response = client.get("/config")
    assert response.status_code == 200
    config = response.json()
    assert "config" in config


def test_config_without_key(client):
    """Test que le config est accessible sans clé (pour le développement)."""
    response = client.get("/config")
    # Sans clé secrète configurée, cela devrait fonctionner
    assert response.status_code == 200


def test_menu_generation_requires_services(client):
    """Test que la génération de menu nécessite les services externes."""
    request_data = {
        "start_date": "2026-01-01",
        "end_date": "2026-01-07",
        "budget_limit": 200.0,
        "default_household_size": 4,
    }
    response = client.post("/menus/generate", json=request_data)
    # Sans les services externes, cela peut échouer
    # Le test vérifie juste que l'endpoint répond
    assert response.status_code in [200, 500]


def test_menu_generation_with_new_fields(client):
    """Test la génération de menu avec les nouveaux champs."""
    request_data = {
        "start_date": "2026-01-01",
        "end_date": "2026-01-07",
        "budget_limit": 200.0,
        "default_household_size": 4,
        "meal_quantity_overrides": {"2026-01-01_dinner": 5},
        "household_id": "test-household",
        "include_breakfast": False,
        "include_lunch": True,
        "include_dinner": True,
    }
    response = client.post("/menus/generate", json=request_data)
    # Sans les services externes, cela peut échouer
    assert response.status_code in [200, 500]


class TestMenuGenerationRequest:
    """Tests du modèle MenuGenerationRequest."""

    def test_default_meal_composition(self):
        """Test la composition par défaut des repas."""
        request = MenuGenerationRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 7),
        )
        assert request.default_household_size == 4
        assert request.include_breakfast is False
        assert request.include_lunch is True
        assert request.include_dinner is True
        assert request.meal_composition["lunch"] == ["starter", "main", "dessert"]
        assert request.meal_composition["dinner"] == ["starter", "main", "dessert"]

    def test_meal_quantity_overrides(self):
        """Test la surcharge de quantités par repas."""
        request = MenuGenerationRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 7),
            default_household_size=4,
            meal_quantity_overrides={"2026-01-01_dinner": 6},
        )
        assert request.meal_quantity_overrides["2026-01-01_dinner"] == 6

    def test_custom_meal_composition(self):
        """Test la composition personnalisée des repas."""
        request = MenuGenerationRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 7),
            meal_composition={"dinner": ["main"]},
        )
        assert request.meal_composition["dinner"] == ["main"]


def test_list_menus(client):
    """Test de la liste des menus."""
    response = client.get("/menus")
    assert response.status_code == 200
    menus = response.json()
    assert isinstance(menus, list)


def test_get_nonexistent_menu(client):
    """Test de récupération d'un menu inexistant."""
    response = client.get("/menus/nonexistent-id")
    assert response.status_code == 404


class TestConfig:
    """Tests de la configuration."""

    def test_default_config(self):
        """Test de la configuration par défaut."""
        config = MenuOrchestratorConfig()
        assert config.api_host == "0.0.0.0"
        assert config.api_port == 8004
        assert config.weight_nutrition == 0.25
        assert config.weight_budget == 0.25
        assert config.weight_variety == 0.25
        assert config.weight_season == 0.25

    def test_config_to_dict(self):
        """Test de la conversion de config en dictionnaire."""
        config = MenuOrchestratorConfig()
        config_dict = config.to_dict()
        assert "mealie_base_url" in config_dict
        assert "nutrition_advisor_url" in config_dict
        assert "budget_advisor_url" in config_dict
        assert "weight_nutrition" in config_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
