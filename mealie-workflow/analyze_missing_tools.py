#!/usr/bin/env python3
"""
ANALYSE OUTILS MCP MANQUANTS
Identifie les outils nécessaires pour un import de recettes correct
"""

import json
import requests
from pathlib import Path

def load_mealie_config():
    """Charge la configuration Mealie"""
    config_path = Path(__file__).parent / "config" / "mealie_config.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement config: {e}")
        return None

def test_available_endpoints():
    """Test les endpoints API disponibles"""
    config = load_mealie_config()
    
    if not config:
        return {}
    
    api_url = config.get("mealie_api", {}).get("url", "")
    token = config.get("mealie_api", {}).get("token", "")
    
    if not api_url or not token:
        return {}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Endpoints à tester
    endpoints = {
        "recipes": f"{api_url}/recipes",
        "categories": f"{api_url}/categories", 
        "foods": f"{api_url}/foods",
        "units": f"{api_url}/units",
        "tools": f"{api_url}/tools",
        "tags": f"{api_url}/tags",
        "cookbooks": f"{api_url}/cookbooks",
        "mealplans": f"{api_url}/meal-plans",
        "shopping_lists": f"{api_url}/shopping-lists",
        "users": f"{api_url}/users",
        "groups": f"{api_url}/groups",
        "statistics": f"{api_url}/statistics",
        "imports": f"{api_url}/imports"
    }
    
    available = {}
    
    for name, url in endpoints.items():
        try:
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                available[name] = {"status": "available", "url": url}
                print(f"✅ {name}: Disponible")
            elif response.status_code == 401:
                available[name] = {"status": "auth_required", "url": url}
                print(f"🔒 {name}: Authentification requise")
            elif response.status_code == 404:
                available[name] = {"status": "not_found", "url": url}
                print(f"❌ {name}: Non trouvé")
            else:
                available[name] = {"status": f"error_{response.status_code}", "url": url}
                print(f"⚠️ {name}: Erreur {response.status_code}")
                
        except Exception as e:
            available[name] = {"status": "exception", "error": str(e)}
            print(f"💥 {name}: Exception - {e}")
    
    return available

def identify_missing_tools():
    """Identifie les outils MCP manquants pour un import complet"""
    print("🔍 OUTILS MCP MANQUANTS POUR IMPORT COMPLET")
    print("=" * 60)
    
    available_endpoints = test_available_endpoints()
    
    print(f"\n📊 ENDPOINTS DISPONIBLES: {len([e for e in available_endpoints.values() if e['status'] == 'available'])}")
    print(f"📊 ENDPOINTS BLOQUÉS: {len([e for e in available_endpoints.values() if e['status'] == 'auth_required'])}")
    
    print("\n🛠️ OUTILS MCP CRITIQUES MANQUANTS:")
    
    missing_tools = {
        # Import & Validation
        "mcp3_validate_recipe": {
            "description": "Valider la qualité d'une recette avant import",
            "priority": "HIGH",
            "endpoint": "/recipes/validate",
            "params": ["recipe_data"]
        },
        "mcp3_verify_import": {
            "description": "Vérifier qu'une recette a été correctement importée",
            "priority": "HIGH", 
            "endpoint": "/recipes/{slug}/verify",
            "params": ["recipe_slug"]
        },
        "mcp3_import_batch": {
            "description": "Importer plusieurs recettes en lot",
            "priority": "HIGH",
            "endpoint": "/recipes/batch-import",
            "params": ["recipes_list"]
        },
        
        # Gestion des données
        "mcp3_search_recipes": {
            "description": "Rechercher des recettes avec filtres",
            "priority": "MEDIUM",
            "endpoint": "/recipes/search",
            "params": ["query", "filters"]
        },
        "mcp3_export_recipes": {
            "description": "Exporter des recettes (JSON, CSV, etc.)",
            "priority": "MEDIUM",
            "endpoint": "/recipes/export",
            "params": ["format", "filters"]
        },
        "mcp3_duplicate_recipe": {
            "description": "Dupliquer une recette existante",
            "priority": "MEDIUM",
            "endpoint": "/recipes/{slug}/duplicate",
            "params": ["recipe_slug", "new_name"]
        },
        
        # Gestion des métadonnées
        "mcp3_list_categories": {
            "description": "Lister les catégories de recettes",
            "priority": "MEDIUM",
            "endpoint": "/categories",
            "params": []
        },
        "mcp3_create_category": {
            "description": "Créer une nouvelle catégorie",
            "priority": "MEDIUM", 
            "endpoint": "/categories",
            "params": ["name", "description"]
        },
        "mcp3_list_tags": {
            "description": "Lister les tags disponibles",
            "priority": "LOW",
            "endpoint": "/tags",
            "params": []
        },
        "mcp3_create_tag": {
            "description": "Créer un nouveau tag",
            "priority": "LOW",
            "endpoint": "/tags", 
            "params": ["name", "color"]
        },
        
        # Qualité & Validation
        "mcp3_check_recipe_quality": {
            "description": "Analyser la qualité d'une recette",
            "priority": "HIGH",
            "endpoint": "/recipes/{slug}/quality-check",
            "params": ["recipe_slug"]
        },
        "mcp3_get_nutrition_info": {
            "description": "Obtenir les informations nutritionnelles",
            "priority": "MEDIUM",
            "endpoint": "/recipes/{slug}/nutrition",
            "params": ["recipe_slug"]
        },
        
        # Statistiques & Monitoring
        "mcp3_get_import_stats": {
            "description": "Statistiques d'importation",
            "priority": "MEDIUM",
            "endpoint": "/statistics/imports",
            "params": ["date_range"]
        },
        "mcp3_get_recipe_stats": {
            "description": "Statistiques détaillées d'une recette",
            "priority": "LOW",
            "endpoint": "/recipes/{slug}/stats",
            "params": ["recipe_slug"]
        },
        
        # Nettoyage & Maintenance
        "mcp3_cleanup_duplicates": {
            "description": "Nettoyer les recettes en double",
            "priority": "HIGH",
            "endpoint": "/recipes/cleanup-duplicates",
            "params": ["dry_run"]
        },
        "mcp3_fix_invalid_recipes": {
            "description": "Corriger les recettes invalides",
            "priority": "HIGH",
            "endpoint": "/recipes/fix-invalid",
            "params": ["recipe_slugs"]
        }
    }
    
    # Organiser par priorité
    high_priority = {k: v for k, v in missing_tools.items() if v["priority"] == "HIGH"}
    medium_priority = {k: v for k, v in missing_tools.items() if v["priority"] == "MEDIUM"}
    low_priority = {k: v for k, v in missing_tools.items() if v["priority"] == "LOW"}
    
    print(f"\n🚨 PRIORITÉ HAUTE ({len(high_priority)} outils):")
    for tool, info in high_priority.items():
        print(f"   ❌ {tool}")
        print(f"      📝 {info['description']}")
        print(f"      🔗 API: {info['endpoint']}")
        print(f"      📋 Params: {', '.join(info['params'])}")
    
    print(f"\n⚠️ PRIORITÉ MOYENNE ({len(medium_priority)} outils):")
    for tool, info in medium_priority.items():
        print(f"   ❌ {tool}")
        print(f"      📝 {info['description']}")
        print(f"      🔗 API: {info['endpoint']}")
    
    print(f"\nℹ️ PRIORITÉ BASSE ({len(low_priority)} outils):")
    for tool, info in low_priority.items():
        print(f"   ❌ {tool}")
        print(f"      📝 {info['description']}")
    
    return missing_tools

def generate_missing_tools_plan():
    """Génère un plan pour créer les outils manquants"""
    missing_tools = identify_missing_tools()
    
    print(f"\n📋 PLAN DE CRÉATION DES OUTILS MANQUANTS")
    print("=" * 50)
    
    print("\n🎯 OBJECTIF: Créer les MCP manquants pour un import 100% fonctionnel")
    
    print("\n📅 PHASE 1: OUTILS CRITIQUES (Priorité HAUTE)")
    high_priority = [k for k, v in missing_tools.items() if v["priority"] == "HIGH"]
    
    for i, tool in enumerate(high_priority, 1):
        info = missing_tools[tool]
        print(f"   {i}. {tool}")
        print(f"      Description: {info['description']}")
        print(f"      Endpoint: {info['endpoint']}")
        print(f"      Paramètres: {', '.join(info['params'])}")
    
    print("\n📅 PHASE 2: OUTILS COMPLÉMENTAIRES (Priorité MOYENNE)")
    medium_priority = [k for k, v in missing_tools.items() if v["priority"] == "MEDIUM"]
    
    for i, tool in enumerate(medium_priority, 1):
        info = missing_tools[tool]
        print(f"   {i}. {tool}")
        print(f"      Description: {info['description']}")
        print(f"      Endpoint: {info['endpoint']}")
    
    print("\n💡 RECOMMANDATIONS:")
    print("   1. Commencer par les outils de validation (validate_recipe, verify_import)")
    print("   2. Implémenter l'import par lot (import_batch)")
    print("   3. Ajouter la recherche et l'export (search_recipes, export_recipes)")
    print("   4. Compléter avec les outils de qualité et statistiques")
    
    print(f"\n🎯 RÉSULTAT ATTENDU:")
    print(f"   - Import de recettes 100% fonctionnel")
    print(f"   - Validation automatique de la qualité")
    print(f"   - Vérification des imports réussis")
    print(f"   - Gestion par lot des recettes")
    print(f"   - Monitoring et statistiques complètes")

if __name__ == "__main__":
    generate_missing_tools_plan()
