"""Tests E2E pour le workflow complet du Budget Advisor."""

import os
import time
from typing import Optional

import requests

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8003")
MEALIE_BASE_URL = os.getenv("MEALIE_BASE_URL", "http://localhost:9925")
MEALIE_API_KEY = os.getenv("MEALIE_API_KEY", "")


def test_health_check():
    """Test 1: Health check endpoint."""
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mealie-budget-advisor"
    print("✅ Health check OK")


def test_status_endpoint():
    """Test 2: Status endpoint."""
    response = requests.get(f"{API_BASE_URL}/status", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "config" in data
    print("✅ Status endpoint OK")


def test_budget_crud():
    """Test 3: Budget CRUD operations."""
    # Créer un budget
    budget_data = {
        "period": {"year": 2026, "month": 12},
        "total_budget": 600,
        "condiments_forfait": 25,
        "meals_per_day": 3,
        "days_per_month": 30,
    }
    response = requests.post(f"{API_BASE_URL}/budget", json=budget_data, timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["period"] == "2026-12"
    print("✅ Budget creation OK")

    # Récupérer le budget
    response = requests.get(f"{API_BASE_URL}/budget", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    print("✅ Budget retrieval OK")

    # Lister les budgets
    response = requests.get(f"{API_BASE_URL}/budget/list", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "budgets" in data
    print("✅ Budget list OK")

    # Supprimer le budget
    response = requests.delete(f"{API_BASE_URL}/budget/period/2026-12", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    print("✅ Budget deletion OK")


def test_manual_prices():
    """Test 4: Manual prices management."""
    # Ajouter un prix manuel (note: utilise query params)
    response = requests.post(
        "http://localhost:8003/prices/manual",
        params={
            "ingredient_name": "tomate",
            "price_per_unit": 2.50,
            "unit": "kg",
        },
        timeout=5,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    print("✅ Manual price creation OK")

    # Lister les prix manuels
    response = requests.get("http://localhost:8003/prices/manual", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    print("✅ Manual prices list OK")


def test_recipe_cost():
    """Test 5: Recipe cost calculation."""
    # Note: Ce test nécessite Mealie en cours d'exécution
    # et une recette avec le slug spécifié
    if not MEALIE_API_KEY:
        print("⏭️  Recipe cost test skipped (no Mealie API key)")
        return

    # Utiliser une recette test si disponible
    test_slug = "carbonara-marmiton"  # À adapter selon vos recettes

    response = requests.get(
        f"{API_BASE_URL}/recipes/{test_slug}/cost",
        params={"use_open_prices": True},
        timeout=10,
    )

    if response.status_code == 404:
        print(f"⏭️  Recipe cost test skipped (recipe '{test_slug}' not found)")
        return

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "cost" in data
    print("✅ Recipe cost calculation OK")


def run_e2e_tests():
    """Exécute tous les tests E2E."""
    print("\n🧪 Exécution des tests E2E Budget Advisor")
    print("=" * 50)

    tests = [
        test_health_check,
        test_status_endpoint,
        test_budget_crud,
        test_manual_prices,
        test_recipe_cost,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except requests.exceptions.ConnectionError:
            print(f"❌ {test.__name__} FAILED: API not reachable")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1

    print("=" * 50)
    print(f"\n📊 Résultats: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 Tous les tests E2E réussis!")
        return 0
    else:
        print(f"⚠️  {failed} test(s) échoué(s)")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(run_e2e_tests())
