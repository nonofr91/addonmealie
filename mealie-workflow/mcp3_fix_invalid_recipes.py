#!/usr/bin/env python3
"""
MCP3 FIX INVALID RECIPES
Outil MCP pour corriger les recettes invalides
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, List

def fix_invalid_recipes(recipe_slugs: List[str] = None, auto_fix: bool = False) -> Dict[str, Any]:
    """
    Corrige les recettes invalides
    
    Args:
        recipe_slugs: Liste des slugs de recettes à corriger (None = toutes)
        auto_fix: Si True, applique les corrections automatiquement
        
    Returns:
        Dict avec résultats des corrections
    """
    try:
        print(f"🔧 Correction des recettes invalides")
        print(f"   🎯 Mode: {'AUTOMATIQUE' if auto_fix else 'ANALYSE SEULEMENT'}")
        
        # Charger la configuration Mealie
        config_path = "config/mealie_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            return {
                "success": False,
                "error": "Configuration Mealie non trouvée",
                "fix_status": "FAILED"
            }
        
        api_url = config.get("mealie_api", {}).get("url", "")
        token = config.get("mealie_api", {}).get("token", "")
        
        if not api_url or not token:
            return {
                "success": False,
                "error": "Configuration API manquante",
                "fix_status": "FAILED"
            }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 1. Obtenir les recettes à analyser
        if recipe_slugs:
            recipes_to_check = recipe_slugs
            print(f"   📋 Recettes spécifiées: {len(recipes_to_check)}")
        else:
            # Récupérer toutes les recettes
            print(f"   📋 Récupération de toutes les recettes...")
            response = requests.get(f"{api_url}/recipes", headers=headers, timeout=10)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Impossible de récupérer les recettes (HTTP {response.status_code})",
                    "fix_status": "FAILED"
                }
            
            all_recipes = response.json()
            recipes_to_check = [recipe.get("slug", "") for recipe in all_recipes]
            print(f"   📊 {len(recipes_to_check)} recettes trouvées")
        
        # 2. Analyser chaque recette
        fix_results = {
            "fix_id": f"fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "auto_fix": auto_fix,
            "total_recipes": len(recipes_to_check),
            "invalid_recipes": [],
            "fixable_recipes": [],
            "unfixable_recipes": [],
            "fixed_recipes": [],
            "errors": [],
            "fix_status": "COMPLETED"
        }
        
        print(f"\n🔍 Analyse des recettes...")
        
        for i, slug in enumerate(recipes_to_check, 1):
            if not slug:
                continue
                
            print(f"   📋 {i}/{len(recipes_to_check)}: {slug}")
            
            try:
                # Récupérer les détails de la recette
                response = requests.get(f"{api_url}/recipes/{slug}", headers=headers, timeout=5)
                
                if response.status_code != 200:
                    print(f"      ❌ Recette non trouvée")
                    continue
                
                recipe = response.json()
                
                # Analyser les problèmes
                issues = analyze_recipe_issues(recipe)
                
                if not issues["has_issues"]:
                    print(f"      ✅ Recette valide")
                    continue
                
                print(f"      🐛 {len(issues['problems'])} problèmes trouvés")
                
                invalid_recipe_info = {
                    "slug": slug,
                    "name": recipe.get("name", ""),
                    "issues": issues,
                    "fixes_applied": []
                }
                
                # Déterminer si la recette est corrigeable
                if issues["is_fixable"]:
                    print(f"      🔧 Corrigeable: {issues['fixable_problems']}/{len(issues['problems'])}")
                    
                    fix_results["fixable_recipes"].append(invalid_recipe_info)
                    
                    # Appliquer les corrections si mode auto
                    if auto_fix:
                        fixes = apply_recipe_fixes(recipe, issues["fixes"])
                        
                        if fixes["success"]:
                            # Mettre à jour la recette
                            update_response = requests.patch(
                                f"{api_url}/recipes/{slug}",
                                headers=headers,
                                json=fixes["updated_data"],
                                timeout=10
                            )
                            
                            if update_response.status_code == 200:
                                print(f"         ✅ Corrections appliquées")
                                invalid_recipe_info["fixes_applied"] = fixes["applied_fixes"]
                                fix_results["fixed_recipes"].append(invalid_recipe_info)
                            else:
                                error_msg = f"Erreur mise à jour: HTTP {update_response.status_code}"
                                print(f"         ❌ {error_msg}")
                                fix_results["errors"].append(f"{slug}: {error_msg}")
                        else:
                            error_msg = f"Erreur corrections: {fixes.get('error', 'Inconnue')}"
                            print(f"         ❌ {error_msg}")
                            fix_results["errors"].append(f"{slug}: {error_msg}")
                else:
                    print(f"      ❌ Non corrigeable: problèmes critiques")
                    fix_results["unfixable_recipes"].append(invalid_recipe_info)
                
                fix_results["invalid_recipes"].append(invalid_recipe_info)
                
            except Exception as e:
                error_msg = f"Exception analyse {slug}: {str(e)}"
                print(f"      💥 {error_msg}")
                fix_results["errors"].append(error_msg)
        
        # 3. Résumé final
        print(f"\n🎯 RÉSUMÉ CORRECTIONS")
        print(f"   📊 Recettes analysées: {fix_results['total_recipes']}")
        print(f"   🐛 Recettes invalides: {len(fix_results['invalid_recipes'])}")
        print(f"   🔧 Recettes corrigeables: {len(fix_results['fixable_recipes'])}")
        print(f"   ❌ Recettes non corrigeables: {len(fix_results['unfixable_recipes'])}")
        print(f"   ✅ Recettes corrigées: {len(fix_results['fixed_recipes'])}")
        print(f"   🐛 Erreurs: {len(fix_results['errors'])}")
        
        return fix_results
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Erreur correction recettes: {str(e)}",
            "fix_status": "FAILED"
        }
        print(f"💥 Exception globale: {e}")
        return error_result

def analyze_recipe_issues(recipe: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyse les problèmes d'une recette
    
    Args:
        recipe: Données de la recette
        
    Returns:
        Dict avec l'analyse des problèmes
    """
    issues = {
        "has_issues": False,
        "is_fixable": True,
        "problems": [],
        "fixes": [],
        "fixable_problems": 0
    }
    
    # 1. Vérifier le nom
    name = recipe.get("name", "").strip()
    if not name:
        issues["problems"].append("Nom manquant")
        issues["fixes"].append({
            "problem": "Nom manquant",
            "fix": "Ajouter un nom générique",
            "action": "set_name",
            "value": "Recette sans nom"
        })
        issues["fixable_problems"] += 1
    elif len(name) < 3:
        issues["problems"].append("Nom trop court")
        issues["fixes"].append({
            "problem": "Nom trop court",
            "fix": "Améliorer le nom",
            "action": "set_name",
            "value": f"Recette {name.title()}"
        })
        issues["fixable_problems"] += 1
    
    # 2. Vérifier les ingrédients
    ingredients = recipe.get("recipeIngredient", [])
    if not ingredients:
        issues["problems"].append("Aucun ingrédient")
        issues["fixes"].append({
            "problem": "Aucun ingrédient",
            "fix": "Ajouter ingrédient générique",
            "action": "set_ingredients",
            "value": ["Ingrédient 1", "Ingrédient 2"]
        })
        issues["fixable_problems"] += 1
    else:
        # Vérifier les ingrédients vides
        valid_ingredients = []
        for ingredient in ingredients:
            if isinstance(ingredient, str) and len(ingredient.strip()) > 2:
                valid_ingredients.append(ingredient.strip())
        
        if len(valid_ingredients) < len(ingredients):
            issues["problems"].append(f"{len(ingredients) - len(valid_ingredients)} ingrédients invalides")
            issues["fixes"].append({
                "problem": "Ingrédients invalides",
                "fix": "Nettoyer les ingrédients",
                "action": "set_ingredients",
                "value": valid_ingredients if valid_ingredients else ["Ingrédient par défaut"]
            })
            issues["fixable_problems"] += 1
    
    # 3. Vérifier les instructions
    instructions = recipe.get("recipeInstructions", [])
    if not instructions:
        issues["problems"].append("Aucune instruction")
        issues["fixes"].append({
            "problem": "Aucune instruction",
            "fix": "Ajouter instruction générique",
            "action": "set_instructions",
            "value": ["Préparer les ingrédients", "Cuire selon les instructions"]
        })
        issues["fixable_problems"] += 1
    else:
        # Vérifier les instructions vides
        valid_instructions = []
        for instruction in instructions:
            if isinstance(instruction, str) and len(instruction.strip()) > 5:
                valid_instructions.append(instruction.strip())
        
        if len(valid_instructions) < len(instructions):
            issues["problems"].append(f"{len(instructions) - len(valid_instructions)} instructions invalides")
            issues["fixes"].append({
                "problem": "Instructions invalides",
                "fix": "Nettoyer les instructions",
                "action": "set_instructions",
                "value": valid_instructions if valid_instructions else ["Préparer", "Cuire"]
            })
            issues["fixable_problems"] += 1
    
    # 4. Vérifier les portions
    servings = recipe.get("recipeServings")
    if not servings:
        issues["problems"].append("Portions non spécifiées")
        issues["fixes"].append({
            "problem": "Portions non spécifiées",
            "fix": "Définir portions par défaut",
            "action": "set_servings",
            "value": 4
        })
        issues["fixable_problems"] += 1
    
    # 5. Vérifier la description
    description = recipe.get("description", "").strip()
    if not description:
        issues["problems"].append("Aucune description")
        issues["fixes"].append({
            "problem": "Aucune description",
            "fix": "Ajouter description générique",
            "action": "set_description",
            "value": "Recette délicieuse et facile à préparer"
        })
        issues["fixable_problems"] += 1
    
    # Déterminer si la recette a des problèmes
    issues["has_issues"] = len(issues["problems"]) > 0
    
    # Déterminer si c'est corrigeable (tous les problèmes sont corrigeables pour l'instant)
    issues["is_fixable"] = issues["has_issues"]  # Tous les problèmes sont corrigeables
    
    return issues

def apply_recipe_fixes(recipe: Dict[str, Any], fixes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Applique les corrections à une recette
    
    Args:
        recipe: Recette originale
        fixes: Liste des corrections à appliquer
        
    Returns:
        Dict avec résultats des corrections
    """
    try:
        updated_data = recipe.copy()
        applied_fixes = []
        
        for fix in fixes:
            action = fix.get("action")
            value = fix.get("value")
            
            if action == "set_name":
                updated_data["name"] = value
                applied_fixes.append(f"Nom défini: {value}")
            
            elif action == "set_ingredients":
                updated_data["recipeIngredient"] = value
                applied_fixes.append(f"Ingrédients définis: {len(value)}")
            
            elif action == "set_instructions":
                updated_data["recipeInstructions"] = value
                applied_fixes.append(f"Instructions définies: {len(value)}")
            
            elif action == "set_servings":
                updated_data["recipeServings"] = value
                applied_fixes.append(f"Portions définies: {value}")
            
            elif action == "set_description":
                updated_data["description"] = value
                applied_fixes.append(f"Description définie")
        
        return {
            "success": True,
            "updated_data": updated_data,
            "applied_fixes": applied_fixes
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "applied_fixes": []
        }

def quick_fix_check() -> Dict[str, Any]:
    """
    Vérification rapide des recettes invalides (analyse seulement)
    
    Returns:
        Dict avec résultats simplifiés
    """
    result = fix_invalid_recipes(auto_fix=False)
    
    return {
        "total_recipes": result.get("total_recipes", 0),
        "invalid_recipes": len(result.get("invalid_recipes", [])),
        "fixable_recipes": len(result.get("fixable_recipes", [])),
        "unfixable_recipes": len(result.get("unfixable_recipes", []))
    }

# Test de la fonction
if __name__ == "__main__":
    print("🧪 TEST FIX INVALID RECIPES")
    print("=" * 30)
    
    # Test 1: Analyse seulement
    print("\n1. TEST ANALYSE SEULEMENT")
    result1 = fix_invalid_recipes(auto_fix=False)
    
    print(f"Résultat: {result1.get('fix_status', 'N/A')}")
    print(f"Recettes invalides: {len(result1.get('invalid_recipes', []))}")
    print(f"Recettes corrigeables: {len(result1.get('fixable_recipes', []))}")
    
    # Test 2: Vérification rapide
    print("\n2. TEST VÉRIFICATION RAPIDE")
    quick_result = quick_fix_check()
    
    print(f"Total recettes: {quick_result['total_recipes']}")
    print(f"Invalides: {quick_result['invalid_recipes']}")
    print(f"Corrigeables: {quick_result['fixable_recipes']}")
    
    # Test 3: Test sur recettes spécifiques (si disponibles)
    print("\n3. TEST RECETTES SPÉCIFIQUES")
    try:
        from mcp_auth_wrapper import mcp3_list_recipes
        recipes = mcp3_list_recipes()
        
        if recipes:
            # Prendre les 2 premières recettes
            test_slugs = [recipes[0].get("slug", ""), recipes[1].get("slug", "")] if len(recipes) >= 2 else [recipes[0].get("slug", "")]
            
            print(f"Test sur: {test_slugs}")
            result3 = fix_invalid_recipes(recipe_slugs=test_slugs, auto_fix=False)
            
            print(f"Invalides trouvées: {len(result3.get('invalid_recipes', []))}")
        else:
            print("Aucune recette disponible")
            
    except Exception as e:
        print(f"Erreur test spécifique: {e}")
    
    print("\n✅ Tests terminés")
