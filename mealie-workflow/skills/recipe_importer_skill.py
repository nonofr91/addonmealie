#!/usr/bin/env python3
"""
SKILL MCP: RECIPE IMPORTER
Skill pour l'import des recettes dans Mealie
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import de l'importateur
import sys
sys.path.append(str(Path(__file__).parent.parent / "src" / "importing"))
from mealie_importer_mcp import MealieImporterMCP

class RecipeImporterSkill:
    """Skill MCP pour l'import de recettes dans Mealie"""
    
    def __init__(self):
        # Initialiser le client IA via la factory
        try:
            sys.path.append(str(Path(__file__).parent.parent / "src" / "ai"))
            from ai.factory import create_ai_provider
            ai_client = create_ai_provider()
            use_parser = True
            print("✅ Client IA initialisé avec succès")
        except Exception as e:
            print(f"⚠️ Impossible d'initialiser le client IA: {e}")
            ai_client = None
            use_parser = False
        
        self.importer = MealieImporterMCP(use_parser=use_parser, ai_client=ai_client)
        self.last_import_results = None
    
    def import_structured_recipes(self, structured_filename: str) -> Dict:
        """
        Importe les recettes structurées dans Mealie
        
        Args:
            structured_filename: Fichier JSON des recettes structurées
        
        Returns:
            Dict avec les résultats de l'import
        """
        try:
            print("🔧 SKILL: Recipe Importer - Import Mealie")
            
            # Lancer le workflow d'import
            filename = self.importer.run_import_workflow(structured_filename)
            
            if filename:
                # Charger les résultats pour les retourner
                with open(filename, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                self.last_import_results = results
                
                return {
                    "success": True,
                    "filename": filename,
                    "total_imported": len(results.get('recipes', [])),
                    "recipes": results.get('recipes', []),
                    "statistics": results.get('statistics', {}),
                    "metadata": results.get('metadata', {}),
                    "message": f"Import réussi: {len(results.get('recipes', []))} recettes importées"
                }
            else:
                return {
                    "success": False,
                    "error": "Échec de l'import",
                    "message": "L'import n'a pas pu être complété"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de l'import: {str(e)}"
            }
    
    def import_single_recipe(self, structured_recipe: Dict) -> Dict:
        """
        Importe une seule recette structurée
        
        Args:
            structured_recipe: Recette structurée au format Mealie
        
        Returns:
            Dict avec le résultat de l'import
        """
        try:
            print(f"🔧 SKILL: Recipe Importer - Import unique: {structured_recipe.get('name', 'Sans nom')}")
            
            # Importer la recette
            success = self.importer.import_recipe_to_mealie(structured_recipe)
            
            if success:
                # Récupérer les informations de la recette importée
                imported_recipes = self.importer.imported_recipes
                last_imported = imported_recipes[-1] if imported_recipes else None
                
                if last_imported:
                    return {
                        "success": True,
                        "recipe": last_imported,
                        "recipe_id": last_imported.get('id'),
                        "slug": last_imported.get('slug'),
                        "name": last_imported.get('name'),
                        "servings": last_imported.get('servings'),
                        "ingredients_count": last_imported.get('ingredients_count'),
                        "instructions_count": last_imported.get('instructions_count'),
                        "categories": last_imported.get('categories'),
                        "tags": last_imported.get('tags'),
                        "imported_at": last_imported.get('imported_at'),
                        "message": f"Recette '{last_imported.get('name')}' importée avec succès"
                    }
                else:
                    return {
                        "success": True,
                        "message": "Recette importée mais détails non disponibles"
                    }
            else:
                return {
                    "success": False,
                    "error": "Import échoué",
                    "message": "Impossible d'importer cette recette"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de l'import: {str(e)}"
            }
    
    def get_import_statistics(self) -> Dict:
        """
        Retourne les statistiques du dernier import
        
        Returns:
            Dict avec les statistiques
        """
        try:
            if not self.last_import_results:
                return {
                    "success": False,
                    "error": "Aucun import précédent",
                    "message": "Aucun résultat d'import disponible"
                }
            
            stats = self.last_import_results.get('statistics', {})
            recipes = self.last_import_results.get('recipes', [])
            metadata = self.last_import_results.get('metadata', {})
            
            return {
                "success": True,
                "statistics": stats,
                "total_imported": len(recipes),
                "imported_at": metadata.get('import_date'),
                "config": metadata.get('config', {}),
                "message": f"Statistiques disponibles pour {len(recipes)} recettes importées"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la récupération des statistiques: {str(e)}"
            }
    
    def list_imported_recipes(self) -> Dict:
        """
        Liste toutes les recettes importées
        
        Returns:
            Dict avec la liste des recettes importées
        """
        try:
            if not self.importer.imported_recipes:
                return {
                    "success": False,
                    "error": "Aucune recette importée",
                    "message": "Aucune recette n'a été importée encore"
                }
            
            recipes = self.importer.imported_recipes
            
            # Créer une liste simplifiée
            recipe_list = []
            for recipe in recipes:
                recipe_list.append({
                    "id": recipe.get('id'),
                    "name": recipe.get('name'),
                    "slug": recipe.get('slug'),
                    "servings": recipe.get('servings'),
                    "categories": recipe.get('categories', []),
                    "tags": recipe.get('tags', [])[:3],  # Limiter à 3 tags
                    "difficulty": recipe.get('difficulty'),
                    "cost": recipe.get('cost'),
                    "calories": recipe.get('nutrition', {}).get('calories'),
                    "imported_at": recipe.get('imported_at')
                })
            
            return {
                "success": True,
                "recipes": recipe_list,
                "total_count": len(recipe_list),
                "message": f"{len(recipe_list)} recettes importées disponibles"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la récupération des recettes: {str(e)}"
            }
    
    def verify_recipe_import(self, recipe_id: str = None, recipe_slug: str = None) -> Dict:
        """
        Vérifie qu'une recette a été correctement importée
        
        Args:
            recipe_id: ID de la recette à vérifier
            recipe_slug: Slug de la recette à vérifier
        
        Returns:
            Dict avec le résultat de la vérification
        """
        try:
            if not recipe_id and not recipe_slug:
                return {
                    "success": False,
                    "error": "Paramètres manquants",
                    "message": "Spécifiez recipe_id ou recipe_slug"
                }
            
            print(f"🔧 SKILL: Recipe Importer - Vérification: {recipe_id or recipe_slug}")
            
            # Trouver la recette dans les imports
            target_recipe = None
            for recipe in self.importer.imported_recipes:
                if (recipe_id and recipe.get('id') == recipe_id) or (recipe_slug and recipe.get('slug') == recipe_slug):
                    target_recipe = recipe
                    break
            
            if not target_recipe:
                return {
                    "success": False,
                    "error": "Recette non trouvée",
                    "message": f"Recette '{recipe_id or recipe_slug}' non trouvée dans les imports"
                }
            
            # Simuler la vérification (en production utiliserait mealie-test MCP)
            verification_result = self.importer.verify_imported_recipe(target_recipe['name'], target_recipe['id'])
            
            return {
                "success": verification_result,
                "recipe": target_recipe,
                "verified": verification_result,
                "message": f"Recette '{target_recipe['name']}' {'vérifiée' if verification_result else 'non vérifiée'}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la vérification: {str(e)}"
            }
    
    def get_recipe_details(self, recipe_id: str = None, recipe_slug: str = None) -> Dict:
        """
        Retourne les détails complets d'une recette importée
        
        Args:
            recipe_id: ID de la recette
            recipe_slug: Slug de la recette
        
        Returns:
            Dict avec les détails de la recette
        """
        try:
            if not recipe_id and not recipe_slug:
                return {
                    "success": False,
                    "error": "Paramètres manquants",
                    "message": "Spécifiez recipe_id ou recipe_slug"
                }
            
            # Trouver la recette
            target_recipe = None
            for recipe in self.importer.imported_recipes:
                if (recipe_id and recipe.get('id') == recipe_id) or (recipe_slug and recipe.get('slug') == recipe_slug):
                    target_recipe = recipe
                    break
            
            if not target_recipe:
                return {
                    "success": False,
                    "error": "Recette non trouvée",
                    "message": f"Recette '{recipe_id or recipe_slug}' non trouvée"
                }
            
            return {
                "success": True,
                "recipe": target_recipe,
                "message": f"Détails de la recette '{target_recipe['name']}'"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la récupération des détails: {str(e)}"
            }
    
    def export_import_summary(self) -> Dict:
        """
        Exporte un résumé de l'import pour documentation
        
        Returns:
            Dict avec le résumé d'import
        """
        try:
            if not self.importer.imported_recipes:
                return {
                    "success": False,
                    "error": "Aucun import à exporter",
                    "message": "Effectuez un import d'abord"
                }
            
            recipes = self.importer.imported_recipes
            stats = self.importer.calculate_import_statistics()
            
            summary = {
                "export_date": datetime.now().isoformat(),
                "total_recipes": len(recipes),
                "statistics": stats,
                "categories_summary": {},
                "tags_summary": {},
                "difficulty_summary": {},
                "cost_summary": {},
                "recipes_overview": []
            }
            
            # Analyser les catégories
            categories = {}
            for recipe in recipes:
                for category in recipe.get('categories', []):
                    categories[category] = categories.get(category, 0) + 1
            summary["categories_summary"] = categories
            
            # Analyser les tags
            tags = {}
            for recipe in recipes:
                for tag in recipe.get('tags', []):
                    tags[tag] = tags.get(tag, 0) + 1
            summary["tags_summary"] = dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10])  # Top 10
            
            # Analyser difficultés et coûts
            difficulties = {}
            costs = {}
            for recipe in recipes:
                diff = recipe.get('difficulty', 'Inconnu')
                cost = recipe.get('cost', 'Inconnu')
                difficulties[diff] = difficulties.get(diff, 0) + 1
                costs[cost] = costs.get(cost, 0) + 1
            summary["difficulty_summary"] = difficulties
            summary["cost_summary"] = costs
            
            # Aperçu des recettes
            for recipe in recipes[:5]:  # Top 5
                summary["recipes_overview"].append({
                    "name": recipe.get('name'),
                    "slug": recipe.get('slug'),
                    "servings": recipe.get('servings'),
                    "calories": recipe.get('nutrition', {}).get('calories'),
                    "categories": recipe.get('categories', []),
                    "difficulty": recipe.get('difficulty'),
                    "cost": recipe.get('cost')
                })
            
            return {
                "success": True,
                "summary": summary,
                "message": f"Résumé exporté pour {len(recipes)} recettes"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de l'export du résumé: {str(e)}"
            }

# Fonctions principales pour le skill MCP
def import_recipes(structured_filename: str) -> Dict:
    """Fonction principale d'import"""
    skill = RecipeImporterSkill()
    return skill.import_structured_recipes(structured_filename)

def import_recipe(structured_recipe: Dict) -> Dict:
    """Importe une recette individuelle"""
    skill = RecipeImporterSkill()
    return skill.import_single_recipe(structured_recipe)

def get_import_info() -> Dict:
    """Retourne les informations d'import"""
    skill = RecipeImporterSkill()
    return skill.get_import_statistics()

def list_imported() -> Dict:
    """Liste les recettes importées"""
    skill = RecipeImporterSkill()
    return skill.list_imported_recipes()

def verify_import(recipe_id: str = None, recipe_slug: str = None) -> Dict:
    """Vérifie une recette importée"""
    skill = RecipeImporterSkill()
    return skill.verify_recipe_import(recipe_id, recipe_slug)

def get_recipe_info(recipe_id: str = None, recipe_slug: str = None) -> Dict:
    """Retourne les détails d'une recette"""
    skill = RecipeImporterSkill()
    return skill.get_recipe_details(recipe_id, recipe_slug)

def export_summary() -> Dict:
    """Exporte un résumé d'import"""
    skill = RecipeImporterSkill()
    return skill.export_import_summary()

if __name__ == "__main__":
    # Test du skill
    print("🧪 TEST DU SKILL RECIPE IMPORTER")
    print("=" * 50)
    
    # Tester avec un fichier structuré simulé
    test_structured_file = "structured_data/latest_mealie_structured_recipes.json"
    
    # Tester l'import
    import_result = import_recipes(test_structured_file)
    print(f"📥 Import: {import_result.get('success', False)}")
    
    # Tester les statistiques
    stats_result = get_import_info()
    print(f"📈 Statistiques: {stats_result.get('success', False)}")
    
    # Tester la liste
    list_result = list_imported()
    print(f"📋 Liste: {list_result.get('success', False)}")
    
    # Tester l'export
    summary_result = export_summary()
    print(f"📊 Résumé: {summary_result.get('success', False)}")
