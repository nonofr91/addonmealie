#!/usr/bin/env python3
"""
MCP3 CLEANUP DUPLICATES
Outil MCP pour nettoyer les recettes en double
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, List, Tuple
from difflib import SequenceMatcher

def cleanup_duplicates(dry_run: bool = True, similarity_threshold: float = 0.8) -> Dict[str, Any]:
    """
    Nettoie les recettes en double
    
    Args:
        dry_run: Si True, simule seulement sans supprimer
        similarity_threshold: Seuil de similarité (0.0-1.0)
        
    Returns:
        Dict avec résultats du nettoyage
    """
    try:
        print(f"🧹 Nettoyage des doublons")
        print(f"   🔍 Mode: {'SIMULATION' if dry_run else 'RÉEL'}")
        print(f"   📊 Seuil similarité: {similarity_threshold}")
        
        # Charger la configuration Mealie
        config_path = "config/mealie_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            return {
                "success": False,
                "error": "Configuration Mealie non trouvée",
                "cleanup_status": "FAILED"
            }
        
        api_url = config.get("mealie_api", {}).get("url", "")
        token = config.get("mealie_api", {}).get("token", "")
        
        if not api_url or not token:
            return {
                "success": False,
                "error": "Configuration API manquante",
                "cleanup_status": "FAILED"
            }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 1. Récupérer toutes les recettes
        print(f"\n📋 Récupération des recettes...")
        response = requests.get(f"{api_url}/recipes", headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Impossible de récupérer les recettes (HTTP {response.status_code})",
                "cleanup_status": "FAILED"
            }
        
        all_recipes = response.json()
        print(f"   📊 {len(all_recipes)} recettes trouvées")
        
        # 2. Analyser les doublons potentiels
        print(f"\n🔍 Analyse des doublons...")
        duplicates_groups = []
        processed_recipes = set()
        
        for i, recipe1 in enumerate(all_recipes):
            if i in processed_recipes:
                continue
                
            name1 = recipe1.get("name", "").lower().strip()
            if not name1:
                continue
                
            current_group = [i]
            processed_recipes.add(i)
            
            # Comparer avec les autres recettes
            for j, recipe2 in enumerate(all_recipes[i+1:], i+1):
                if j in processed_recipes:
                    continue
                    
                name2 = recipe2.get("name", "").lower().strip()
                if not name2:
                    continue
                
                # Calculer la similarité des noms
                similarity = SequenceMatcher(None, name1, name2).ratio()
                
                if similarity >= similarity_threshold:
                    current_group.append(j)
                    processed_recipes.add(j)
            
            # Ajouter le groupe s'il contient des doublons
            if len(current_group) > 1:
                group_recipes = [all_recipes[idx] for idx in current_group]
                duplicates_groups.append({
                    "group_id": len(duplicates_groups) + 1,
                    "recipes": group_recipes,
                    "similarity_scores": []
                })
                
                # Calculer les similarités dans le groupe
                for k in range(len(current_group)):
                    for l in range(k+1, len(current_group)):
                        idx1, idx2 = current_group[k], current_group[l]
                        name1 = all_recipes[idx1].get("name", "").lower()
                        name2 = all_recipes[idx2].get("name", "").lower()
                        similarity = SequenceMatcher(None, name1, name2).ratio()
                        
                        duplicates_groups[-1]["similarity_scores"].append({
                            "recipe1_idx": idx1,
                            "recipe2_idx": idx2,
                            "similarity": similarity
                        })
        
        print(f"   🔍 {len(duplicates_groups)} groupes de doublons trouvés")
        
        # 3. Analyser chaque groupe pour déterminer les recettes à conserver
        cleanup_results = {
            "cleanup_id": f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "dry_run": dry_run,
            "similarity_threshold": similarity_threshold,
            "total_recipes": len(all_recipes),
            "duplicate_groups": len(duplicates_groups),
            "groups_processed": 0,
            "recipes_to_delete": [],
            "recipes_to_keep": [],
            "errors": [],
            "cleanup_status": "COMPLETED"
        }
        
        print(f"\n📋 Analyse des groupes de doublons:")
        
        for group in duplicates_groups:
            group_id = group["group_id"]
            recipes = group["recipes"]
            
            print(f"\n   📦 Groupe {group_id} ({len(recipes)} recettes)")
            
            # Analyser la qualité de chaque recette du groupe
            recipe_qualities = []
            
            for recipe in recipes:
                slug = recipe.get("slug", "")
                
                # Obtenir les détails complets
                try:
                    detail_response = requests.get(f"{api_url}/recipes/{slug}", headers=headers, timeout=5)
                    if detail_response.status_code == 200:
                        details = detail_response.json()
                        
                        # Calculer un score de qualité simple
                        quality_score = 0
                        
                        # Nom
                        name = details.get("name", "")
                        if len(name) > 5:
                            quality_score += 20
                        
                        # Ingrédients
                        ingredients = details.get("recipeIngredient", [])
                        if len(ingredients) >= 3:
                            quality_score += 30
                        
                        # Instructions
                        instructions = details.get("recipeInstructions", [])
                        if len(instructions) >= 2:
                            quality_score += 30
                        
                        # Description
                        description = details.get("description", "")
                        if len(description) > 20:
                            quality_score += 20
                        
                        recipe_qualities.append({
                            "recipe": recipe,
                            "details": details,
                            "quality_score": quality_score
                        })
                        
                    else:
                        recipe_qualities.append({
                            "recipe": recipe,
                            "details": {},
                            "quality_score": 0
                        })
                        
                except Exception as e:
                    recipe_qualities.append({
                        "recipe": recipe,
                        "details": {},
                        "quality_score": 0,
                        "error": str(e)
                    })
            
            # Trier par qualité (meilleure en premier)
            recipe_qualities.sort(key=lambda x: x["quality_score"], reverse=True)
            
            # Garder la meilleure recette, marquer les autres pour suppression
            best_recipe = recipe_qualities[0]
            recipes_to_delete = recipe_qualities[1:]
            
            print(f"      ✅ À conserver: {best_recipe['recipe'].get('name', 'N/A')} (score: {best_recipe['quality_score']})")
            
            for recipe_info in recipes_to_delete:
                recipe_name = recipe_info['recipe'].get('name', 'N/A')
                recipe_score = recipe_info['quality_score']
                print(f"         ❌ À supprimer: {recipe_name} (score: {recipe_score})")
                
                cleanup_results["recipes_to_delete"].append({
                    "group_id": group_id,
                    "recipe": recipe_info["recipe"],
                    "reason": "Duplicate (lower quality)",
                    "quality_score": recipe_score,
                    "kept_recipe": best_recipe["recipe"]
                })
            
            cleanup_results["recipes_to_keep"].append(best_recipe["recipe"])
            cleanup_results["groups_processed"] += 1
        
        # 4. Exécuter le nettoyage (si pas en mode dry_run)
        if not dry_run and cleanup_results["recipes_to_delete"]:
            print(f"\n🗑️ Suppression des {len(cleanup_results['recipes_to_delete'])} recettes...")
            
            deleted_count = 0
            for delete_info in cleanup_results["recipes_to_delete"]:
                recipe = delete_info["recipe"]
                slug = recipe.get("slug", "")
                name = recipe.get("name", "N/A")
                
                try:
                    delete_response = requests.delete(f"{api_url}/recipes/{slug}", headers=headers, timeout=10)
                    
                    if delete_response.status_code in [200, 204]:
                        print(f"   ✅ Supprimé: {name}")
                        deleted_count += 1
                    else:
                        error_msg = f"Erreur suppression {name}: HTTP {delete_response.status_code}"
                        print(f"   ❌ {error_msg}")
                        cleanup_results["errors"].append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Exception suppression {name}: {str(e)}"
                    print(f"   💥 {error_msg}")
                    cleanup_results["errors"].append(error_msg)
            
            cleanup_results["deleted_count"] = deleted_count
        else:
            cleanup_results["deleted_count"] = 0
            if dry_run:
                print(f"\n🔍 MODE SIMULATION: {len(cleanup_results['recipes_to_delete'])} recettes seraient supprimées")
        
        # 5. Résumé final
        cleanup_results["final_recipe_count"] = cleanup_results["total_recipes"] - cleanup_results["deleted_count"]
        cleanup_results["space_saved"] = cleanup_results["deleted_count"]
        
        print(f"\n🎯 RÉSUMÉ NETTOYAGE")
        print(f"   📊 Recettes initiales: {cleanup_results['total_recipes']}")
        print(f"   📦 Groupes de doublons: {cleanup_results['duplicate_groups']}")
        print(f"   ✅ Recettes conservées: {len(cleanup_results['recipes_to_keep'])}")
        print(f"   ❌ Recettes à supprimer: {len(cleanup_results['recipes_to_delete'])}")
        print(f"   🗑️ Recettes supprimées: {cleanup_results['deleted_count']}")
        print(f"   📊 Recettes finales: {cleanup_results['final_recipe_count']}")
        print(f"   💰 Espace économisé: {cleanup_results['space_saved']} recettes")
        print(f"   🐛 Erreurs: {len(cleanup_results['errors'])}")
        
        return cleanup_results
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Erreur nettoyage doublons: {str(e)}",
            "cleanup_status": "FAILED"
        }
        print(f"💥 Exception globale: {e}")
        return error_result

def quick_cleanup_check() -> Dict[str, Any]:
    """
    Vérification rapide des doublons (dry run)
    
    Returns:
        Dict avec résultats simplifiés
    """
    result = cleanup_duplicates(dry_run=True, similarity_threshold=0.8)
    
    return {
        "total_recipes": result.get("total_recipes", 0),
        "duplicate_groups": result.get("duplicate_groups", 0),
        "recipes_to_delete": len(result.get("recipes_to_delete", [])),
        "space_saved": len(result.get("recipes_to_delete", []))
    }

# Test de la fonction
if __name__ == "__main__":
    print("🧪 TEST CLEANUP DUPLICATES")
    print("=" * 30)
    
    # Test 1: Simulation de nettoyage
    print("\n1. TEST SIMULATION NETTOYAGE")
    result1 = cleanup_duplicates(dry_run=True, similarity_threshold=0.8)
    
    print(f"Résultat: {result1.get('cleanup_status', 'N/A')}")
    print(f"Groupes trouvés: {result1.get('duplicate_groups', 0)}")
    print(f"Recettes à supprimer: {len(result1.get('recipes_to_delete', []))}")
    
    # Test 2: Vérification rapide
    print("\n2. TEST VÉRIFICATION RAPIDE")
    quick_result = quick_cleanup_check()
    
    print(f"Total recettes: {quick_result['total_recipes']}")
    print(f"Groupes doublons: {quick_result['duplicate_groups']}")
    print(f"Recettes à supprimer: {quick_result['recipes_to_delete']}")
    
    # Test 3: Simulation avec seuil différent
    print("\n3. TEST SEUIL SIMILARITÉ DIFFÉRENT")
    result3 = cleanup_duplicates(dry_run=True, similarity_threshold=0.9)
    
    print(f"Seuil 0.9 - Groupes: {result3.get('duplicate_groups', 0)}")
    print(f"Seuil 0.9 - À supprimer: {len(result3.get('recipes_to_delete', []))}")
    
    print("\n✅ Tests terminés")
