#!/usr/bin/env python3
"""
MCP3 SEARCH RECIPES
Outil MCP pour rechercher des recettes dans Mealie
"""

import json
from typing import Dict, List, Any, Optional

def search_recipes(query: str, num: int = 10) -> Dict[str, Any]:
    """
    Recherche des recettes dans Mealie
    
    Args:
        query: Terme de recherche
        num: Nombre de résultats maximum
        
    Returns:
        Dict avec résultats de recherche
    """
    try:
        # Obtenir toutes les recettes
        all_recipes = list_recipes()
        
        if not all_recipes:
            return {
                "success": False,
                "error": "Impossible d'obtenir les recettes",
                "results": []
            }
        
        # Filtrer les recettes selon la recherche
        query_lower = query.lower()
        matching_recipes = []
        
        for recipe in all_recipes:
            recipe_name = recipe.get("name", "").lower()
            recipe_description = recipe.get("description", "").lower()
            recipe_slug = recipe.get("slug", "").lower()
            
            # Recherche dans nom, description et slug
            if (query_lower in recipe_name or 
                query_lower in recipe_description or 
                query_lower in recipe_slug):
                
                # Ajouter un score de pertinence
                score = 0
                if query_lower in recipe_name:
                    score += 10
                if query_lower == recipe_name:
                    score += 20
                if query_lower in recipe_slug:
                    score += 5
                if query_lower in recipe_description:
                    score += 3
                
                matching_recipes.append({
                    **recipe,
                    "search_score": score
                })
        
        # Trier par score de pertinence
        matching_recipes.sort(key=lambda x: x["search_score"], reverse=True)
        
        # Limiter le nombre de résultats
        results = matching_recipes[:num]
        
        return {
            "success": True,
            "query": query,
            "total_found": len(matching_recipes),
            "results_returned": len(results),
            "results": results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur recherche: {str(e)}",
            "results": []
        }

def list_recipes() -> Optional[List[Dict[str, Any]]]:
    """
    Obtient la liste de toutes les recettes (fonction utilitaire)
    """
    try:
        # Utiliser le MCP existant
        return mcp3_list_recipes()
    except:
        return None

def advanced_search(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recherche avancée avec filtres
    
    Args:
        filters: Dictionnaire de filtres (ex: {"category": "dessert", "servings": 4})
        
    Returns:
        Dict avec résultats de recherche avancée
    """
    try:
        all_recipes = list_recipes()
        
        if not all_recipes:
            return {
                "success": False,
                "error": "Impossible d'obtenir les recettes",
                "results": []
            }
        
        matching_recipes = []
        
        for recipe in all_recipes:
            matches = True
            
            # Filtrer par catégorie
            if "category" in filters:
                recipe_categories = recipe.get("categories", [])
                if not any(filters["category"].lower() in cat.lower() for cat in recipe_categories):
                    matches = False
            
            # Filtrer par nombre de portions
            if "servings" in filters:
                recipe_servings = recipe.get("servings", 0)
                try:
                    if recipe_servings != filters["servings"]:
                        matches = False
                except:
                    matches = False
            
            # Filtrer par mots-clés dans ingrédients
            if "ingredients" in filters:
                recipe_ingredients = recipe.get("ingredients", [])
                ingredients_text = " ".join(recipe_ingredients).lower()
                search_ingredients = filters["ingredients"].lower()
                
                if search_ingredients not in ingredients_text:
                    matches = False
            
            if matches:
                matching_recipes.append(recipe)
        
        return {
            "success": True,
            "filters": filters,
            "total_found": len(matching_recipes),
            "results": matching_recipes
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur recherche avancée: {str(e)}",
            "results": []
        }

# Test des fonctions
if __name__ == "__main__":
    print("🧪 TEST SEARCH RECIPES")
    print("=" * 30)
    
    # Test recherche simple
    test_query = "quiche"
    result = search_recipes(test_query, num=5)
    
    print(f"Recherche: {test_query}")
    print(f"Résultats: {result.get('total_found', 0)} trouvés")
    
    if result.get("success"):
        for recipe in result.get("results", [])[:3]:
            name = recipe.get("name", "Inconnu")
            score = recipe.get("search_score", 0)
            print(f"  📖 {name} (score: {score})")
    
    print("\n" + "=" * 30)
    
    # Test recherche avancée
    filters = {"category": "dessert"}
    advanced_result = advanced_search(filters)
    
    print(f"Recherche avancée: {filters}")
    print(f"Résultats: {advanced_result.get('total_found', 0)} trouvés")
    
    if advanced_result.get("success"):
        for recipe in advanced_result.get("results", [])[:3]:
            name = recipe.get("name", "Inconnu")
            print(f"  📖 {name}")
    
    print("\n✅ Tests terminés")
