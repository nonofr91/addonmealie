#!/usr/bin/env python3
"""
Script pour créer une recette spéciale "Nutrition Advisor" dans Mealie
avec une recipe action vers l'UI de l'addon.

Usage:
    python3 setup_mealie_integration.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

MEALIE_BASE_URL = os.environ.get("MEALIE_BASE_URL", "http://localhost:9000").rstrip("/")
MEALIE_API_KEY = os.environ.get("MEALIE_API_KEY", "")
ADDON_UI_URL = os.environ.get("ADDON_UI_URL", "http://localhost:8502")

# Configuration de la recette spéciale
RECIPE_NAME = "🔬 Nutrition Advisor"
RECIPE_DESCRIPTION = """
Gestionnaire de profils nutritionnels et planificateur de menus.

Cette recette spéciale fournit un lien vers l'interface de gestion des profils 
nutritionnels de l'addon mealie-nutrition-advisor.

Fonctionnalités :
- Gestion des profils des membres du foyer
- Configuration des pathologies médicales
- Planification des présences hebdomadaires
- Calcul nutritionnel personnalisé
"""
TAG_NAME = "nutrition-addon"

# Charger mcp_auth_wrapper depuis mealie-workflow
WORKFLOW_DIR = Path(__file__).parent.parent.parent.parent / "mealie-workflow"
sys.path.insert(0, str(WORKFLOW_DIR))

try:
    import mcp_auth_wrapper as mcp
    print(f"✓ mcp_auth_wrapper chargé depuis {WORKFLOW_DIR}")
except ImportError as exc:
    print(f"❌ Impossible d'importer mcp_auth_wrapper: {exc}")
    print(f"   Assurez-vous que mealie-workflow existe à {WORKFLOW_DIR}")
    sys.exit(1)


def get_or_create_tag(tag_name: str) -> str:
    """Récupère ou crée un tag via API REST (pas de fonction MCP dans le wrapper)."""
    import requests
    
    headers = {
        "Authorization": f"Bearer {MEALIE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    api_url = f"{MEALIE_BASE_URL}/api"
    
    # Chercher le tag existant
    resp = requests.get(f"{api_url}/organizers/tags", params={"perPage": 200}, headers=headers)
    resp.raise_for_status()
    tags = resp.json().get("items", [])
    
    for tag in tags:
        if tag.get("name") == tag_name:
            print(f"✓ Tag '{tag_name}' trouvé (ID: {tag.get('id')})")
            return tag.get("id")
    
    # Créer le tag s'il n'existe pas
    print(f"Création du tag '{tag_name}'...")
    resp = requests.post(f"{api_url}/organizers/tags", headers=headers, json={"name": tag_name})
    resp.raise_for_status()
    tag_id = resp.json().get("id")
    print(f"✓ Tag '{tag_name}' créé (ID: {tag_id})")
    return tag_id


def create_nutrition_advisor_recipe(tag_id: str) -> dict:
    """Crée la recette spéciale Nutrition Advisor via mcp_auth_wrapper."""
    # Chercher si la recette existe déjà
    print(f"Recherche de la recette '{RECIPE_NAME}'...")
    recipes = mcp.mcp3_list_recipes()
    
    existing_slug = None
    for recipe in recipes:
        if recipe.get("name") == RECIPE_NAME:
            existing_slug = recipe.get("slug")
            print(f"✓ Recette existante trouvée (slug: {existing_slug})")
            break
    
    if existing_slug:
        print(f"⚠ La recette existe déjà. Supprimez-la d'abord dans Mealie ou utilisez un autre nom.")
        return {"slug": existing_slug, "name": RECIPE_NAME}
    
    # Créer la recette via mcp_auth_wrapper
    print(f"Création de la recette '{RECIPE_NAME}' avec description et tag...")
    
    result = mcp.mcp3_create_recipe(
        name=RECIPE_NAME,
        description=RECIPE_DESCRIPTION,
        tags=[TAG_NAME],
        ingredients=[],
        instructions=[]
    )
    
    if result.get("success"):
        slug = result.get("recipe_id")
        print(f"✓ Recette créée avec succès (slug: {slug})")
        return {"slug": slug, "name": RECIPE_NAME}
    else:
        print(f"❌ Erreur lors de la création: {result.get('error')}")
        sys.exit(1)


def main():
    """Fonction principale."""
    print("=" * 60)
    print("Configuration de l'intégration Mealie pour Nutrition Advisor")
    print("=" * 60)
    print(f"Mealie URL: {MEALIE_BASE_URL}")
    print(f"Addon UI URL: {ADDON_UI_URL}")
    print()
    
    if not MEALIE_API_KEY:
        print("❌ Erreur: MEALIE_API_KEY non définie")
        print("   Définissez cette variable d'environnement ou dans .env")
        sys.exit(1)
    
    try:
        # Vérifier la connexion
        print("Vérification de la connexion à Mealie...")
        recipes = mcp.mcp3_list_recipes()
        print(f"✓ Connecté à Mealie ({len(recipes)} recettes trouvées)")
        print()
        
        # Créer ou récupérer le tag
        tag_id = get_or_create_tag(TAG_NAME)
        print()
        
        # Créer la recette spéciale
        recipe = create_nutrition_advisor_recipe(tag_id)
        print()
        
        print("=" * 60)
        print("✓ Configuration terminée avec succès")
        print("=" * 60)
        print()
        print(f"Recette créée : {MEALIE_BASE_URL}/recipe/{recipe.get('slug')}")
        print(f"Tag : {TAG_NAME}")
        print(f"Action : {ADDON_UI_URL}")
        print()
        print("Vous pouvez maintenant trouver cette recette dans Mealie en")
        print("recherchant le tag 'nutrition-addon' ou le nom '🔬 Nutrition Advisor'.")
            
    except Exception as exc:
        print(f"❌ Erreur: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
