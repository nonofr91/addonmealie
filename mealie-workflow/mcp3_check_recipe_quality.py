#!/usr/bin/env python3
"""
MCP3 CHECK RECIPE QUALITY
Outil MCP pour analyser la qualité d'une recette existante
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, List
from collections import Counter

def check_recipe_quality(recipe_slug: str) -> Dict[str, Any]:
    """
    Analyse la qualité d'une recette existante
    
    Args:
        recipe_slug: Slug de la recette à analyser
        
    Returns:
        Dict avec résultats d'analyse de qualité
    """
    try:
        print(f"🔍 Analyse qualité: {recipe_slug}")
        
        # Charger la configuration Mealie
        config_path = "config/mealie_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            return {
                "success": False,
                "error": "Configuration Mealie non trouvée",
                "quality_status": "FAILED"
            }
        
        api_url = config.get("mealie_api", {}).get("url", "")
        token = config.get("mealie_api", {}).get("token", "")
        
        if not api_url or not token:
            return {
                "success": False,
                "error": "Configuration API manquante",
                "quality_status": "FAILED"
            }
        
        # Récupérer les détails de la recette
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{api_url}/recipes/{recipe_slug}", headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Recette non trouvée (HTTP {response.status_code})",
                "quality_status": "FAILED"
            }
        
        recipe = response.json()
        
        # Analyse de qualité
        quality_analysis = {
            "recipe_slug": recipe_slug,
            "recipe_name": recipe.get("name", ""),
            "analysis_timestamp": datetime.now().isoformat(),
            "quality_status": "GOOD",
            "overall_score": 100,
            "categories": {},
            "issues": [],
            "recommendations": [],
            "metrics": {}
        }
        
        print(f"   📖 Recette: {recipe.get('name', 'N/A')}")
        
        # 1. Analyse du nom
        name = recipe.get("name", "").strip()
        name_score = 100
        
        if len(name) < 3:
            quality_analysis["issues"].append("Nom trop court")
            name_score -= 30
        elif len(name) > 100:
            quality_analysis["issues"].append("Nom trop long")
            name_score -= 15
        elif not any(char.isalpha() for char in name):
            quality_analysis["issues"].append("Nom sans lettres")
            name_score -= 25
        
        quality_analysis["categories"]["name_quality"] = {
            "score": name_score,
            "status": "EXCELLENT" if name_score >= 90 else "BON" if name_score >= 70 else "FAIBLE",
            "details": f"Longueur: {len(name)} caractères"
        }
        
        # 2. Analyse des ingrédients
        ingredients = recipe.get("recipeIngredient", [])
        ingredients_score = 100
        
        if not ingredients:
            quality_analysis["issues"].append("Aucun ingrédient")
            ingredients_score -= 100
        else:
            # Nombre d'ingrédients
            if len(ingredients) < 2:
                quality_analysis["issues"].append("Moins de 2 ingrédients")
                ingredients_score -= 30
            elif len(ingredients) > 20:
                quality_analysis["issues"].append("Plus de 20 ingrédients (trop complexe)")
                ingredients_score -= 20
            
            # Qualité des ingrédients
            valid_ingredients = 0
            generic_ingredients = ["sel", "poivre", "eau", "huile", "beurre", "sucre", "farine"]
            generic_count = 0
            
            ingredient_lengths = []
            for ingredient in ingredients:
                if isinstance(ingredient, str) and len(ingredient.strip()) > 2:
                    valid_ingredients += 1
                    ingredient_lengths.append(len(ingredient.strip()))
                    
                    # Vérifier si générique
                    ingredient_lower = ingredient.lower()
                    if any(generic in ingredient_lower for generic in generic_ingredients):
                        generic_count += 1
            
            if valid_ingredients < len(ingredients):
                ingredients_score -= (len(ingredients) - valid_ingredients) * 10
            
            if generic_count > len(ingredients) * 0.3:
                quality_analysis["issues"].append(f"Trop d'ingrédients génériques ({generic_count}/{len(ingredients)})")
                ingredients_score -= generic_count * 5
            
            # Longueur moyenne des ingrédients
            if ingredient_lengths:
                avg_length = sum(ingredient_lengths) / len(ingredient_lengths)
                if avg_length < 10:
                    quality_analysis["issues"].append("Ingrédients trop courts en moyenne")
                    ingredients_score -= 15
            
            quality_analysis["metrics"]["ingredients_stats"] = {
                "total": len(ingredients),
                "valid": valid_ingredients,
                "generic": generic_count,
                "avg_length": sum(ingredient_lengths) / len(ingredient_lengths) if ingredient_lengths else 0
            }
        
        quality_analysis["categories"]["ingredients_quality"] = {
            "score": max(0, ingredients_score),
            "status": "EXCELLENT" if ingredients_score >= 90 else "BON" if ingredients_score >= 70 else "FAIBLE",
            "details": f"{len(ingredients)} ingrédients"
        }
        
        # 3. Analyse des instructions
        instructions = recipe.get("recipeInstructions", [])
        instructions_score = 100
        
        if not instructions:
            quality_analysis["issues"].append("Aucune instruction")
            instructions_score -= 100
        else:
            # Nombre d'instructions
            if len(instructions) < 2:
                quality_analysis["issues"].append("Moins de 2 instructions")
                instructions_score -= 30
            elif len(instructions) > 15:
                quality_analysis["issues"].append("Plus de 15 instructions (trop long)")
                instructions_score -= 20
            
            # Qualité des instructions
            valid_instructions = 0
            instruction_lengths = []
            
            for instruction in instructions:
                if isinstance(instruction, str) and len(instruction.strip()) > 5:
                    valid_instructions += 1
                    instruction_lengths.append(len(instruction.strip()))
            
            if valid_instructions < len(instructions):
                instructions_score -= (len(instructions) - valid_instructions) * 10
            
            # Longueur moyenne des instructions
            if instruction_lengths:
                avg_length = sum(instruction_lengths) / len(instruction_lengths)
                if avg_length < 15:
                    quality_analysis["issues"].append("Instructions trop courtes en moyenne")
                    instructions_score -= 15
                elif avg_length > 200:
                    quality_analysis["issues"].append("Instructions trop longues en moyenne")
                    instructions_score -= 10
            
            # Analyse des mots-clés
            all_instructions_text = " ".join(instructions).lower()
            action_verbs = ["cuire", "préparer", "mélanger", "ajouter", "laisser", "faire", "mettre", "verser"]
            action_count = sum(1 for verb in action_verbs if verb in all_instructions_text)
            
            if action_count < 2:
                quality_analysis["issues"].append("Peu de verbes d'action")
                instructions_score -= 10
            
            quality_analysis["metrics"]["instructions_stats"] = {
                "total": len(instructions),
                "valid": valid_instructions,
                "avg_length": sum(instruction_lengths) / len(instruction_lengths) if instruction_lengths else 0,
                "action_verbs": action_count
            }
        
        quality_analysis["categories"]["instructions_quality"] = {
            "score": max(0, instructions_score),
            "status": "EXCELLENT" if instructions_score >= 90 else "BON" if instructions_score >= 70 else "FAIBLE",
            "details": f"{len(instructions)} instructions"
        }
        
        # 4. Analyse de la description
        description = recipe.get("description", "").strip()
        description_score = 100
        
        if not description:
            quality_analysis["issues"].append("Aucune description")
            description_score -= 40
        elif len(description) < 10:
            quality_analysis["issues"].append("Description trop courte")
            description_score -= 20
        elif len(description) > 500:
            quality_analysis["issues"].append("Description trop longue")
            description_score -= 15
        
        quality_analysis["categories"]["description_quality"] = {
            "score": max(0, description_score),
            "status": "BONNE" if description_score >= 80 else "MOYENNE" if description_score >= 60 else "FAIBLE",
            "details": f"Longueur: {len(description)} caractères"
        }
        
        # 5. Analyse de la cohérence
        coherence_score = 100
        name_lower = name.lower()
        ingredients_text = " ".join(str(ing) for ing in ingredients).lower()
        instructions_text = " ".join(instructions).lower()
        
        # Vérifier la cohérence pour certains types de recettes
        coherence_checks = {
            "quiche": ["lardon", "œuf", "crème", "fromage"],
            "tarte": ["pâte", "farine", "beurre"],
            "bœuf": ["bœuf", "boeuf", "viande"],
            "saumon": ["saumon", "poisson"],
            "chocolat": ["chocolat", "cacao"],
            "salade": ["salade", "laitue", "tomate"],
            "soupe": ["bouillon", "eau", "légumes"]
        }
        
        coherence_found = False
        for recipe_type, required_ingredients in coherence_checks.items():
            if recipe_type in name_lower:
                coherence_found = True
                found_ingredients = sum(1 for req in required_ingredients if req in ingredients_text)
                
                if found_ingredients == 0:
                    quality_analysis["issues"].append(f"{recipe_type.title()} sans ingrédients typiques")
                    coherence_score -= 30
                elif found_ingredients < len(required_ingredients) / 2:
                    quality_analysis["issues"].append(f"{recipe_type.title()} avec peu d'ingrédients typiques")
                    coherence_score -= 15
                
                quality_analysis["metrics"]["coherence"] = {
                    "type": recipe_type,
                    "expected_ingredients": len(required_ingredients),
                    "found_ingredients": found_ingredients
                }
                break
        
        if not coherence_found and len(ingredients) > 0:
            quality_analysis["issues"].append("Type de recette non identifiable")
            coherence_score -= 10
        
        quality_analysis["categories"]["coherence_quality"] = {
            "score": max(0, coherence_score),
            "status": "EXCELLENTE" if coherence_score >= 90 else "BONNE" if coherence_score >= 70 else "FAIBLE",
            "details": "Cohérence nom/ingrédients"
        }
        
        # 6. Analyse de la complétude
        completeness_score = 100
        required_fields = ["name", "recipeIngredient", "recipeInstructions"]
        optional_fields = ["description", "recipeServings", "prepTime", "cookTime", "totalTime"]
        
        missing_required = [field for field in required_fields if not recipe.get(field)]
        missing_optional = [field for field in optional_fields if not recipe.get(field)]
        
        if missing_required:
            completeness_score -= len(missing_required) * 25
            quality_analysis["issues"].append(f"Champs requis manquants: {', '.join(missing_required)}")
        
        if missing_optional:
            completeness_score -= len(missing_optional) * 5
        
        quality_analysis["categories"]["completeness_quality"] = {
            "score": max(0, completeness_score),
            "status": "COMPLÈTE" if completeness_score >= 90 else "PARTIELLE" if completeness_score >= 70 else "INCOMPLÈTE",
            "details": f"{len(required_fields) - len(missing_required)}/{len(required_fields)} champs requis"
        }
        
        # 7. Score global
        scores = [
            quality_analysis["categories"]["name_quality"]["score"],
            quality_analysis["categories"]["ingredients_quality"]["score"],
            quality_analysis["categories"]["instructions_quality"]["score"],
            quality_analysis["categories"]["description_quality"]["score"],
            quality_analysis["categories"]["coherence_quality"]["score"],
            quality_analysis["categories"]["completeness_quality"]["score"]
        ]
        
        quality_analysis["overall_score"] = sum(scores) / len(scores)
        
        # 8. Statut de qualité
        if quality_analysis["overall_score"] >= 90:
            quality_analysis["quality_status"] = "EXCELLENT"
        elif quality_analysis["overall_score"] >= 80:
            quality_analysis["quality_status"] = "BON"
        elif quality_analysis["overall_score"] >= 70:
            quality_analysis["quality_status"] = "MOYEN"
        elif quality_analysis["overall_score"] >= 60:
            quality_analysis["quality_status"] = "FAIBLE"
        else:
            quality_analysis["quality_status"] = "TRÈS FAIBLE"
        
        # 9. Recommandations
        quality_analysis["recommendations"] = []
        
        if quality_analysis["overall_score"] < 70:
            quality_analysis["recommendations"].append("Améliorer globalement la recette")
        
        if quality_analysis["categories"]["ingredients_quality"]["score"] < 70:
            quality_analysis["recommendations"].append("Ajouter plus d'ingrédients spécifiques")
        
        if quality_analysis["categories"]["instructions_quality"]["score"] < 70:
            quality_analysis["recommendations"].append("Détailler davantage les instructions")
        
        if quality_analysis["categories"]["description_quality"]["score"] < 70:
            quality_analysis["recommendations"].append("Enrichir la description")
        
        if quality_analysis["categories"]["coherence_quality"]["score"] < 70:
            quality_analysis["recommendations"].append("Améliorer la cohérence nom/ingrédients")
        
        # Affichage résumé
        print(f"   🎯 Score global: {quality_analysis['overall_score']:.1f}/100")
        print(f"   📊 Statut: {quality_analysis['quality_status']}")
        print(f"   🐛 Problèmes: {len(quality_analysis['issues'])}")
        print(f"   💡 Recommandations: {len(quality_analysis['recommendations'])}")
        
        return quality_analysis
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Erreur analyse qualité: {str(e)}",
            "quality_status": "FAILED",
            "overall_score": 0
        }
        print(f"   💥 Exception: {e}")
        return error_result

def quick_quality_check(recipe_slug: str) -> Dict[str, Any]:
    """
    Analyse de qualité rapide
    
    Args:
        recipe_slug: Slug de la recette
        
    Returns:
        Dict avec résultats simplifiés
    """
    result = check_recipe_quality(recipe_slug)
    
    return {
        "recipe_slug": recipe_slug,
        "quality_status": result.get("quality_status", "UNKNOWN"),
        "overall_score": result.get("overall_score", 0),
        "issues_count": len(result.get("issues", [])),
        "recommendations_count": len(result.get("recommendations", []))
    }

# Test de la fonction
if __name__ == "__main__":
    print("🧪 TEST CHECK RECIPE QUALITY")
    print("=" * 30)
    
    # D'abord lister les recettes pour en trouver une
    try:
        from mcp_auth_wrapper import mcp3_list_recipes
        recipes = mcp3_list_recipes()
        
        if recipes:
            print(f"\n📋 Test avec {len(recipes)} recettes disponibles")
            
            # Tester la première recette
            test_slug = recipes[0].get("slug", "")
            print(f"\n🔍 Analyse complète: {test_slug}")
            
            result1 = check_recipe_quality(test_slug)
            print(f"Résultat: {result1.get('quality_status', 'N/A')} ({result1.get('overall_score', 0):.1f}/100)")
            
            # Test rapide sur les 3 premières
            print(f"\n🚀 Analyse rapide des 3 premières recettes:")
            for i, recipe in enumerate(recipes[:3], 1):
                slug = recipe.get("slug", "")
                name = recipe.get("name", "N/A")
                
                quick_result = quick_quality_check(slug)
                print(f"   {i}. {name}: {quick_result['quality_status']} ({quick_result['overall_score']:.1f}/100)")
            
        else:
            print("Aucune recette disponible pour le test")
            
    except Exception as e:
        print(f"Erreur test: {e}")
    
    print("\n✅ Tests terminés")
