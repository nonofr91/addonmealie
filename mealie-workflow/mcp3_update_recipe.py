#!/usr/bin/env python3
"""
MCP3 UPDATE RECIPE
Outil MCP pour mettre à jour des recettes dans Mealie
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List

def update_recipe(recipe_slug: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Met à jour une recette dans Mealie
    
    Args:
        recipe_slug: Slug de la recette à mettre à jour
        updates: Dictionnaire des champs à mettre à jour
        
    Returns:
        Dict avec succès/erreur
    """
    try:
        # Vérifier que la recette existe
        existing_recipe = get_recipe_details(recipe_slug)
        
        if not existing_recipe or "error" in existing_recipe:
            return {
                "success": False,
                "error": f"Recette {recipe_slug} non trouvée"
            }
        
        # Valider les champs à mettre à jour
        valid_fields = [
            "name", "description", "ingredients", "instructions",
            "prep_time", "cook_time", "total_time", "servings",
            "categories", "tags", "image"
        ]
        
        invalid_fields = [field for field in updates.keys() if field not in valid_fields]
        if invalid_fields:
            return {
                "success": False,
                "error": f"Champs invalides: {', '.join(invalid_fields)}"
            }
        
        # Créer la recette mise à jour
        updated_recipe = existing_recipe.copy()
        updated_recipe.update(updates)
        
        # Ajouter des métadonnées de mise à jour
        updated_recipe["updated_at"] = datetime.now().isoformat()
        updated_recipe["updated_by"] = "MCP3_Update_Recipe"
        updated_recipe["update_fields"] = list(updates.keys())
        
        # Simuler la mise à jour (à remplacer avec vraie API Mealie)
        # En attendant, on sauvegarde dans un fichier de log
        update_log = {
            "updated_at": datetime.now().isoformat(),
            "recipe_slug": recipe_slug,
            "updates": updates,
            "updated_recipe": updated_recipe,
            "simulation": True
        }
        
        # Sauvegarder le log de mise à jour
        log_file = f"/tmp/mealie_updates_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(update_log) + '\n')
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde log: {e}")
        
        return {
            "success": True,
            "message": f"Recette {updated_recipe.get('name')} mise à jour (simulation)",
            "updated_recipe": updated_recipe,
            "updates_applied": updates,
            "simulation": True,
            "log_file": log_file
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur mise à jour: {str(e)}"
        }

def add_ingredient(recipe_slug: str, ingredient: str) -> Dict[str, Any]:
    """
    Ajoute un ingrédient à une recette
    
    Args:
        recipe_slug: Slug de la recette
        ingredient: Ingrédient à ajouter
        
    Returns:
        Dict avec succès/erreur
    """
    try:
        existing_recipe = get_recipe_details(recipe_slug)
        
        if not existing_recipe:
            return {
                "success": False,
                "error": f"Recette {recipe_slug} non trouvée"
            }
        
        current_ingredients = existing_recipe.get("ingredients", [])
        
        # Vérifier si l'ingrédient existe déjà
        if ingredient in current_ingredients:
            return {
                "success": False,
                "error": f"L'ingrédient '{ingredient}' existe déjà"
            }
        
        # Ajouter l'ingrédient
        new_ingredients = current_ingredients + [ingredient]
        
        return update_recipe(recipe_slug, {"ingredients": new_ingredients})
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur ajout ingrédient: {str(e)}"
        }

def remove_ingredient(recipe_slug: str, ingredient: str) -> Dict[str, Any]:
    """
    Supprime un ingrédient d'une recette
    
    Args:
        recipe_slug: Slug de la recette
        ingredient: Ingrédient à supprimer
        
    Returns:
        Dict avec succès/erreur
    """
    try:
        existing_recipe = get_recipe_details(recipe_slug)
        
        if not existing_recipe:
            return {
                "success": False,
                "error": f"Recette {recipe_slug} non trouvée"
            }
        
        current_ingredients = existing_recipe.get("ingredients", [])
        
        # Vérifier si l'ingrédient existe
        if ingredient not in current_ingredients:
            return {
                "success": False,
                "error": f"L'ingrédient '{ingredient}' n'existe pas"
            }
        
        # Supprimer l'ingrédient
        new_ingredients = [ing for ing in current_ingredients if ing != ingredient]
        
        return update_recipe(recipe_slug, {"ingredients": new_ingredients})
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur suppression ingrédient: {str(e)}"
        }

def add_instruction(recipe_slug: str, instruction: str, position: Optional[int] = None) -> Dict[str, Any]:
    """
    Ajoute une instruction à une recette
    
    Args:
        recipe_slug: Slug de la recette
        instruction: Instruction à ajouter
        position: Position où insérer (None = à la fin)
        
    Returns:
        Dict avec succès/erreur
    """
    try:
        existing_recipe = get_recipe_details(recipe_slug)
        
        if not existing_recipe:
            return {
                "success": False,
                "error": f"Recette {recipe_slug} non trouvée"
            }
        
        current_instructions = existing_recipe.get("instructions", [])
        
        # Ajouter l'instruction
        if position is None:
            new_instructions = current_instructions + [instruction]
        else:
            new_instructions = current_instructions.copy()
            new_instructions.insert(position, instruction)
        
        return update_recipe(recipe_slug, {"instructions": new_instructions})
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur ajout instruction: {str(e)}"
        }

def get_recipe_details(recipe_slug: str) -> Optional[Dict[str, Any]]:
    """
    Obtient les détails d'une recette (fonction utilitaire)
    """
    try:
        # Utiliser le MCP existant
        return mcp3_get_recipe_details(recipe_slug)
    except:
        return None

# Test des fonctions
if __name__ == "__main__":
    print("🧪 TEST UPDATE RECIPE")
    print("=" * 30)
    
    # Test mise à jour simple
    test_slug = "quiche-lorraine"
    updates = {
        "description": "Recette de quiche lorraine améliorée",
        "servings": 6
    }
    
    result = update_recipe(test_slug, updates)
    
    print(f"Mise à jour: {test_slug}")
    print(f"Champs: {list(updates.keys())}")
    print(f"Résultat: {result.get('success', False)}")
    
    if result.get("success"):
        updated_recipe = result.get("updated_recipe", {})
        print(f"Nouvelle description: {updated_recipe.get('description', 'N/A')}")
        print(f"Nouvelles portions: {updated_recipe.get('servings', 'N/A')}")
    
    print("\n" + "=" * 30)
    
    # Test ajout ingrédient
    ingredient_result = add_ingredient(test_slug, "1 pincée de muscade")
    print(f"Ajout ingrédient: {ingredient_result.get('success', False)}")
    
    print("\n✅ Tests terminés")
