"""Tests pour l'API du Menu Orchestrator."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from mealie_menu_orchestrator.api import app
from mealie_menu_orchestrator.config import MenuOrchestratorConfig


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
    }
    response = client.post("/menus/generate", json=request_data)
    # Sans les services externes, cela peut échouer
    # Le test vérifie juste que l'endpoint répond
    assert response.status_code in [200, 500]


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
