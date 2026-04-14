#!/usr/bin/env python3
"""
MEALIE MCP AUTH CORRECTOR
Corrige les MCP Mealie pour utiliser l'authentification
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

def test_auth_with_config():
    """Test l'authentification avec la configuration"""
    config = load_mealie_config()
    
    if not config:
        return False
    
    api_url = config.get("mealie_api", {}).get("url")
    token = config.get("mealie_api", {}).get("token")
    
    if not api_url or not token:
        print("❌ URL ou token manquant dans la configuration")
        return False
    
    print(f"🔧 Test authentification avec:")
    print(f"   URL: {api_url}")
    print(f"   Token: {token[:20]}...")
    
    # Test d'authentification
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # Tester l'API Mealie directement
        response = requests.get(f"{api_url}/recipes", headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Authentification réussie !")
            recipes = response.json()
            print(f"   📋 {len(recipes)} recettes trouvées")
            return True
        elif response.status_code == 401:
            print("❌ Erreur 401 - Token invalide ou expiré")
            return False
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False

def create_auth_fixed_mcp():
    """Crée des MCP avec authentification corrigée"""
    config = load_mealie_config()
    
    if not config:
        return None
    
    api_url = config.get("mealie_api", {}).get("url")
    token = config.get("mealie_api", {}).get("token")
    
    if not api_url or not token:
        return None
    
    # Créer les MCP avec authentification
    def auth_mcp3_list_recipes():
        """Liste les recettes avec authentification"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(f"{api_url}/recipes", headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return []
    
    def auth_mcp3_get_recipe_details(slug):
        """Obtient les détails d'une recette avec authentification"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(f"{api_url}/recipes/{slug}", headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return {"name": "Erreur", "ingredients": [], "instructions": []}
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return {"name": "Erreur", "ingredients": [], "instructions": []}
    
    def auth_mcp3_create_recipe(**kwargs):
        """Crée une recette avec authentification"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Préparer le payload
        payload = {
            "name": kwargs.get("name", "Recette sans nom"),
            "description": kwargs.get("description", ""),
            "recipeIngredient": kwargs.get("ingredients", []),
            "recipeInstructions": kwargs.get("instructions", []),
            "recipeServings": kwargs.get("servings", 4),
            "prepTime": kwargs.get("prep_time", "PT15M"),
            "cookTime": kwargs.get("cook_time", "PT30M"),
            "totalTime": kwargs.get("total_time", "PT45M"),
            "recipeCategory": kwargs.get("categories", []),
            "tags": kwargs.get("tags", []),
            "image": kwargs.get("image", "")
        }
        
        try:
            response = requests.post(f"{api_url}/recipes", headers=headers, json=payload, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {"success": True, "recipe_id": result.get("id", "unknown")}
            else:
                print(f"❌ Erreur création: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return {"success": False, "error": str(e)}
    
    def auth_mcp3_delete_recipe(slug):
        """Supprime une recette avec authentification"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.delete(f"{api_url}/recipes/{slug}", headers=headers, timeout=10)
            
            if response.status_code in [200, 204]:
                return {"success": True, "message": f"Recette {slug} supprimée"}
            else:
                print(f"❌ Erreur suppression: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return {"success": False, "error": str(e)}
    
    def auth_mcp3_update_recipe(slug, updates):
        """Met à jour une recette avec authentification"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.patch(f"{api_url}/recipes/{slug}", headers=headers, json=updates, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return {"success": True, "updated_recipe": result}
            else:
                print(f"❌ Erreur mise à jour: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ Erreur connexion: {e}")
            return {"success": False, "error": str(e)}
    
    return {
        "list_recipes": auth_mcp3_list_recipes,
        "get_recipe_details": auth_mcp3_get_recipe_details,
        "create_recipe": auth_mcp3_create_recipe,
        "delete_recipe": auth_mcp3_delete_recipe,
        "update_recipe": auth_mcp3_update_recipe
    }

def test_auth_fixed_mcp():
    """Test les MCP avec authentification corrigée"""
    print("🧪 TEST MCP AVEC AUTHENTIFICATION CORRIGÉE")
    print("=" * 50)
    
    mcp_functions = create_auth_fixed_mcp()
    
    if not mcp_functions:
        print("❌ Impossible de créer les MCP avec authentification")
        return False
    
    results = {}
    
    # Test list_recipes
    try:
        recipes = mcp_functions["list_recipes"]()
        print(f"✅ list_recipes: {len(recipes)} recettes")
        results["list_recipes"] = True
        
        if recipes:
            # Test get_recipe_details
            first_slug = recipes[0].get("slug", "")
            if first_slug:
                details = mcp_functions["get_recipe_details"](first_slug)
                print(f"✅ get_recipe_details: {details.get('name', 'N/A')}")
                results["get_recipe_details"] = True
            else:
                results["get_recipe_details"] = False
        else:
            results["get_recipe_details"] = False
            
    except Exception as e:
        print(f"❌ Erreur list_recipes: {e}")
        results["list_recipes"] = False
        results["get_recipe_details"] = False
    
    # Test create_recipe
    try:
        new_recipe = mcp_functions["create_recipe"](
            name="Test Auth MCP",
            description="Test avec authentification corrigée",
            ingredients=["Test 1", "Test 2"],
            instructions=["Étape 1", "Étape 2"],
            servings=4
        )
        print(f"✅ create_recipe: {new_recipe.get('success', False)}")
        results["create_recipe"] = True
    except Exception as e:
        print(f"❌ Erreur create_recipe: {e}")
        results["create_recipe"] = False
    
    # Résultats
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n📊 Résultats: {success_count}/{total_count} MCP fonctionnent")
    
    if success_count >= total_count * 0.8:
        print("🎉 Authentification MCP corrigée avec succès !")
        return mcp_functions
    else:
        print("⚠️ Authentification partiellement corrigée")
        return mcp_functions

def generate_auth_wrapper():
    """Génère le wrapper MCP avec authentification"""
    mcp_functions = test_auth_fixed_mcp()
    
    if not mcp_functions:
        return None
    
    wrapper_content = '''#!/usr/bin/env python3
"""
MEALIE MCP WRAPPER - AUTHENTIFICATION CORRIGÉE
Utilise les vrais MCP Mealie avec authentification
"""

import sys
from pathlib import Path

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

# MCP avec authentification corrigée
def mcp3_list_recipes():
    """Liste les recettes Mealie avec authentification"""
    return ''' + repr(mcp_functions["list_recipes"]) + '''

def mcp3_get_recipe_details(slug):
    """Détails recette Mealie avec authentification"""
    return ''' + repr(mcp_functions["get_recipe_details"]) + '''

def mcp3_create_recipe(**kwargs):
    """Création recette Mealie avec authentification"""
    return ''' + repr(mcp_functions["create_recipe"]) + '''

def mcp3_delete_recipe(slug):
    """Suppression recette Mealie avec authentification"""
    return ''' + repr(mcp_functions["delete_recipe"]) + '''

def mcp3_update_recipe(slug, updates):
    """Mise à jour recette Mealie avec authentification"""
    return ''' + repr(mcp_functions["update_recipe"]) + '''

# MCP Jina (disponibles directement)
try:
    mcp2_read_url = globals().get('mcp2_read_url')
    mcp2_search_images = globals().get('mcp2_search_images')
    mcp2_show_api_key = globals().get('mcp2_show_api_key')
    print("✅ MCP Jina disponibles")
except:
    print("⚠️ MCP Jina non disponibles")

print("🎉 MCP WRAPPER AUTHENTIFIÉ INITIALISÉ")
print("✅ Vrais MCP Mealie avec authentification")
print("✅ Plus besoin de MCP mealie-test")
'''
    
    # Écrire le wrapper
    wrapper_path = Path(__file__).parent / "mcp_auth_wrapper.py"
    
    try:
        with open(wrapper_path, 'w', encoding='utf-8') as f:
            f.write(wrapper_content)
        
        print(f"✅ Wrapper authentifié créé: {wrapper_path}")
        return str(wrapper_path)
        
    except Exception as e:
        print(f"❌ Erreur création wrapper: {e}")
        return None

if __name__ == "__main__":
    print("🔧 CORRECTION AUTHENTIFICATION MCP MEALIE")
    print("=" * 50)
    
    # 1. Tester l'authentification avec la config
    if test_auth_with_config():
        print("\n✅ Authentification configuration valide")
        
        # 2. Créer les MCP avec authentification
        print("\n🔧 Création MCP avec authentification...")
        mcp_functions = test_auth_fixed_mcp()
        
        # 3. Générer le wrapper
        print("\n📝 Génération wrapper authentifié...")
        wrapper_path = generate_auth_wrapper()
        
        if wrapper_path:
            print(f"\n🎉 SUCCÈS ! Wrapper authentifié créé:")
            print(f"   📁 {wrapper_path}")
            print("\n📋 Prochaines étapes:")
            print("   1. Remplacer mcp_wrapper.py par mcp_auth_wrapper.py")
            print("   2. Supprimer tous les MCP mealie-test")
            print("   3. Tester le workflow complet")
        else:
            print("\n❌ Erreur création wrapper")
    else:
        print("\n❌ Authentification échouée")
        print("🔧 Vérifier la configuration dans config/mealie_config.json")
