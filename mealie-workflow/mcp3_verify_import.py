#!/usr/bin/env python3
"""
MCP3 VERIFY IMPORT
Outil MCP pour vérifier qu'une recette a été correctement importée
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional

def verify_import(recipe_slug: str, expected_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Vérifie qu'une recette a été correctement importée
    
    Args:
        recipe_slug: Slug de la recette à vérifier
        expected_data: Données attendues pour comparaison (optionnel)
        
    Returns:
        Dict avec résultats de vérification
    """
    try:
        print(f"🔍 Vérification import: {recipe_slug}")
        
        # Charger la configuration Mealie
        config_path = "config/mealie_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            return {
                "success": False,
                "error": "Configuration Mealie non trouvée",
                "verification_status": "FAILED"
            }
        
        api_url = config.get("mealie_api", {}).get("url", "")
        token = config.get("mealie_api", {}).get("token", "")
        
        if not api_url or not token:
            return {
                "success": False,
                "error": "Configuration API manquante",
                "verification_status": "FAILED"
            }
        
        # 1. Vérifier que la recette existe
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{api_url}/recipes/{recipe_slug}", headers=headers, timeout=10)
        
        verification_results = {
            "recipe_slug": recipe_slug,
            "verification_timestamp": datetime.now().isoformat(),
            "verification_status": "PASSED",
            "checks": {},
            "issues": [],
            "score": 100,
            "imported_recipe": None
        }
        
        if response.status_code == 200:
            imported_recipe = response.json()
            verification_results["imported_recipe"] = imported_recipe
            
            print(f"   ✅ Recette trouvée: {imported_recipe.get('name', 'N/A')}")
            verification_results["checks"]["existence"] = "✅ Recette existe"
        else:
            verification_results["verification_status"] = "FAILED"
            verification_results["issues"].append(f"Recette non trouvée (HTTP {response.status_code})")
            verification_results["checks"]["existence"] = "❌ Recette non trouvée"
            verification_results["score"] -= 50
            return verification_results
        
        # 2. Vérifier la structure des données
        required_fields = ["name", "recipeIngredient", "recipeInstructions"]
        missing_fields = []
        
        for field in required_fields:
            if field not in imported_recipe or not imported_recipe[field]:
                missing_fields.append(field)
                verification_results["score"] -= 20
        
        if missing_fields:
            verification_results["issues"].append(f"Champs manquants: {', '.join(missing_fields)}")
            verification_results["checks"]["structure"] = f"❌ Champs manquants: {missing_fields}"
        else:
            verification_results["checks"]["structure"] = "✅ Structure complète"
        
        # 3. Vérifier la qualité des données
        name = imported_recipe.get("name", "").strip()
        ingredients = imported_recipe.get("recipeIngredient", [])
        instructions = imported_recipe.get("recipeInstructions", [])
        
        # Vérifier le nom
        if len(name) < 3:
            verification_results["issues"].append("Nom trop court")
            verification_results["score"] -= 10
            verification_results["checks"]["name_quality"] = "⚠️ Nom court"
        else:
            verification_results["checks"]["name_quality"] = "✅ Nom valide"
        
        # Vérifier les ingrédients
        if len(ingredients) < 2:
            verification_results["issues"].append("Moins de 2 ingrédients")
            verification_results["score"] -= 15
            verification_results["checks"]["ingredients_quality"] = f"⚠️ Seulement {len(ingredients)} ingrédients"
        else:
            valid_ingredients = sum(1 for ing in ingredients if isinstance(ing, str) and len(ing.strip()) > 2)
            verification_results["checks"]["ingredients_quality"] = f"✅ {valid_ingredients}/{len(ingredients)} ingrédients valides"
        
        # Vérifier les instructions
        if len(instructions) < 2:
            verification_results["issues"].append("Moins de 2 instructions")
            verification_results["score"] -= 15
            verification_results["checks"]["instructions_quality"] = f"⚠️ Seulement {len(instructions)} instructions"
        else:
            valid_instructions = sum(1 for inst in instructions if isinstance(inst, str) and len(inst.strip()) > 5)
            verification_results["checks"]["instructions_quality"] = f"✅ {valid_instructions}/{len(instructions)} instructions valides"
        
        # 4. Comparaison avec données attendues (si fournies)
        if expected_data:
            verification_results["checks"]["comparison"] = {}
            
            # Comparer le nom
            expected_name = expected_data.get("name", "").lower()
            imported_name = name.lower()
            
            if expected_name and expected_name != imported_name:
                verification_results["issues"].append(f"Nom différent: attendu '{expected_name}', obtenu '{imported_name}'")
                verification_results["score"] -= 10
                verification_results["checks"]["comparison"]["name"] = "❌ Nom différent"
            else:
                verification_results["checks"]["comparison"]["name"] = "✅ Nom correspond"
            
            # Comparer le nombre d'ingrédients
            expected_ingredients_count = len(expected_data.get("ingredients", []))
            imported_ingredients_count = len(ingredients)
            
            if abs(expected_ingredients_count - imported_ingredients_count) > 1:
                verification_results["issues"].append(f"Nombre d'ingrédients différent: attendu {expected_ingredients_count}, obtenu {imported_ingredients_count}")
                verification_results["score"] -= 10
                verification_results["checks"]["comparison"]["ingredients_count"] = "❌ Nombre différent"
            else:
                verification_results["checks"]["comparison"]["ingredients_count"] = "✅ Nombre similaire"
            
            # Comparer le nombre d'instructions
            expected_instructions_count = len(expected_data.get("instructions", []))
            imported_instructions_count = len(instructions)
            
            if abs(expected_instructions_count - imported_instructions_count) > 1:
                verification_results["issues"].append(f"Nombre d'instructions différent: attendu {expected_instructions_count}, obtenu {imported_instructions_count}")
                verification_results["score"] -= 10
                verification_results["checks"]["comparison"]["instructions_count"] = "❌ Nombre différent"
            else:
                verification_results["checks"]["comparison"]["instructions_count"] = "✅ Nombre similaire"
        
        # 5. Vérifier les métadonnées
        metadata_fields = ["id", "slug", "createdAt", "updatedAt"]
        metadata_present = sum(1 for field in metadata_fields if field in imported_recipe)
        
        if metadata_present >= 3:
            verification_results["checks"]["metadata"] = f"✅ {metadata_present}/{len(metadata_fields)} métadonnées présentes"
        else:
            verification_results["issues"].append(f"Métadonnées incomplètes: {metadata_present}/{len(metadata_fields)}")
            verification_results["score"] -= 5
            verification_results["checks"]["metadata"] = f"⚠️ Métadonnées incomplètes"
        
        # 6. Score final et statut
        verification_results["score"] = max(0, verification_results["score"])
        
        if verification_results["score"] >= 80:
            verification_results["verification_status"] = "PASSED"
        elif verification_results["score"] >= 60:
            verification_results["verification_status"] = "WARNING"
        else:
            verification_results["verification_status"] = "FAILED"
        
        # 7. Recommandations
        verification_results["recommendations"] = []
        
        if verification_results["verification_status"] == "FAILED":
            verification_results["recommendations"].append("Importer à nouveau la recette")
        
        if verification_results["issues"]:
            verification_results["recommendations"].append("Corriger les problèmes identifiés")
        
        if verification_results["score"] < 90:
            verification_results["recommendations"].append("Améliorer la qualité des données")
        
        # Affichage résumé
        print(f"   🎯 Score: {verification_results['score']}/100")
        print(f"   📊 Statut: {verification_results['verification_status']}")
        print(f"   🐛 Problèmes: {len(verification_results['issues'])}")
        print(f"   💡 Recommandations: {len(verification_results['recommendations'])}")
        
        return verification_results
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Erreur vérification: {str(e)}",
            "verification_status": "FAILED",
            "score": 0
        }
        print(f"   ❌ Exception: {e}")
        return error_result

def quick_verify(recipe_slug: str) -> bool:
    """
    Vérification rapide (existence seulement)
    
    Args:
        recipe_slug: Slug de la recette
        
    Returns:
        bool: True si importé correctement
    """
    result = verify_import(recipe_slug)
    return result.get("verification_status") == "PASSED"

# Test de la fonction
if __name__ == "__main__":
    print("🧪 TEST VERIFY IMPORT")
    print("=" * 30)
    
    # Test 1: Vérification d'une recette existante
    print("\n1. TEST VÉRIFICATION RECETTE EXISTANTE")
    
    # D'abord lister les recettes pour en trouver une
    try:
        from mcp_auth_wrapper import mcp3_list_recipes
        recipes = mcp3_list_recipes()
        
        if recipes:
            test_slug = recipes[0].get("slug", "")
            print(f"Test avec: {test_slug}")
            
            result1 = verify_import(test_slug)
            print(f"Résultat: {result1.get('verification_status', 'N/A')}")
        else:
            print("Aucune recette disponible pour le test")
            
    except Exception as e:
        print(f"Erreur test: {e}")
    
    # Test 2: Vérification d'une recette inexistante
    print("\n2. TEST VÉRIFICATION RECETTE INEXISTANTE")
    result2 = verify_import("recipe-inexistante-12345")
    print(f"Résultat: {result2.get('verification_status', 'N/A')}")
    
    # Test 3: Vérification avec données attendues
    print("\n3. TEST VÉRIFICATION AVEC DONNÉES ATTENDUES")
    if recipes:
        test_slug = recipes[0].get("slug", "")
        expected_data = {
            "name": recipes[0].get("name", ""),
            "ingredients": ["Ingrédient 1", "Ingrédient 2"],
            "instructions": ["Étape 1", "Étape 2"]
        }
        
        result3 = verify_import(test_slug, expected_data)
        print(f"Résultat: {result3.get('verification_status', 'N/A')}")
    
    print("\n✅ Tests terminés")
