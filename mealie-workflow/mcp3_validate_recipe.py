#!/usr/bin/env python3
"""
MCP3 VALIDATE RECIPE
Outil MCP pour valider la qualité d'une recette avant import
"""

import json
import requests
from datetime import datetime
from typing import Dict, Any, List

def validate_recipe(recipe_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide la qualité d'une recette avant import
    
    Args:
        recipe_data: Dictionnaire contenant les données de la recette
        
    Returns:
        Dict avec résultats de validation
    """
    try:
        print(f"🔍 Validation recette: {recipe_data.get('name', 'Sans nom')}")
        
        # Critères de validation
        validation_results = {
            "recipe_name": recipe_data.get('name', ''),
            "validation_timestamp": datetime.now().isoformat(),
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "score": 100,
            "details": {}
        }
        
        # 1. Validation du nom
        name = recipe_data.get('name', '').strip()
        if not name:
            validation_results["errors"].append("Nom de recette manquant")
            validation_results["is_valid"] = False
            validation_results["score"] -= 30
        elif len(name) < 3:
            validation_results["warnings"].append("Nom de recette trop court")
            validation_results["score"] -= 10
        else:
            validation_results["details"]["name"] = "✅ Valide"
        
        # 2. Validation des ingrédients
        ingredients = recipe_data.get('ingredients', [])
        if not ingredients:
            validation_results["errors"].append("Aucun ingrédient fourni")
            validation_results["is_valid"] = False
            validation_results["score"] -= 40
        elif len(ingredients) < 2:
            validation_results["warnings"].append("Moins de 2 ingrédients")
            validation_results["score"] -= 15
        else:
            # Vérifier la qualité des ingrédients
            valid_ingredients = 0
            generic_ingredients = ["sel", "poivre", "eau", "huile", "beurre"]
            
            for ingredient in ingredients:
                if isinstance(ingredient, str) and len(ingredient.strip()) > 2:
                    valid_ingredients += 1
                    
                    # Vérifier si ingrédient générique
                    ingredient_lower = ingredient.lower()
                    if any(generic in ingredient_lower for generic in generic_ingredients):
                        validation_results["warnings"].append(f"Ingrédient générique: {ingredient}")
                        validation_results["score"] -= 5
            
            validation_results["details"]["ingredients"] = f"✅ {valid_ingredients}/{len(ingredients)} valides"
        
        # 3. Validation des instructions
        instructions = recipe_data.get('instructions', [])
        if not instructions:
            validation_results["errors"].append("Aucune instruction fournie")
            validation_results["is_valid"] = False
            validation_results["score"] -= 30
        elif len(instructions) < 2:
            validation_results["warnings"].append("Moins de 2 instructions")
            validation_results["score"] -= 15
        else:
            # Vérifier la qualité des instructions
            valid_instructions = 0
            
            for instruction in instructions:
                if isinstance(instruction, str) and len(instruction.strip()) > 5:
                    valid_instructions += 1
            
            validation_results["details"]["instructions"] = f"✅ {valid_instructions}/{len(instructions)} valides"
        
        # 4. Validation des portions
        servings = recipe_data.get('servings')
        if not servings:
            validation_results["warnings"].append("Nombre de portions non spécifié")
            validation_results["score"] -= 10
        else:
            try:
                servings_int = int(servings)
                if servings_int < 1:
                    validation_results["errors"].append("Nombre de portions invalide")
                    validation_results["is_valid"] = False
                    validation_results["score"] -= 20
                else:
                    validation_results["details"]["servings"] = f"✅ {servings_int} portions"
            except (ValueError, TypeError):
                validation_results["warnings"].append("Format de portions invalide")
                validation_results["score"] -= 10
        
        # 5. Validation des temps
        time_fields = ['prep_time', 'cook_time', 'total_time']
        for field in time_fields:
            time_value = recipe_data.get(field)
            if time_value:
                if isinstance(time_value, str) and len(time_value.strip()) > 0:
                    validation_results["details"][field] = "✅ Spécifié"
                else:
                    validation_results["warnings"].append(f"Format {field} invalide")
                    validation_results["score"] -= 5
        
        # 6. Validation de la description
        description = recipe_data.get('description', '').strip()
        if not description:
            validation_results["warnings"].append("Aucune description")
            validation_results["score"] -= 10
        elif len(description) < 10:
            validation_results["warnings"].append("Description trop courte")
            validation_results["score"] -= 5
        else:
            validation_results["details"]["description"] = "✅ Valide"
        
        # 7. Cohérence nom/contenu
        name_lower = name.lower()
        ingredients_text = " ".join(str(ing) for ing in ingredients).lower()
        
        # Vérifier la cohérence pour certains types de recettes
        coherence_checks = {
            "quiche": ["lardon", "œuf", "crème", "fromage"],
            "tarte": ["pâte", "farine", "beurre"],
            "bœuf": ["bœuf", "boeuf", "viande"],
            "saumon": ["saumon", "poisson"],
            "chocolat": ["chocolat", "cacao"]
        }
        
        for recipe_type, required_ingredients in coherence_checks.items():
            if recipe_type in name_lower:
                found_ingredients = sum(1 for req in required_ingredients if req in ingredients_text)
                if found_ingredients == 0:
                    validation_results["warnings"].append(f"{recipe_type.title()} sans ingrédients typiques")
                    validation_results["score"] -= 15
                else:
                    validation_results["details"][f"coherence_{recipe_type}"] = f"✅ {found_ingredients} ingrédients typiques"
        
        # 8. Score final
        validation_results["score"] = max(0, validation_results["score"])
        
        # 9. Catégorie de qualité
        if validation_results["score"] >= 90:
            validation_results["quality"] = "EXCELLENTE"
        elif validation_results["score"] >= 75:
            validation_results["quality"] = "BONNE"
        elif validation_results["score"] >= 60:
            validation_results["quality"] = "MOYENNE"
        elif validation_results["score"] >= 40:
            validation_results["quality"] = "FAIBLE"
        else:
            validation_results["quality"] = "TRÈS FAIBLE"
        
        # 10. Recommandations
        validation_results["recommendations"] = []
        
        if validation_results["errors"]:
            validation_results["recommendations"].append("Corriger les erreurs avant import")
        
        if validation_results["warnings"]:
            validation_results["recommendations"].append("Améliorer les warnings pour meilleure qualité")
        
        if validation_results["score"] < 70:
            validation_results["recommendations"].append("Enrichir la recette avec plus de détails")
        
        # Résumé final
        print(f"   🎯 Score: {validation_results['score']}/100")
        print(f"   📊 Qualité: {validation_results['quality']}")
        print(f"   ✅ Valide: {validation_results['is_valid']}")
        print(f"   🐛 Erreurs: {len(validation_results['errors'])}")
        print(f"   ⚠️ Warnings: {len(validation_results['warnings'])}")
        
        return validation_results
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Erreur validation: {str(e)}",
            "is_valid": False,
            "score": 0
        }
        print(f"   ❌ Exception: {e}")
        return error_result

def quick_validate(recipe_name: str, ingredients: List[str], instructions: List[str]) -> bool:
    """
    Validation rapide pour les cas simples
    
    Args:
        recipe_name: Nom de la recette
        ingredients: Liste des ingrédients
        instructions: Liste des instructions
        
    Returns:
        bool: True si valide
    """
    recipe_data = {
        "name": recipe_name,
        "ingredients": ingredients,
        "instructions": instructions
    }
    
    result = validate_recipe(recipe_data)
    return result.get("is_valid", False)

# Test de la fonction
if __name__ == "__main__":
    print("🧪 TEST VALIDATE RECIPE")
    print("=" * 30)
    
    # Test 1: Recette valide
    print("\n1. TEST RECETTE VALIDE")
    valid_recipe = {
        "name": "Quiche Lorraine",
        "description": "Recette traditionnelle française",
        "ingredients": [
            "200g lardons",
            "4 œufs", 
            "40cl crème fraîche",
            "1 pâte brisée",
            "sel, poivre"
        ],
        "instructions": [
            "Préchauffer le four à 180°C",
            "Faire revenir les lardons",
            "Mélanger œufs et crème",
            "Verser sur la pâte et cuire 40min"
        ],
        "servings": 6,
        "prep_time": "15",
        "cook_time": "40"
    }
    
    result1 = validate_recipe(valid_recipe)
    print(f"Résultat: {result1.get('quality', 'N/A')}")
    
    # Test 2: Recette invalide
    print("\n2. TEST RECETTE INVALIDE")
    invalid_recipe = {
        "name": "",
        "ingredients": [],
        "instructions": []
    }
    
    result2 = validate_recipe(invalid_recipe)
    print(f"Résultat: {result2.get('quality', 'N/A')}")
    
    # Test 3: Recette moyenne
    print("\n3. TEST RECETTE MOYENNE")
    medium_recipe = {
        "name": "Tarte",
        "ingredients": ["farine"],
        "instructions": ["Cuire"]
    }
    
    result3 = validate_recipe(medium_recipe)
    print(f"Résultat: {result3.get('quality', 'N/A')}")
    
    print("\n✅ Tests terminés")
