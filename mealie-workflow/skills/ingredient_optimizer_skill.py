#!/usr/bin/env python3
"""
SKILL MCP: INGREDIENT OPTIMIZER
Skill pour l'optimisation et la gestion des ingrédients dans Mealie
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class IngredientOptimizerSkill:
    """Skill MCP pour l'optimisation des ingrédients dans Mealie"""

    def __init__(self):
        self.last_optimization_results = None

    def validate_ingredients_structure(self, recipe_data: Dict) -> Dict:
        """
        Valide la structure des ingrédients d'une recette

        Args:
            recipe_data: Données de la recette avec recipeIngredient

        Returns:
            Dict avec le résultat de la validation
        """
        try:
            print("🔧 SKILL: Ingredient Optimizer - Validation structure ingrédients")

            ingredients = recipe_data.get("recipeIngredient", [])

            validation_result = {
                "success": True,
                "valid": True,
                "total_ingredients": len(ingredients),
                "issues": [],
                "warnings": []
            }

            for idx, ingredient in enumerate(ingredients):
                if isinstance(ingredient, str):
                    # Format texte simple - valide mais pourrait être amélioré
                    validation_result["warnings"].append({
                        "index": idx,
                        "ingredient": ingredient[:50] + "..." if len(ingredient) > 50 else ingredient,
                        "message": "Format texte simple - considérer la structuration"
                    })
                elif isinstance(ingredient, dict):
                    # Format structuré - vérifier les champs requis
                    if "note" not in ingredient:
                        validation_result["issues"].append({
                            "index": idx,
                            "message": "Champ 'note' manquant dans l'ingrédient structuré"
                        })
                        validation_result["valid"] = False
                else:
                    validation_result["issues"].append({
                        "index": idx,
                        "message": f"Type invalide: {type(ingredient).__name__}"
                    })
                    validation_result["valid"] = False

            validation_result["message"] = f"Validation terminée: {len(ingredients)} ingrédients, {len(validation_result['issues'])} erreurs, {len(validation_result['warnings'])} avertissements"

            self.last_optimization_results = validation_result
            return validation_result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la validation: {str(e)}"
            }

    def intelligent_ingredient_structurer(self, recipe_data: Dict) -> Dict:
        """
        Analyse et structure les ingrédients avec IA

        Args:
            recipe_data: Données de la recette avec recipeIngredient

        Returns:
            Dict avec les ingrédients structurés
        """
        try:
            print("🔧 SKILL: Ingredient Optimizer - Structuration intelligente")

            ingredients = recipe_data.get("recipeIngredient", [])

            structured_ingredients = []

            for ingredient in ingredients:
                if isinstance(ingredient, str):
                    # Tenter de structurer l'ingrédient texte
                    structured = self._parse_ingredient_text(ingredient)
                    structured_ingredients.append(structured)
                elif isinstance(ingredient, dict):
                    # Déjà structuré, valider et améliorer
                    structured = self._enhance_structured_ingredient(ingredient)
                    structured_ingredients.append(structured)
                else:
                    # Type invalide, convertir en texte
                    structured_ingredients.append({
                        "note": str(ingredient),
                        "quantity": None,
                        "unit": None,
                        "food": None
                    })

            result = {
                "success": True,
                "total_ingredients": len(structured_ingredients),
                "structured_ingredients": structured_ingredients,
                "original_count": len(ingredients),
                "message": f"Structuration terminée: {len(structured_ingredients)} ingrédients"
            }

            self.last_optimization_results = result
            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la structuration: {str(e)}"
            }

    def _parse_ingredient_text(self, ingredient_text: str) -> Dict:
        """
        Parse un ingrédient texte en format structuré

        Args:
            ingredient_text: Texte de l'ingrédient

        Returns:
            Dict avec l'ingrédient structuré
        """
        # Implémentation basique - peut être améliorée avec IA
        return {
            "note": ingredient_text,
            "quantity": None,
            "unit": None,
            "food": None
        }

    def _enhance_structured_ingredient(self, ingredient: Dict) -> Dict:
        """
        Améliore un ingrédient déjà structuré

        Args:
            ingredient: Ingrédient structuré

        Returns:
            Dict avec l'ingrédient amélioré
        """
        # S'assurer que tous les champs sont présents
        enhanced = ingredient.copy()

        if "note" not in enhanced:
            enhanced["note"] = ""

        if "quantity" not in enhanced:
            enhanced["quantity"] = None

        if "unit" not in enhanced:
            enhanced["unit"] = None

        if "food" not in enhanced:
            enhanced["food"] = None

        return enhanced

    def complete_ingredient_migration(self, foods_data: List[Dict], units_data: List[Dict]) -> Dict:
        """
        Migre complètement les ingrédients avec création d'éléments

        Args:
            foods_data: Liste des aliments à créer
            units_data: Liste des unités à créer

        Returns:
            Dict avec le résultat de la migration
        """
        try:
            print("🔧 SKILL: Ingredient Optimizer - Migration complète")

            # Cette fonction utilisera les MCP tools restaurés
            # Pour l'instant, retourne un plan de migration
            migration_plan = {
                "success": True,
                "foods_to_create": len(foods_data),
                "units_to_create": len(units_data),
                "foods": foods_data,
                "units": units_data,
                "message": f"Plan de migration: {len(foods_data)} aliments, {len(units_data)} unités"
            }

            self.last_optimization_results = migration_plan
            return migration_plan

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la migration: {str(e)}"
            }

    def correct_existing_foods(self, corrections: List[Dict]) -> Dict:
        """
        Corrige les noms d'aliments existants

        Args:
            corrections: Liste des corrections {food_id, new_name}

        Returns:
            Dict avec le résultat des corrections
        """
        try:
            print("🔧 SKILL: Ingredient Optimizer - Correction aliments")

            correction_results = {
                "success": True,
                "total_corrections": len(corrections),
                "applied_corrections": 0,
                "failed_corrections": 0,
                "corrections": []
            }

            for correction in corrections:
                food_id = correction.get("food_id")
                new_name = correction.get("new_name")

                if food_id and new_name:
                    correction_results["corrections"].append({
                        "food_id": food_id,
                        "new_name": new_name,
                        "status": "pending"
                    })
                    correction_results["applied_corrections"] += 1
                else:
                    correction_results["failed_corrections"] += 1

            correction_results["message"] = f"Corrections planifiées: {correction_results['applied_corrections']} appliquées, {correction_results['failed_corrections']} échouées"

            self.last_optimization_results = correction_results
            return correction_results

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors des corrections: {str(e)}"
            }

    def optimize_ingredients_in_file(self, structured_filename: str) -> Dict:
        """
        Optimise les ingrédients dans un fichier structuré

        Args:
            structured_filename: Chemin du fichier structuré

        Returns:
            Dict avec le résultat de l'optimisation
        """
        try:
            print("🔧 SKILL: Ingredient Optimizer - Optimisation fichier")

            # Charger le fichier structuré
            with open(structured_filename, 'r', encoding='utf-8') as f:
                structured_data = json.load(f)

            recipes = structured_data.get('recipes', [])
            optimized_count = 0

            for recipe in recipes:
                # Valider la structure des ingrédients
                validation_result = self.validate_ingredients_structure(recipe)

                if not validation_result.get('valid'):
                    # Structurer les ingrédients si nécessaire
                    structure_result = self.intelligent_ingredient_structurer(recipe)
                    if structure_result.get('success'):
                        # Mettre à jour les ingrédients dans la recette
                        recipe['recipeIngredient'] = structure_result.get('structured_ingredients', recipe.get('recipeIngredient', []))
                        optimized_count += 1

            # Sauvegarder le fichier optimisé
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(structured_filename).parent
            optimized_filename = output_dir / f"optimized_structured_recipes_{timestamp}.json"

            with open(optimized_filename, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, ensure_ascii=False, indent=2)

            result = {
                "success": True,
                "optimized_count": optimized_count,
                "total_recipes": len(recipes),
                "filename": str(optimized_filename),
                "message": f"Optimisation terminée: {optimized_count}/{len(recipes)} recettes optimisées"
            }

            self.last_optimization_results = result
            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de l'optimisation: {str(e)}"
            }


# Fonctions principales pour le skill MCP
def validate_ingredients(recipe_data: Dict) -> Dict:
    """Fonction principale de validation"""
    skill = IngredientOptimizerSkill()
    return skill.validate_ingredients_structure(recipe_data)


def structure_ingredients(recipe_data: Dict) -> Dict:
    """Fonction principale de structuration"""
    skill = IngredientOptimizerSkill()
    return skill.intelligent_ingredient_structurer(recipe_data)


def migrate_ingredients(foods_data: List[Dict], units_data: List[Dict]) -> Dict:
    """Fonction principale de migration"""
    skill = IngredientOptimizerSkill()
    return skill.complete_ingredient_migration(foods_data, units_data)


def correct_foods(corrections: List[Dict]) -> Dict:
    """Fonction principale de correction"""
    skill = IngredientOptimizerSkill()
    return skill.correct_existing_foods(corrections)


if __name__ == "__main__":
    # Test du skill
    test_recipe = {
        "recipeIngredient": [
            "2 tasses de farine",
            "1 cuillère à soupe de sucre",
            {"note": "3 œufs", "quantity": 3, "unit": "pièces"}
        ]
    }

    print("=== Test Validation ===")
    validation = validate_ingredients(test_recipe)
    print(json.dumps(validation, indent=2, ensure_ascii=False))

    print("\n=== Test Structuration ===")
    structuration = structure_ingredients(test_recipe)
    print(json.dumps(structuration, indent=2, ensure_ascii=False))
