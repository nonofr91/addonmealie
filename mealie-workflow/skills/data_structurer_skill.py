#!/usr/bin/env python3
"""
SKILL MCP: DATA STRUCTURER
Skill pour la transformation des données scrapées en format Mealie
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import du structurer
import sys
sys.path.append(str(Path(__file__).parent.parent / "src" / "structuring"))
from mealie_structurer import MealieDataStructurer

class DataStructurerSkill:
    """Skill MCP pour la structuration des données Mealie"""
    
    def __init__(self):
        self.structurer = MealieDataStructurer()
        self.last_structure_results = None
    
    def structure_scraped_data(self, scraped_filename: str) -> Dict:
        """
        Structure les données scrapées pour Mealie
        
        Args:
            scraped_filename: Fichier JSON des données scrapées
        
        Returns:
            Dict avec les résultats de la structuration
        """
        try:
            print("🔧 SKILL: Data Structurer - Transformation Mealie")
            
            # Lancer le workflow de structuration
            filename = self.structurer.run_structuring_workflow(scraped_filename)
            
            if filename:
                # Charger les résultats pour les retourner
                with open(filename, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                self.last_structure_results = results
                
                return {
                    "success": True,
                    "filename": filename,
                    "total_recipes": len(results.get('recipes', [])),
                    "recipes": results.get('recipes', []),
                    "statistics": results.get('statistics', {}),
                    "metadata": results.get('metadata', {}),
                    "message": f"Structuration réussie: {len(results.get('recipes', []))} recettes"
                }
            else:
                return {
                    "success": False,
                    "error": "Échec de la structuration",
                    "message": "La structuration n'a pas pu être complétée"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la structuration: {str(e)}"
            }
    
    def structure_single_recipe(self, scraped_recipe: Dict) -> Dict:
        """
        Structure une seule recette scrapée
        
        Args:
            scraped_recipe: Données de la recette scrapée
        
        Returns:
            Dict avec la recette structurée
        """
        try:
            print(f"🔧 SKILL: Data Structurer - Recette unique: {scraped_recipe.get('name', 'Sans nom')}")
            
            # Structurer la recette
            mealie_recipe = self.structurer.structure_recipe_for_mealie(scraped_recipe)
            
            if mealie_recipe:
                return {
                    "success": True,
                    "recipe": mealie_recipe,
                    "slug": mealie_recipe.get('slug'),
                    "categories": mealie_recipe.get('recipeCategory', []),
                    "tags": mealie_recipe.get('tags', []),
                    "servings": mealie_recipe.get('recipeServings'),
                    "ingredients_count": len(mealie_recipe.get('recipeIngredient', [])),
                    "instructions_count": len(mealie_recipe.get('recipeInstructions', [])),
                    "nutrition": mealie_recipe.get('nutrition', {}),
                    "message": f"Recette '{mealie_recipe.get('name')}' structurée avec succès"
                }
            else:
                return {
                    "success": False,
                    "error": "Structuration échouée",
                    "message": "Impossible de structurer cette recette"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la structuration: {str(e)}"
            }
    
    def get_structuring_statistics(self) -> Dict:
        """
        Retourne les statistiques de la dernière structuration
        
        Returns:
            Dict avec les statistiques
        """
        try:
            if not self.last_structure_results:
                return {
                    "success": False,
                    "error": "Aucune structuration précédente",
                    "message": "Aucun résultat de structuration disponible"
                }
            
            stats = self.last_structure_results.get('statistics', {})
            recipes = self.last_structure_results.get('recipes', [])
            metadata = self.last_structure_results.get('metadata', {})
            
            return {
                "success": True,
                "statistics": stats,
                "total_recipes": len(recipes),
                "structured_at": metadata.get('created_at'),
                "format": metadata.get('format'),
                "language": metadata.get('language'),
                "cuisine": metadata.get('cuisine'),
                "message": f"Statistiques disponibles pour {len(recipes)} recettes"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la récupération des statistiques: {str(e)}"
            }
    
    def validate_structured_data(self, structured_filename: str = None) -> Dict:
        """
        Valide les données structurées pour Mealie
        
        Args:
            structured_filename: Fichier à valider (utilise le dernier si non spécifié)
        
        Returns:
            Dict avec les résultats de validation
        """
        try:
            print("🔧 SKILL: Data Structurer - Validation Mealie")
            
            # Utiliser le fichier spécifié ou la dernière structuration
            if structured_filename:
                with open(structured_filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif self.last_structure_results:
                data = self.last_structure_results
            else:
                return {
                    "success": False,
                    "error": "Aucune donnée à valider",
                    "message": "Spécifiez un fichier ou effectuez une structuration d'abord"
                }
            
            recipes = data.get('recipes', [])
            validation_results = {
                "total_recipes": len(recipes),
                "valid_recipes": 0,
                "invalid_recipes": 0,
                "issues": [],
                "mealie_compatibility": 0
            }
            
            for recipe in recipes:
                issues = []
                
                # Vérifier les champs requis Mealie
                if not recipe.get('name'):
                    issues.append("Nom manquant")
                
                if not recipe.get('slug'):
                    issues.append("Slug manquant")
                
                if not recipe.get('recipeIngredient'):
                    issues.append("Ingrédients Mealie manquants")
                
                if not recipe.get('recipeInstructions'):
                    issues.append("Instructions Mealie manquantes")
                
                if not recipe.get('recipeServings'):
                    issues.append("Portions Mealie manquantes")
                
                # Vérifier le format des ingrédients
                ingredients = recipe.get('recipeIngredient', [])
                for i, ingredient in enumerate(ingredients):
                    if not isinstance(ingredient, dict):
                        issues.append(f"Ingrédient {i+1}: format incorrect (doit être dict)")
                    elif 'referenceId' not in ingredient:
                        issues.append(f"Ingrédient {i+1}: referenceId manquant")
                
                # Vérifier le format des instructions
                instructions = recipe.get('recipeInstructions', [])
                for i, instruction in enumerate(instructions):
                    if not isinstance(instruction, dict):
                        issues.append(f"Instruction {i+1}: format incorrect (doit être dict)")
                    elif 'id' not in instruction:
                        issues.append(f"Instruction {i+1}: id manquant")
                    elif 'text' not in instruction:
                        issues.append(f"Instruction {i+1}: text manquant")
                
                # Vérifier les informations nutritionnelles
                nutrition = recipe.get('nutrition', {})
                if not nutrition.get('calories'):
                    issues.append("Calories manquantes")
                
                if issues:
                    validation_results["invalid_recipes"] += 1
                    validation_results["issues"].append({
                        "recipe": recipe.get('name', 'Sans nom'),
                        "slug": recipe.get('slug', 'N/A'),
                        "issues": issues
                    })
                else:
                    validation_results["valid_recipes"] += 1
                    validation_results["mealie_compatibility"] += 1
            
            compatibility_rate = (validation_results["mealie_compatibility"] / len(recipes)) * 100 if recipes else 0
            
            return {
                "success": True,
                "validation": validation_results,
                "compatibility_rate": compatibility_rate,
                "message": f"Validation: {validation_results['valid_recipes']} valides, {validation_results['invalid_recipes']} invalides ({compatibility_rate:.1f}% compatible Mealie)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la validation: {str(e)}"
            }
    
    def preview_structured_recipe(self, recipe_slug: str = None) -> Dict:
        """
        Affiche un aperçu d'une recette structurée
        
        Args:
            recipe_slug: Slug de la recette (première recette si non spécifié)
        
        Returns:
            Dict avec l'aperçu de la recette
        """
        try:
            if not self.last_structure_results:
                return {
                    "success": False,
                    "error": "Aucune donnée structurée disponible",
                    "message": "Effectuez une structuration d'abord"
                }
            
            recipes = self.last_structure_results.get('recipes', [])
            
            # Trouver la recette demandée
            target_recipe = None
            if recipe_slug:
                for recipe in recipes:
                    if recipe.get('slug') == recipe_slug:
                        target_recipe = recipe
                        break
            else:
                # Prendre la première recette
                target_recipe = recipes[0] if recipes else None
            
            if not target_recipe:
                return {
                    "success": False,
                    "error": "Recette non trouvée",
                    "message": f"Recette '{recipe_slug or 'première'}' non trouvée"
                }
            
            # Créer l'aperçu
            preview = {
                "name": target_recipe.get('name'),
                "slug": target_recipe.get('slug'),
                "description": target_recipe.get('description', ''),
                "servings": target_recipe.get('recipeServings'),
                "prep_time": target_recipe.get('prepTime'),
                "cook_time": target_recipe.get('cookTime'),
                "total_time": target_recipe.get('totalTime'),
                "categories": target_recipe.get('recipeCategory', []),
                "tags": target_recipe.get('tags', [])[:5],  # Limiter à 5 tags
                "difficulty": target_recipe.get('difficulty'),
                "cost": target_recipe.get('cost'),
                "ingredients_count": len(target_recipe.get('recipeIngredient', [])),
                "instructions_count": len(target_recipe.get('recipeInstructions', [])),
                "nutrition": {
                    "calories": target_recipe.get('nutrition', {}).get('calories'),
                    "protein": target_recipe.get('nutrition', {}).get('proteinContent'),
                    "carbs": target_recipe.get('nutrition', {}).get('carbohydrateContent'),
                    "fat": target_recipe.get('nutrition', {}).get('fatContent')
                }
            }
            
            return {
                "success": True,
                "preview": preview,
                "message": f"Aperçu de la recette '{preview['name']}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la génération de l'aperçu: {str(e)}"
            }

# Fonctions principales pour le skill MCP
def structure_data(scraped_filename: str) -> Dict:
    """Fonction principale de structuration"""
    skill = DataStructurerSkill()
    return skill.structure_scraped_data(scraped_filename)

def structure_recipe(scraped_recipe: Dict) -> Dict:
    """Structure une recette individuelle"""
    skill = DataStructurerSkill()
    return skill.structure_single_recipe(scraped_recipe)

def get_structure_info() -> Dict:
    """Retourne les informations de structuration"""
    skill = DataStructurerSkill()
    return skill.get_structuring_statistics()

def validate_mealie_data(structured_filename: str = None) -> Dict:
    """Valide les données structurées"""
    skill = DataStructurerSkill()
    return skill.validate_structured_data(structured_filename)

def preview_recipe(recipe_slug: str = None) -> Dict:
    """Affiche un aperçu de recette"""
    skill = DataStructurerSkill()
    return skill.preview_structured_recipe(recipe_slug)

if __name__ == "__main__":
    # Test du skill
    print("🧪 TEST DU SKILL DATA STRUCTURER")
    print("=" * 50)
    
    # Tester avec un fichier scrapé simulé
    test_scraped_file = "scraped_data/latest_scraped_recipes_mcp.json"
    
    # Tester la structuration
    structure_result = structure_data(test_scraped_file)
    print(f"🔧 Structuration: {structure_result.get('success', False)}")
    
    # Tester les statistiques
    stats_result = get_structure_info()
    print(f"📈 Statistiques: {stats_result.get('success', False)}")
    
    # Tester la validation
    validation_result = validate_mealie_data()
    print(f"✅ Validation: {validation_result.get('success', False)}")
    
    # Tester l'aperçu
    preview_result = preview_recipe()
    print(f"👁️ Aperçu: {preview_result.get('success', False)}")
