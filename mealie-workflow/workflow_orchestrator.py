#!/usr/bin/env python3
"""
WORKFLOW ORCHESTRATOR
Coordonne les trois étapes du workflow Mealie
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import des skills
import sys
sys.path.insert(0, str(Path(__file__).parent / "skills"))
from recipe_scraper_skill import RecipeScraperSkill
from data_structurer_skill import DataStructurerSkill
from recipe_importer_skill import RecipeImporterSkill
from ingredient_optimizer_skill import IngredientOptimizerSkill

class MealieWorkflowOrchestrator:
    """Orchestrateur du workflow complet Mealie"""
    
    def __init__(self):
        self.scraper_skill = RecipeScraperSkill()
        self.structurer_skill = DataStructurerSkill()
        self.importer_skill = RecipeImporterSkill()
        self.ingredient_optimizer = IngredientOptimizerSkill()
        self.workflow_results = {}
    
    def run_complete_workflow(self, sources: List[str] = None) -> Dict:
        """
        Lance le workflow complet de scraping à l'import
        
        Args:
            sources: Sources à utiliser pour le scraping
        
        Returns:
            Dict avec les résultats complets du workflow
        """
        try:
            print("🚀 DÉMARRAGE DU WORKFLOW COMPLET MEALIE")
            print("📋 Scraping → Structuration → Import")
            print("=" * 60)
            
            workflow_start = datetime.now()
            
            # ÉTAPE 1: Scraping
            print("\n🔍 ÉTAPE 1: SCRAPING DES RECETTES")
            print("-" * 40)
            
            scrape_start = time.time()
            scrape_result = self.scraper_skill.scrape_recipes_from_sources(sources)
            scrape_time = time.time() - scrape_start
            
            if not scrape_result.get('success'):
                return {
                    "success": False,
                    "error": "Scraping échoué",
                    "message": "Le scraping a échoué, workflow arrêté",
                    "step": "scraping",
                    "details": scrape_result
                }
            
            scraped_filename = scrape_result.get('filename')
            self.workflow_results['scraping'] = {
                "success": True,
                "filename": scraped_filename,
                "total_recipes": scrape_result.get('total_recipes', 0),
                "time": scrape_time,
                "result": scrape_result
            }
            
            print(f"✅ Scraping terminé: {scrape_result.get('total_recipes', 0)} recettes en {scrape_time:.1f}s")
            
            # ÉTAPE 2: Structuration
            print("\n🔧 ÉTAPE 2: STRUCTURATION MEALIE")
            print("-" * 40)
            
            structure_start = time.time()
            structure_result = self.structurer_skill.structure_scraped_data(scraped_filename)
            structure_time = time.time() - structure_start
            
            if not structure_result.get('success'):
                return {
                    "success": False,
                    "error": "Structuration échouée",
                    "message": "La structuration a échoué, workflow arrêté",
                    "step": "structuring",
                    "details": structure_result
                }
            
            structured_filename = structure_result.get('filename')
            self.workflow_results['structuring'] = {
                "success": True,
                "filename": structured_filename,
                "total_recipes": structure_result.get('total_recipes', 0),
                "time": structure_time,
                "result": structure_result
            }
            
            print(f"✅ Structuration terminée: {structure_result.get('total_recipes', 0)} recettes en {structure_time:.1f}s")
            
            # ÉTAPE 3: Import
            print("\n📥 ÉTAPE 3: IMPORT MEALIE")
            print("-" * 40)
            
            import_start = time.time()
            import_result = self.importer_skill.import_structured_recipes(structured_filename)
            import_time = time.time() - import_start
            
            if not import_result.get('success'):
                return {
                    "success": False,
                    "error": "Import échoué",
                    "message": "L'import a échoué",
                    "step": "importing",
                    "details": import_result
                }
            
            import_filename = import_result.get('filename')
            self.workflow_results['importing'] = {
                "success": True,
                "filename": import_filename,
                "total_imported": import_result.get('total_imported', 0),
                "time": import_time,
                "result": import_result
            }
            
            print(f"✅ Import terminé: {import_result.get('total_imported', 0)} recettes en {import_time:.1f}s")
            
            # Calculer les statistiques finales
            workflow_end = datetime.now()
            total_time = (workflow_end - workflow_start).total_seconds()
            
            final_results = {
                "success": True,
                "workflow": {
                    "start_time": workflow_start.isoformat(),
                    "end_time": workflow_end.isoformat(),
                    "total_time": total_time,
                    "scraping_time": scrape_time,
                    "structuring_time": structure_time,
                    "importing_time": import_time
                },
                "results": self.workflow_results,
                "statistics": self.calculate_workflow_statistics(),
                "files": {
                    "scraped": scraped_filename,
                    "structured": structured_filename,
                    "import_report": import_filename
                },
                "message": "Workflow complet terminé avec succès!"
            }
            
            print(f"\n🎉 WORKFLOW TERMINÉ AVEC SUCCÈS!")
            print(f"⏱️ Temps total: {total_time:.1f}s")
            print(f"📊 Recettes traitées: {scrape_result.get('total_recipes', 0)} → {structure_result.get('total_recipes', 0)} → {import_result.get('total_imported', 0)}")
            
            return final_results
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors du workflow: {str(e)}",
                "step": "unknown"
            }
    
    def run_step_by_step(self, step: str, **kwargs) -> Dict:
        """
        Exécute une étape spécifique du workflow
        
        Args:
            step: 'scraping', 'structuring', 'importing'
            **kwargs: Paramètres spécifiques à l'étape
        
        Returns:
            Dict avec les résultats de l'étape
        """
        try:
            print(f"🔧 EXÉCUTION DE L'ÉTAPE: {step.upper()}")
            print("-" * 40)
            
            if step == 'scraping':
                sources = kwargs.get('sources')
                result = self.scraper_skill.scrape_recipes_from_sources(sources)
                self.workflow_results['scraping'] = result
                
            elif step == 'structuring':
                scraped_filename = kwargs.get('scraped_filename')
                if not scraped_filename and 'scraping' in self.workflow_results:
                    scraped_filename = self.workflow_results['scraping'].get('filename')
                
                if not scraped_filename:
                    return {
                        "success": False,
                        "error": "Fichier scraped manquant",
                        "message": "Spécifiez scraped_filename ou exécutez le scraping d'abord"
                    }
                
                result = self.structurer_skill.structure_scraped_data(scraped_filename)
                self.workflow_results['structuring'] = result
                
            elif step == 'importing':
                structured_filename = kwargs.get('structured_filename')
                if not structured_filename and 'structuring' in self.workflow_results:
                    structured_filename = self.workflow_results['structuring'].get('filename')
                
                if not structured_filename:
                    return {
                        "success": False,
                        "error": "Fichier structuré manquant",
                        "message": "Spécifiez structured_filename ou exécutez la structuration d'abord"
                    }
                
                result = self.importer_skill.import_structured_recipes(structured_filename)
                self.workflow_results['importing'] = result
                
            else:
                return {
                    "success": False,
                    "error": "Étape inconnue",
                    "message": f"Étape '{step}' non reconnue. Utilisez: scraping, structuring, importing"
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de l'étape {step}: {str(e)}"
            }
    
    def get_workflow_status(self) -> Dict:
        """
        Retourne le statut actuel du workflow
        
        Returns:
            Dict avec le statut du workflow
        """
        try:
            status = {
                "completed_steps": list(self.workflow_results.keys()),
                "step_status": {},
                "overall_progress": 0
            }
            
            total_steps = 3  # scraping, structuring, importing
            completed_steps = 0
            
            for step, result in self.workflow_results.items():
                step_status = result.get('success', False)
                status["step_status"][step] = {
                    "completed": step_status,
                    "message": result.get('message', ''),
                    "details": {
                        "total_items": result.get('total_recipes', result.get('total_imported', 0)),
                        "filename": result.get('filename'),
                        "time": result.get('time', 0)
                    }
                }
                
                if step_status:
                    completed_steps += 1
            
            status["overall_progress"] = (completed_steps / total_steps) * 100
            
            return {
                "success": True,
                "status": status,
                "message": f"Workflow: {completed_steps}/{total_steps} étapes complétées ({status['overall_progress']:.1f}%)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Erreur lors de la récupération du statut: {str(e)}"
            }
    
    def calculate_workflow_statistics(self) -> Dict:
        """Calcule les statistiques complètes du workflow"""
        try:
            stats = {
                "scraping": {},
                "structuring": {},
                "importing": {},
                "conversion_rates": {}
            }
            
            # Statistiques scraping
            if 'scraping' in self.workflow_results:
                scraping_result = self.workflow_results['scraping']['result']
                stats["scraping"] = {
                    "total_recipes": scraping_result.get('total_recipes', 0),
                    "sources_used": scraping_result.get('statistics', {}).get('sources_used', []),
                    "avg_instructions": scraping_result.get('statistics', {}).get('avg_instructions_per_recipe', 0),
                    "avg_ingredients": scraping_result.get('statistics', {}).get('avg_ingredients_per_recipe', 0)
                }
            
            # Statistiques structuration
            if 'structuring' in self.workflow_results:
                structuring_result = self.workflow_results['structuring']['result']
                stats["structuring"] = {
                    "total_recipes": structuring_result.get('total_recipes', 0),
                    "categories_created": structuring_result.get('statistics', {}).get('total_categories', 0),
                    "tags_created": structuring_result.get('statistics', {}).get('total_tags', 0),
                    "avg_calories": structuring_result.get('statistics', {}).get('average_calories', 0)
                }
            
            # Statistiques import
            if 'importing' in self.workflow_results:
                importing_result = self.workflow_results['importing']['result']
                stats["importing"] = {
                    "total_imported": importing_result.get('total_imported', 0),
                    "categories_in_mealie": importing_result.get('statistics', {}).get('total_categories', 0),
                    "tags_in_mealie": importing_result.get('statistics', {}).get('total_tags', 0),
                    "avg_ingredients": importing_result.get('statistics', {}).get('avg_ingredients_per_recipe', 0),
                    "avg_instructions": importing_result.get('statistics', {}).get('avg_instructions_per_recipe', 0)
                }
            
            # Taux de conversion
            scraped_count = stats["scraping"].get("total_recipes", 0)
            structured_count = stats["structuring"].get("total_recipes", 0)
            imported_count = stats["importing"].get("total_imported", 0)
            
            if scraped_count > 0:
                stats["conversion_rates"] = {
                    "scraping_to_structuring": (structured_count / scraped_count) * 100,
                    "structuring_to_import": (imported_count / structured_count) * 100 if structured_count > 0 else 0,
                    "overall_efficiency": (imported_count / scraped_count) * 100 if scraped_count > 0 else 0
                }
            
            return stats
            
        except Exception as e:
            return {
                "error": str(e),
                "message": f"Erreur calcul statistiques: {str(e)}"
            }
    
    def save_workflow_report(self, results: Dict = None) -> Optional[str]:
        """Sauvegarde un rapport complet du workflow"""
        try:
            # Utiliser les résultats fournis ou les derniers résultats
            workflow_data = results or self.workflow_results
            
            if not workflow_data:
                return None
            
            # Créer le dossier reports
            output_dir = Path(__file__).parent.parent / "workflow_reports"
            output_dir.mkdir(exist_ok=True)
            
            # Préparer le rapport
            report = {
                "report_date": datetime.now().isoformat(),
                "workflow_results": workflow_data,
                "statistics": self.calculate_workflow_statistics(),
                "status": self.get_workflow_status(),
                "summary": self.generate_workflow_summary()
            }
            
            # Sauvegarder avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = output_dir / f"mealie_workflow_report_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # Créer aussi un fichier latest
            latest_filename = output_dir / "latest_mealie_workflow_report.json"
            with open(latest_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Rapport workflow sauvegardé: {filename}")
            return str(filename)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde rapport: {e}")
            return None
    
    def generate_workflow_summary(self) -> Dict:
        """Génère un résumé du workflow"""
        try:
            summary = {
                "workflow_completed": False,
                "total_processing_time": 0,
                "recipes_processed": {
                    "scraped": 0,
                    "structured": 0,
                    "imported": 0
                },
                "success_rate": 0,
                "files_generated": [],
                "next_steps": []
            }
            
            # Vérifier si le workflow est complet
            if all(step in self.workflow_results for step in ['scraping', 'structuring', 'importing']):
                summary["workflow_completed"] = True
            
            # Calculer les temps et quantités
            total_time = 0
            for step, result in self.workflow_results.items():
                if result.get('success'):
                    total_time += result.get('time', 0)
                    
                    if step == 'scraping':
                        summary["recipes_processed"]["scraped"] = result.get('total_recipes', 0)
                    elif step == 'structuring':
                        summary["recipes_processed"]["structured"] = result.get('total_recipes', 0)
                    elif step == 'importing':
                        summary["recipes_processed"]["imported"] = result.get('total_imported', 0)
                    
                    if result.get('filename'):
                        summary["files_generated"].append(result.get('filename'))
            
            summary["total_processing_time"] = total_time
            
            # Calculer le taux de succès
            scraped = summary["recipes_processed"]["scraped"]
            imported = summary["recipes_processed"]["imported"]
            if scraped > 0:
                summary["success_rate"] = (imported / scraped) * 100
            
            # Prochaines étapes
            if not summary["workflow_completed"]:
                if 'scraping' not in self.workflow_results:
                    summary["next_steps"].append("Exécuter le scraping des recettes")
                if 'structuring' not in self.workflow_results:
                    summary["next_steps"].append("Structurer les données scrapées")
                if 'importing' not in self.workflow_results:
                    summary["next_steps"].append("Importer les recettes dans Mealie")
            else:
                summary["next_steps"].append("Utiliser les agents MCP (@nutrition-planner, @recipe-analyzer, @shopping-optimizer)")
                summary["next_steps"].append("Créer des menus personnalisés")
                summary["next_steps"].append("Générer des listes de courses")
            
            return summary
            
        except Exception as e:
            return {
                "error": str(e),
                "message": f"Erreur génération résumé: {str(e)}"
            }

# Fonctions principales pour l'orchestrateur
def run_full_workflow(sources: List[str] = None) -> Dict:
    """Lance le workflow complet"""
    orchestrator = MealieWorkflowOrchestrator()
    return orchestrator.run_complete_workflow(sources)

def run_workflow_step(step: str, **kwargs) -> Dict:
    """Exécute une étape spécifique"""
    orchestrator = MealieWorkflowOrchestrator()
    return orchestrator.run_step_by_step(step, **kwargs)

def get_workflow_status() -> Dict:
    """Retourne le statut du workflow"""
    orchestrator = MealieWorkflowOrchestrator()
    return orchestrator.get_workflow_status()

def save_workflow_report(results: Dict = None) -> Optional[str]:
    """Sauvegarde un rapport de workflow"""
    orchestrator = MealieWorkflowOrchestrator()
    return orchestrator.save_workflow_report(results)

if __name__ == "__main__":
    # Test de l'orchestrateur
    print("🧪 TEST DE L'ORCHESTRATEUR WORKFLOW")
    print("=" * 50)
    
    # Tester le workflow complet
    workflow_result = run_full_workflow()
    print(f"🚀 Workflow complet: {workflow_result.get('success', False)}")
    
    # Tester le statut
    status_result = get_workflow_status()
    print(f"📊 Statut: {status_result.get('success', False)}")
    
    # Tester la sauvegarde du rapport
    report_file = save_workflow_report(workflow_result)
    print(f"📋 Rapport: {'OK' if report_file else 'Échec'}")
