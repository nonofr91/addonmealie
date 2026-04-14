#!/usr/bin/env python3
"""
SKILL MCP: RECIPE SCRAPER
Skill principal pour le scraping de recettes avec les outils MCP
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import du scraper
import sys
sys.path.append(str(Path(__file__).parent.parent / "src" / "scraping"))
from recipe_scraper_mcp import RecipeScraperMCP

class RecipeScraperSkill:
    """Skill MCP pour le scraping de recettes"""
    
    def __init__(self):
        self.scraper = RecipeScraperMCP()
        self.last_scrape_results = None
    
    def scrape_recipes_from_sources(self, sources: List[str] = None) -> Dict:
        """
        Scrape des recettes depuis les sources spécifiées
        
        Args:
            sources: Liste des sources à utiliser (ex: ['marmiton', '750g'])
        
        Returns:
            Dict avec les résultats du scraping
        """
        try:
            print("🔧 SKILL: Recipe Scraper - Scraping depuis sources")
            
            # Lancer le workflow de scraping
            filename = self.scraper.run_scraping_workflow()
            
            if filename:
                # Charger les résultats pour les retourner
                with open(filename, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                
                self.last_scrape_results = results
                
                return {
                    "success": True,
                    "filename": filename,
                    "total_recipes": len(results.get('recipes', [])),
                    "recipes": results.get('recipes', []),
                    "statistics": results.get('statistics', {}),
                    "message": f"Scraping réussi: {len(results.get('recipes', []))} recettes"
                }
            else:
                return {
                    "success": False,
                    "error": "Échec du scraping",
                    "message": "Le scraping n'a pas pu être complété"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors du scraping: {str(e)}"
            }
    
    def scrape_specific_recipe(self, url: str) -> Dict:
        """
        Scrape une recette spécifique depuis une URL
        
        Args:
            url: URL de la recette à scraper
        
        Returns:
            Dict avec les données de la recette scrapée
        """
        try:
            print(f"🔧 SKILL: Recipe Scraper - Scraping spécifique: {url}")
            
            # Extraire la recette
            recipe_data = self.scraper.extract_recipe_content(url)
            
            if recipe_data:
                return {
                    "success": True,
                    "recipe": recipe_data,
                    "message": f"Recette '{recipe_data.get('name', 'Sans nom')}' scrapée avec succès"
                }
            else:
                return {
                    "success": False,
                    "error": "Recette non trouvée",
                    "message": "Impossible de scraper la recette depuis cette URL"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors du scraping de la recette: {str(e)}"
            }
    
    def get_scraping_statistics(self) -> Dict:
        """
        Retourne les statistiques du dernier scraping
        
        Returns:
            Dict avec les statistiques
        """
        try:
            if not self.last_scrape_results:
                return {
                    "success": False,
                    "error": "Aucun scraping précédent",
                    "message": "Aucun résultat de scraping disponible"
                }
            
            stats = self.last_scrape_results.get('statistics', {})
            recipes = self.last_scrape_results.get('recipes', [])
            
            return {
                "success": True,
                "statistics": stats,
                "total_recipes": len(recipes),
                "scraped_at": self.last_scrape_results.get('metadata', {}).get('scraped_at'),
                "sources_used": self.last_scrape_results.get('metadata', {}).get('sources', []),
                "message": f"Statistiques disponibles pour {len(recipes)} recettes"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la récupération des statistiques: {str(e)}"
            }
    
    def list_available_sources(self) -> Dict:
        """
        Liste les sources de scraping disponibles
        
        Returns:
            Dict avec les sources configurées
        """
        try:
            sources_config = self.scraper.sources_config
            sources = sources_config.get('sources', {})
            target_recipes = sources_config.get('target_recipes', [])
            
            return {
                "success": True,
                "sources": list(sources.keys()),
                "source_details": sources,
                "target_recipes": target_recipes,
                "total_sources": len(sources),
                "total_target_recipes": len(target_recipes),
                "message": f"{len(sources)} sources configurées pour {len(target_recipes)} recettes cibles"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la récupération des sources: {str(e)}"
            }
    
    def validate_scraped_data(self, filename: str = None) -> Dict:
        """
        Valide les données scrapées
        
        Args:
            filename: Fichier à valider (utilise le dernier si non spécifié)
        
        Returns:
            Dict avec les résultats de validation
        """
        try:
            print("🔧 SKILL: Recipe Scraper - Validation des données")
            
            # Utiliser le fichier spécifié ou le dernier scraping
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif self.last_scrape_results:
                data = self.last_scrape_results
            else:
                return {
                    "success": False,
                    "error": "Aucune donnée à valider",
                    "message": "Spécifiez un fichier ou effectuez un scraping d'abord"
                }
            
            recipes = data.get('recipes', [])
            validation_results = {
                "total_recipes": len(recipes),
                "valid_recipes": 0,
                "invalid_recipes": 0,
                "issues": []
            }
            
            for recipe in recipes:
                issues = []
                
                # Vérifier les champs requis
                if not recipe.get('name'):
                    issues.append("Nom manquant")
                
                if not recipe.get('ingredients'):
                    issues.append("Ingrédients manquants")
                
                if not recipe.get('instructions'):
                    issues.append("Instructions manquantes")
                
                if not recipe.get('servings'):
                    issues.append("Portions manquantes")
                
                if issues:
                    validation_results["invalid_recipes"] += 1
                    validation_results["issues"].append({
                        "recipe": recipe.get('name', 'Sans nom'),
                        "issues": issues
                    })
                else:
                    validation_results["valid_recipes"] += 1
            
            return {
                "success": True,
                "validation": validation_results,
                "message": f"Validation: {validation_results['valid_recipes']} valides, {validation_results['invalid_recipes']} invalides"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la validation: {str(e)}"
            }

# Fonctions principales pour le skill MCP
def scrape_recipes(sources: List[str] = None) -> Dict:
    """Fonction principale de scraping"""
    skill = RecipeScraperSkill()
    return skill.scrape_recipes_from_sources(sources)

def scrape_recipe(url: str) -> Dict:
    """Scrape une recette spécifique"""
    skill = RecipeScraperSkill()
    return skill.scrape_specific_recipe(url)

def get_scraping_info() -> Dict:
    """Retourne les informations de scraping"""
    skill = RecipeScraperSkill()
    return skill.get_scraping_statistics()

def list_sources() -> Dict:
    """Liste les sources disponibles"""
    skill = RecipeScraperSkill()
    return skill.list_available_sources()

def validate_data(filename: str = None) -> Dict:
    """Valide les données scrapées"""
    skill = RecipeScraperSkill()
    return skill.validate_scraped_data(filename)

if __name__ == "__main__":
    # Test du skill
    print("🧪 TEST DU SKILL RECIPE SCRAPER")
    print("=" * 50)
    
    # Tester le listing des sources
    sources_result = list_sources()
    print(f"📊 Sources: {sources_result.get('success', False)}")
    
    # Tester le scraping
    scrape_result = scrape_recipes()
    print(f"🔧 Scraping: {scrape_result.get('success', False)}")
    
    # Tester les statistiques
    stats_result = get_scraping_info()
    print(f"📈 Statistiques: {stats_result.get('success', False)}")
    
    # Tester la validation
    validation_result = validate_data()
    print(f"✅ Validation: {validation_result.get('success', False)}")
