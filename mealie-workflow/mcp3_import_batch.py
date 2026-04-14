#!/usr/bin/env python3
"""
MCP3 IMPORT BATCH
Outil MCP pour importer plusieurs recettes en lot
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, List

def import_batch(recipes_list: List[Dict[str, Any]], batch_size: int = 5, delay: float = 1.0) -> Dict[str, Any]:
    """
    Importe plusieurs recettes en lot
    
    Args:
        recipes_list: Liste de recettes à importer
        batch_size: Taille des lots
        delay: Délai entre les imports (secondes)
        
    Returns:
        Dict avec résultats de l'import par lot
    """
    try:
        print(f"🚀 Import par lot: {len(recipes_list)} recettes")
        print(f"   📦 Taille des lots: {batch_size}")
        print(f"   ⏱️ Délai: {delay}s entre les imports")
        
        # Charger la configuration Mealie
        config_path = "config/mealie_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            return {
                "success": False,
                "error": "Configuration Mealie non trouvée",
                "batch_status": "FAILED"
            }
        
        api_url = config.get("mealie_api", {}).get("url", "")
        token = config.get("mealie_api", {}).get("token", "")
        
        if not api_url or not token:
            return {
                "success": False,
                "error": "Configuration API manquante",
                "batch_status": "FAILED"
            }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Résultats de l'import par lot
        batch_results = {
            "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "total_recipes": len(recipes_list),
            "batch_size": batch_size,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "successful_imports": [],
            "failed_imports": [],
            "skipped_imports": [],
            "batch_status": "IN_PROGRESS",
            "statistics": {
                "total_processed": 0,
                "success_count": 0,
                "failure_count": 0,
                "skip_count": 0,
                "success_rate": 0.0
            },
            "errors": []
        }
        
        # Diviser en lots
        total_batches = (len(recipes_list) + batch_size - 1) // batch_size
        
        print(f"   📊 Total lots: {total_batches}")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(recipes_list))
            current_batch = recipes_list[start_idx:end_idx]
            
            print(f"\n📦 Lot {batch_num + 1}/{total_batches} ({len(current_batch)} recettes)")
            
            # Traiter chaque recette du lot
            for i, recipe in enumerate(current_batch):
                recipe_index = start_idx + i + 1
                recipe_name = recipe.get("name", f"Recette {recipe_index}")
                
                print(f"   🔄 {recipe_index}/{len(recipes_list)}: {recipe_name}")
                
                try:
                    # Valider la recette avant import
                    from mcp3_validate_recipe import validate_recipe
                    validation_result = validate_recipe(recipe)
                    
                    if not validation_result.get("is_valid", False):
                        print(f"      ❌ Validation échouée - Import ignoré")
                        batch_results["skipped_imports"].append({
                            "index": recipe_index,
                            "name": recipe_name,
                            "reason": "Validation échouée",
                            "validation_errors": validation_result.get("errors", [])
                        })
                        batch_results["statistics"]["skip_count"] += 1
                        continue
                    
                    # Préparer le payload pour l'API
                    payload = {
                        "name": recipe.get("name", "Recette sans nom"),
                        "description": recipe.get("description", ""),
                        "recipeIngredient": recipe.get("ingredients", []),
                        "recipeInstructions": recipe.get("instructions", []),
                        "recipeServings": recipe.get("servings", 4),
                        "prepTime": f"PT{recipe.get('prep_time', '15')}M",
                        "cookTime": f"PT{recipe.get('cook_time', '30')}M",
                        "totalTime": f"PT{recipe.get('total_time', '45')}M",
                        "recipeCategory": recipe.get("categories", []),
                        "tags": recipe.get("tags", []),
                        "image": recipe.get("image", "")
                    }
                    
                    # Importer la recette
                    response = requests.post(f"{api_url}/recipes", headers=headers, json=payload, timeout=10)
                    
                    if response.status_code in [200, 201]:
                        result = response.json()
                        recipe_id = result.get("id", "unknown")
                        
                        print(f"      ✅ Importé (ID: {recipe_id})")
                        
                        batch_results["successful_imports"].append({
                            "index": recipe_index,
                            "name": recipe_name,
                            "recipe_id": recipe_id,
                            "validation_score": validation_result.get("score", 0),
                            "import_time": datetime.now().isoformat()
                        })
                        batch_results["statistics"]["success_count"] += 1
                        
                        # Vérifier l'import
                        if recipe_id != "unknown":
                            from mcp3_verify_import import verify_import
                            verify_result = verify_import(recipe_id, recipe)
                            
                            if verify_result.get("verification_status") != "PASSED":
                                print(f"      ⚠️ Import réussi mais vérification échouée")
                                batch_results["errors"].append({
                                    "recipe_name": recipe_name,
                                    "error": "Vérification échouée",
                                    "details": verify_result.get("issues", [])
                                })
                        
                    else:
                        error_msg = f"HTTP {response.status_code}"
                        if response.text:
                            error_msg += f": {response.text[:100]}"
                        
                        print(f"      ❌ Erreur import: {error_msg}")
                        
                        batch_results["failed_imports"].append({
                            "index": recipe_index,
                            "name": recipe_name,
                            "error": error_msg,
                            "http_status": response.status_code
                        })
                        batch_results["statistics"]["failure_count"] += 1
                        batch_results["errors"].append({
                            "recipe_name": recipe_name,
                            "error": error_msg
                        })
                    
                    batch_results["statistics"]["total_processed"] += 1
                    
                    # Délai entre les imports
                    if delay > 0 and i < len(current_batch) - 1:
                        time.sleep(delay)
                
                except Exception as e:
                    print(f"      💥 Exception: {e}")
                    
                    batch_results["failed_imports"].append({
                        "index": recipe_index,
                        "name": recipe_name,
                        "error": f"Exception: {str(e)}"
                    })
                    batch_results["statistics"]["failure_count"] += 1
                    batch_results["statistics"]["total_processed"] += 1
                    batch_results["errors"].append({
                        "recipe_name": recipe_name,
                        "error": f"Exception: {str(e)}"
                    })
            
            # Délai entre les lots
            if batch_num < total_batches - 1 and delay > 0:
                print(f"   ⏱️ Pause de {delay}s avant le lot suivant...")
                time.sleep(delay * 2)  # Pause plus longue entre les lots
        
        # Finaliser les résultats
        batch_results["end_time"] = datetime.now().isoformat()
        batch_results["batch_status"] = "COMPLETED"
        
        # Calculer le taux de succès
        total = batch_results["statistics"]["total_processed"]
        success = batch_results["statistics"]["success_count"]
        if total > 0:
            batch_results["statistics"]["success_rate"] = (success / total) * 100
        
        # Afficher le résumé
        print(f"\n🎯 RÉSUMÉ IMPORT PAR LOT")
        print(f"   📊 Total traitées: {batch_results['statistics']['total_processed']}/{batch_results['total_recipes']}")
        print(f"   ✅ Succès: {batch_results['statistics']['success_count']}")
        print(f"   ❌ Échecs: {batch_results['statistics']['failure_count']}")
        print(f"   ⏭️ Ignorées: {batch_results['statistics']['skip_count']}")
        print(f"   📈 Taux de succès: {batch_results['statistics']['success_rate']:.1f}%")
        
        # Statut final
        if batch_results["statistics"]["success_rate"] >= 80:
            batch_results["batch_status"] = "SUCCESS"
        elif batch_results["statistics"]["success_rate"] >= 60:
            batch_results["batch_status"] = "PARTIAL"
        else:
            batch_results["batch_status"] = "FAILED"
        
        print(f"   🎉 Statut final: {batch_results['batch_status']}")
        
        return batch_results
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Erreur import par lot: {str(e)}",
            "batch_status": "FAILED"
        }
        print(f"💥 Exception globale: {e}")
        return error_result

def quick_batch_import(recipes_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Import par lot rapide avec paramètres par défaut
    
    Args:
        recipes_list: Liste de recettes à importer
        
    Returns:
        Dict avec résultats simplifiés
    """
    return import_batch(recipes_list, batch_size=3, delay=0.5)

# Test de la fonction
if __name__ == "__main__":
    print("🧪 TEST IMPORT BATCH")
    print("=" * 30)
    
    # Créer des recettes de test
    test_recipes = [
        {
            "name": "Test Batch 1 - Quiche",
            "description": "Première recette de test batch",
            "ingredients": ["200g lardons", "4 œufs", "40cl crème", "1 pâte"],
            "instructions": ["Préparer pâte", "Mélanger appareil", "Cuire 40min"],
            "servings": 6,
            "prep_time": "15",
            "cook_time": "40"
        },
        {
            "name": "Test Batch 2 - Tarte",
            "description": "Deuxième recette de test batch",
            "ingredients": ["1kg pommes", "200g sucre", "1 pâte sablée"],
            "instructions": ["Peler pommes", "Caraméliser", "Cuire 45min"],
            "servings": 8,
            "prep_time": "20",
            "cook_time": "45"
        },
        {
            "name": "Test Batch 3 - Gâteau",
            "description": "Troisième recette de test batch",
            "ingredients": ["200g farine", "200g sucre", "4 œufs", "100g beurre"],
            "instructions": ["Mélanger ingrédients", "Verser moule", "Cuire 30min"],
            "servings": 4,
            "prep_time": "10",
            "cook_time": "30"
        },
        {
            "name": "Test Batch 4 - Salade",
            "description": "Quatrième recette de test batch",
            "ingredients": ["1 laitue", "2 tomates", "1 concombre", "vinaigrette"],
            "instructions": ["Laver légumes", "Couper", "Assaisonner"],
            "servings": 2,
            "prep_time": "10",
            "cook_time": "0"
        },
        {
            "name": "Test Batch 5 - Soupe",
            "description": "Cinquième recette de test batch",
            "ingredients": ["1kg carottes", "1 oignon", "1L bouillon", "crème"],
            "instructions": ["Éplucher légumes", "Cuire 30min", "Mix"],
            "servings": 4,
            "prep_time": "15",
            "cook_time": "30"
        }
    ]
    
    print(f"\n🚀 Test avec {len(test_recipes)} recettes")
    
    # Test import par lot
    result = import_batch(test_recipes, batch_size=2, delay=0.5)
    
    print(f"\n📊 Résultat final: {result.get('batch_status', 'N/A')}")
    print(f"🎯 Taux de succès: {result.get('statistics', {}).get('success_rate', 0):.1f}%")
    
    print("\n✅ Test terminé")
