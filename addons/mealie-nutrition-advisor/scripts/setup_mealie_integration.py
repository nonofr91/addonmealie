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

import httpx
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


def get_client() -> httpx.Client:
    """Crée un client HTTP avec authentification."""
    headers = {
        "Authorization": f"Bearer {MEALIE_API_KEY}",
        "Content-Type": "application/json",
    }
    return httpx.Client(base_url=MEALIE_BASE_URL, headers=headers, timeout=30.0)


def get_or_create_tag(client: httpx.Client, tag_name: str) -> str:
    """Récupère ou crée un tag."""
    # Chercher le tag existant
    resp = client.get("/api/organizers/tags", params={"perPage": 200})
    resp.raise_for_status()
    tags = resp.json().get("items", [])
    
    for tag in tags:
        if tag.get("name") == tag_name:
            print(f"✓ Tag '{tag_name}' trouvé (ID: {tag.get('id')})")
            return tag.get("id")
    
    # Créer le tag s'il n'existe pas
    print(f"Création du tag '{tag_name}'...")
    resp = client.post("/api/organizers/tags", json={"name": tag_name})
    resp.raise_for_status()
    tag_id = resp.json().get("id")
    print(f"✓ Tag '{tag_NAME}' créé (ID: {tag_id})")
    return tag_id


def create_nutrition_advisor_recipe(client: httpx.Client, tag_id: str) -> dict:
    """Crée la recette spéciale Nutrition Advisor."""
    # Chercher si la recette existe déjà
    print(f"Recherche de la recette '{RECIPE_NAME}'...")
    resp = client.get("/api/recipes", params={"perPage": 200})
    resp.raise_for_status()
    recipes = resp.json().get("items", [])
    
    existing_slug = None
    for recipe in recipes:
        if recipe.get("name") == RECIPE_NAME:
            existing_slug = recipe.get("slug")
            print(f"✓ Recette existante trouvée (slug: {existing_slug})")
            break
    
    if existing_slug:
        print(f"⚠ La recette existe déjà. Supprimez-la d'abord dans Mealie ou utilisez un autre nom.")
        return {"slug": existing_slug, "name": RECIPE_NAME}
    
    # Créer une nouvelle recette avec tous les champs en une seule fois
    print(f"Création de la recette '{RECIPE_NAME}' avec description et tag...")
    recipe_data = {
        "name": RECIPE_NAME,
        "description": RECIPE_DESCRIPTION,
        "tags": [TAG_NAME],
        "recipeIngredient": [],
        "recipeInstructions": []
    }
    
    try:
        # Essayer POST avec payload complet
        resp = client.post("/api/recipes", json=recipe_data)
        if resp.status_code == 200:
            recipe = resp.json()
            print(f"✓ Recette créée avec succès (slug: {recipe.get('slug')})")
            return recipe
        else:
            print(f"⚠ POST retourné {resp.status_code}")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 422:
            print(f"⚠ Erreur 422 - payload non accepté")
            print(f"   L'API locale n'accepte que {'name': ...} lors de la création")
        else:
            print(f"⚠ Erreur POST: {exc.response.status_code}")
            raise
    
    # Fallback : créer avec seulement le nom
    print(f"Création de la recette avec seulement le nom...")
    resp = client.post("/api/recipes", json={"name": RECIPE_NAME})
    resp.raise_for_status()
    slug = resp.json()
    print(f"✓ Recette créée (slug: {slug})")
    
    # Essayer d'ajouter le tag via l'endpoint de liaison
    print(f"Tentative d'ajout du tag à la recette...")
    try:
        # Récupérer l'ID de la recette
        resp = client.get(f"/api/recipes/{slug}")
        resp.raise_for_status()
        recipe_id = resp.json().get("id")
        
        # Essayer d'ajouter le tag via l'endpoint de liaison
        resp = client.post(f"/api/recipes/{recipe_id}/tags", json={"id": tag_id})
        if resp.status_code == 200:
            print(f"✓ Tag ajouté à la recette")
    except Exception as exc:
        print(f"⚠ Impossible d'ajouter le tag automatiquement: {exc}")
    
    print(f"⚠ L'API locale ne permet pas d'ajouter description lors de la création.")
    print(f"   Vous devrez mettre à jour la description manuellement dans Mealie.")
    return {"slug": slug, "name": RECIPE_NAME}


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
        with get_client() as client:
            # Vérifier la connexion
            print("Vérification de la connexion à Mealie...")
            try:
                resp = client.get("/api/about")
                resp.raise_for_status()
                print(f"✓ Connecté à Mealie (version: {resp.json().get('version', 'inconnue')})")
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    print("⚠ Endpoint /api/about non trouvé, tentative de continuer...")
                else:
                    raise
            print()
            
            # Créer ou récupérer le tag
            tag_id = get_or_create_tag(client, TAG_NAME)
            print()
            
            # Créer la recette spéciale
            recipe = create_nutrition_advisor_recipe(client, tag_id)
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
            
    except httpx.HTTPStatusError as exc:
        print(f"❌ Erreur HTTP {exc.response.status_code}")
        if exc.response.status_code == 401:
            print("   Vérifiez que votre API key est correcte")
        elif exc.response.status_code == 403:
            print("   Vérifiez les permissions de votre API key")
        elif exc.response.status_code == 404:
            print("   Endpoint non trouvé, vérifiez l'URL de Mealie")
        else:
            print(f"   {exc.response.text[:200]}")
        sys.exit(1)
    except httpx.ConnectError:
        print("❌ Erreur de connexion à Mealie")
        print(f"   Vérifiez que Mealie est accessible à {MEALIE_BASE_URL}")
        sys.exit(1)
    except Exception as exc:
        print(f"❌ Erreur: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
