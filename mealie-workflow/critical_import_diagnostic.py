#!/usr/bin/env python3
"""
CRITICAL IMPORT DIAGNOSTIC
Diagnostic des problèmes critiques d'import dans Mealie
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

class CriticalImportDiagnostic:
    """Diagnostic des problèmes critiques d'import"""
    
    def __init__(self):
        self.critical_issues = []
        self.diagnostic_log = []
        
    def run_critical_diagnostic(self) -> Dict:
        """Lance le diagnostic complet des imports"""
        print("🚨 DIAGNOSTIC CRITIQUE D'IMPORT MEALIE")
        print("🔍 Vérification des vrais problèmes de qualité")
        print("=" * 80)
        
        # 1. Vérifier les recettes dans Mealie
        print("\n📋 ÉTAPE 1: VÉRIFICATION RECETTES MEALIE")
        mealie_issues = self.check_mealie_recipes()
        
        # 2. Analyser les fichiers locaux
        print("\n📁 ÉTAPE 2: ANALYSE FICHIERS LOCAUX")
        local_issues = self.check_local_files()
        
        # 3. Comparer les données
        print("\n🔄 ÉTAPE 3: COMPARAISON DONNÉES")
        comparison_issues = self.compare_data_sources()
        
        # 4. Identifier les causes racines
        print("\n🎯 ÉTAPE 4: ANALYSE CAUSES RACINES")
        root_causes = self.analyze_root_causes()
        
        # 5. Générer le plan de correction
        print("\n🔧 ÉTAPE 5: PLAN DE CORRECTION")
        correction_plan = self.generate_correction_plan()
        
        # Rapport final
        report = {
            "diagnostic_date": datetime.now().isoformat(),
            "critical_score": self.calculate_critical_score(),
            "issues": {
                "mealie": mealie_issues,
                "local": local_issues,
                "comparison": comparison_issues,
                "root_causes": root_causes
            },
            "correction_plan": correction_plan,
            "status": "CRITICAL" if self.critical_issues else "OK"
        }
        
        # Afficher le résumé
        self.print_diagnostic_summary(report)
        
        return report
    
    def check_mealie_recipes(self) -> Dict:
        """Vérifie les recettes dans Mealie via MCP"""
        try:
            # Importer les outils MCP mealie-test
            from skills.recipe_importer_skill import list_imported, get_recipe_info
            
            recipes = list_imported()
            issues = []
            
            if not recipes.get("success"):
                return {
                    "error": "Impossible de lister les recettes Mealie",
                    "issues": [{"error": "Échec connexion Mealie", "severity": "HIGH"}]
                }
            
            recipe_list = recipes.get("recipes", [])
            print(f"   📊 Recettes trouvées dans Mealie: {len(recipe_list)}")
            
            for recipe in recipe_list[:5]:  # Limiter à 5 pour le diagnostic
                recipe_name = recipe.get("name", "Sans nom")
                slug = recipe.get("slug", "")
                
                print(f"   🔍 Analyse: {recipe_name}")
                
                # Obtenir les détails
                details = get_recipe_info(recipe_slug=slug)
                
                if not details.get("success"):
                    issues.append({
                        "recipe": recipe_name,
                        "slug": slug,
                        "issues": ["Impossible d'obtenir les détails"],
                        "severity": "HIGH"
                    })
                    continue
                
                recipe_data = details.get("recipe", {})
                
                # Vérifications critiques
                recipe_issues = []
                
                # 1. Vérifier les ingrédients
                ingredients = recipe_data.get("ingredients", [])
                if len(ingredients) < 3:
                    recipe_issues.append(f"Moins de 3 ingrédients: {len(ingredients)}")
                
                # 2. Vérifier si ce sont des vrais ingrédients
                generic_ingredients = ["ingrédient", "principal", "accompagnement", "varié"]
                generic_count = sum(1 for ing in ingredients 
                                 if any(generic in ing.lower() for generic in generic_ingredients))
                
                if generic_count > 0:
                    recipe_issues.append(f"{generic_count} ingrédients génériques")
                
                # 3. Vérifier les instructions
                instructions = recipe_data.get("instructions", [])
                if len(instructions) < 3:
                    recipe_issues.append(f"Moins de 3 instructions: {len(instructions)}")
                
                # 4. Vérifier si ce sont de vraies instructions
                generic_instructions = ["préparer", "cuire selon", "servir"]
                generic_inst_count = sum(1 for inst in instructions 
                                       if any(generic in inst.lower() for generic in generic_instructions))
                
                if generic_inst_count > 0:
                    recipe_issues.append(f"{generic_inst_count} instructions génériques")
                
                # 5. Vérifier la cohérence nom/contenu
                name_lower = recipe_name.lower()
                ingredients_text = " ".join(ingredients).lower()
                
                if "quiche" in name_lower and "lardon" not in ingredients_text:
                    recipe_issues.append("Quiche sans lardons - incohérent")
                
                if "tarte" in name_lower and "pomme" not in ingredients_text:
                    recipe_issues.append("Tarte sans pommes - incohérent")
                
                if recipe_issues:
                    issues.append({
                        "recipe": recipe_name,
                        "slug": slug,
                        "issues": recipe_issues,
                        "severity": "HIGH" if len(recipe_issues) >= 3 else "MEDIUM"
                    })
                    self.critical_issues.append(f"{recipe_name}: {', '.join(recipe_issues)}")
                else:
                    print(f"      ✅ {recipe_name}: OK")
            
            return {
                "total_recipes": len(recipe_list),
                "problematic_recipes": len(issues),
                "issues": issues
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "issues": [{"error": "Impossible de vérifier Mealie", "severity": "HIGH"}]
            }
    
    def check_local_files(self) -> Dict:
        """Vérifie les fichiers locaux"""
        issues = []
        
        # Vérifier le fichier structuré
        structured_file = Path(__file__).parent / "structured_data/latest_mealie_structured_recipes.json"
        
        if structured_file.exists():
            try:
                with open(structured_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                recipes = data.get("recipes", [])
                
                for recipe in recipes:
                    recipe_name = recipe.get("name", "")
                    ingredients = recipe.get("recipeIngredient", [])
                    instructions = recipe.get("recipeInstructions", [])
                    
                    recipe_issues = []
                    
                    # Vérifier les ingrédients
                    generic_ingredients = ["principal", "accompagnement", "varié"]
                    for ing in ingredients:
                        if isinstance(ing, dict):
                            food = ing.get("food", "").lower()
                            if any(generic in food for generic in generic_ingredients):
                                recipe_issues.append(f"Ingrédient générique: {food}")
                    
                    # Vérifier les instructions
                    for inst in instructions:
                        if isinstance(inst, dict):
                            text = inst.get("text", "").lower()
                            generic_instructions = ["préparer les ingrédients", "cuire selon", "servir chaud"]
                            if any(generic in text for generic in generic_instructions):
                                recipe_issues.append(f"Instruction générique: {text[:30]}...")
                    
                    if recipe_issues:
                        issues.append({
                            "recipe": recipe_name,
                            "issues": recipe_issues,
                            "severity": "HIGH"
                        })
                
            except Exception as e:
                issues.append({"error": f"Erreur lecture fichier structuré: {e}", "severity": "HIGH"})
        else:
            issues.append({"error": "Fichier structuré manquant", "severity": "HIGH"})
        
        return {
            "file_checked": str(structured_file),
            "issues": issues
        }
    
    def compare_data_sources(self) -> Dict:
        """Compare les sources de données"""
        issues = []
        
        # Vérifier la cohérence entre les fichiers
        files_to_check = [
            ("scraped", "scraped_data/latest_scraped_recipes_mcp.json"),
            ("structured", "structured_data/latest_mealie_structured_recipes.json"),
            ("import", "import_reports/latest_mealie_import_report.json")
        ]
        
        for file_type, file_path in files_to_check:
            path = Path(__file__).parent / file_path
            if not path.exists():
                issues.append({
                    "file_type": file_type,
                    "issue": f"Fichier {file_type} manquant",
                    "severity": "HIGH"
                })
        
        # Vérifier si les données sont synchronisées
        try:
            scraped_file = Path(__file__).parent / "scraped_data/latest_scraped_recipes_mcp.json"
            import_file = Path(__file__).parent / "import_reports/latest_mealie_import_report.json"
            
            if scraped_file.exists() and import_file.exists():
                with open(scraped_file, 'r') as f:
                    scraped_data = json.load(f)
                with open(import_file, 'r') as f:
                    import_data = json.load(f)
                
                scraped_count = scraped_data.get("metadata", {}).get("total_recipes", 0)
                imported_count = import_data.get("metadata", {}).get("total_imported", 0)
                
                if imported_count == 0 and scraped_count > 0:
                    issues.append({
                        "issue": f"Aucune importation alors que {scraped_count} recettes scrapées",
                        "severity": "HIGH"
                    })
                elif imported_count < scraped_count * 0.5:
                    issues.append({
                        "issue": f"Taux d'import faible: {imported_count}/{scraped_count}",
                        "severity": "MEDIUM"
                    })
        
        except Exception as e:
            issues.append({"error": f"Erreur comparaison: {e}", "severity": "MEDIUM"})
        
        return {"comparison_issues": issues}
    
    def analyze_root_causes(self) -> Dict:
        """Analyse les causes racines"""
        causes = []
        
        # Cause 1: Templates de scraping
        causes.append({
            "cause": "Templates de scraping génériques",
            "description": "Le scraper utilise des templates au lieu de scraper le vrai contenu",
            "impact": "HIGH",
            "evidence": "Ingrédients comme 'Ingrédient principal', 'Accomplement 1'"
        })
        
        # Cause 2: Parsing incomplet
        causes.append({
            "cause": "Parsing incomplet des recettes",
            "description": "Seule une partie des recettes est parsée correctement",
            "impact": "HIGH",
            "evidence": "Quiche Lorraine avec seulement la pâte brisée"
        })
        
        # Cause 3: Validation de qualité défaillante
        causes.append({
            "cause": "Validation de qualité défaillante",
            "description": "Le système de qualité donne de faux positifs",
            "impact": "HIGH",
            "evidence": "Score 86.8/100 mais recettes inutilisables"
        })
        
        # Cause 4: Simulation MCP
        causes.append({
            "cause": "Simulation des appels MCP",
            "description": "Les vrais appels MCP ne sont pas utilisés",
            "impact": "MEDIUM",
            "evidence": "Templates fixes au lieu de contenu réel"
        })
        
        return {"root_causes": causes}
    
    def generate_correction_plan(self) -> Dict:
        """Génère le plan de correction"""
        plan = {
            "immediate_actions": [
                {
                    "action": "Arrêter l'import actuel",
                    "priority": "URGENT",
                    "description": "Les recettes actuelles sont inutilisables"
                },
                {
                    "action": "Implémenter vrai scraping MCP",
                    "priority": "HIGH", 
                    "description": "Utiliser mcp2_read_url pour scraper le vrai contenu"
                },
                {
                    "action": "Corriger les templates de parsing",
                    "priority": "HIGH",
                    "description": "Créer des templates spécifiques par type de recette"
                }
            ],
            "medium_term_actions": [
                {
                    "action": "Améliorer la validation qualité",
                    "priority": "MEDIUM",
                    "description": "Détecter les ingrédients/instructions génériques"
                },
                {
                    "action": "Nettoyer les recettes existantes",
                    "priority": "MEDIUM",
                    "description": "Supprimer ou corriger les recettes inutilisables"
                }
            ],
            "validation_steps": [
                "Vérifier que chaque Quiche Lorraine a des lardons",
                "Vérifier que chaque Tarte Tatin a des pommes",
                "Vérifier que les instructions sont spécifiques",
                "Tester manuellement 5 recettes importées"
            ]
        }
        
        return plan
    
    def calculate_critical_score(self) -> int:
        """Calcule un score de criticité"""
        if len(self.critical_issues) == 0:
            return 100
        elif len(self.critical_issues) <= 2:
            return 60
        elif len(self.critical_issues) <= 5:
            return 30
        else:
            return 0
    
    def print_diagnostic_summary(self, report: Dict):
        """Affiche le résumé du diagnostic"""
        score = report["critical_score"]
        status = report["status"]
        
        print(f"\n🎯 RÉSUMÉ DU DIAGNOSTIC")
        print("=" * 50)
        print(f"📊 Score de criticité: {score}/100")
        print(f"🚨 Statut: {status}")
        print(f"📋 Problèmes critiques: {len(self.critical_issues)}")
        
        if self.critical_issues:
            print(f"\n🚨 PROBLÈMES CRITIQUES:")
            for i, issue in enumerate(self.critical_issues[:5], 1):
                print(f"   {i}. {issue}")
        
        print(f"\n🔧 ACTIONS IMMÉDIATES:")
        for action in report["correction_plan"]["immediate_actions"][:3]:
            print(f"   • {action['action']} ({action['priority']})")
        
        if score < 50:
            print(f"\n⚠️ RECOMMANDATION: ARRÊTER L'IMPORT ET CORRIGER AVANT DE CONTINUER")
        else:
            print(f"\n✅ RECOMMANDATION: CONTINUER AVEC PRUDENCE")

if __name__ == "__main__":
    diagnostic = CriticalImportDiagnostic()
    report = diagnostic.run_critical_diagnostic()
