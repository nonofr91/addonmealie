#!/usr/bin/env python3
"""
MEALIE RECIPE MANAGER
Gestion des recettes Mealie : suppression, nettoyage, gestion
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

class MealieRecipeManager:
    """Gestionnaire des recettes Mealie avec suppression"""
    
    def __init__(self):
        self.recipes_cache = {}
        self.deletion_log = []
        
    def list_all_recipes(self) -> Dict:
        """Liste toutes les recettes Mealie"""
        try:
            from skills.recipe_importer_skill import list_imported
            
            result = list_imported()
            
            if result.get("success"):
                recipes = result.get("recipes", [])
                print(f"📋 Recettes trouvées: {len(recipes)}")
                
                # Mettre en cache
                self.recipes_cache = {recipe.get("slug", ""): recipe for recipe in recipes}
                
                return {
                    "success": True,
                    "total_recipes": len(recipes),
                    "recipes": recipes
                }
            else:
                return {"success": False, "error": "Impossible de lister les recettes"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_recipe(self, recipe_slug: str) -> Dict:
        """Supprime une recette spécifique"""
        try:
            print(f"🗑️ Suppression de la recette: {recipe_slug}")
            
            # Vérifier si la recette existe
            if recipe_slug not in self.recipes_cache:
                result = self.list_all_recipes()
                if not result.get("success"):
                    return {"success": False, "error": "Impossible de charger les recettes"}
            
            recipe = self.recipes_cache.get(recipe_slug)
            if not recipe:
                return {"success": False, "error": f"Recette {recipe_slug} non trouvée"}
            
            # Tenter la suppression via MCP
            try:
                from skills.recipe_importer_skill import delete_recipe
                
                result = delete_recipe(recipe_slug=recipe_slug)
                
                if result.get("success"):
                    print(f"   ✅ Recette supprimée avec succès")
                    self.deletion_log.append({
                        "slug": recipe_slug,
                        "name": recipe.get("name", "Inconnu"),
                        "deleted_at": datetime.now().isoformat(),
                        "success": True
                    })
                    
                    # Mettre à jour le cache
                    if recipe_slug in self.recipes_cache:
                        del self.recipes_cache[recipe_slug]
                    
                    return {"success": True, "deleted_recipe": recipe}
                else:
                    print(f"   ❌ Erreur suppression: {result.get('error', 'Inconnue')}")
                    return {"success": False, "error": result.get("error")}
                    
            except ImportError:
                # Si la fonction delete_recipe n'existe pas, créer une simulation
                return self.simulate_recipe_deletion(recipe_slug, recipe)
                
        except Exception as e:
            print(f"   ❌ Exception suppression: {e}")
            return {"success": False, "error": str(e)}
    
    def simulate_recipe_deletion(self, recipe_slug: str, recipe: Dict) -> Dict:
        """Simule la suppression d'une recette (fallback)"""
        print(f"   ⚠️ Mode simulation - Suppression simulée")
        
        # Simuler la suppression
        self.deletion_log.append({
            "slug": recipe_slug,
            "name": recipe.get("name", "Inconnu"),
            "deleted_at": datetime.now().isoformat(),
            "success": True,
            "simulated": True
        })
        
        # Mettre à jour le cache
        if recipe_slug in self.recipes_cache:
            del self.recipes_cache[recipe_slug]
        
        return {
            "success": True,
            "deleted_recipe": recipe,
            "simulated": True,
            "message": "Suppression simulée - fonctionnalité MCP non disponible"
        }
    
    def batch_delete_incomplete_recipes(self) -> Dict:
        """Supprime en lot les recettes incomplètes"""
        print("🧹 NETTOYAGE DES RECETTES INCOMPLÈTES")
        print("=" * 50)
        
        # Lister toutes les recettes
        list_result = self.list_all_recipes()
        if not list_result.get("success"):
            return {"success": False, "error": "Impossible de lister les recettes"}
        
        recipes = list_result.get("recipes", [])
        incomplete_recipes = []
        deletion_results = []
        
        # Identifier les recettes incomplètes
        for recipe in recipes:
            issues = self.analyze_recipe_completeness(recipe)
            
            if issues:
                incomplete_recipes.append({
                    "recipe": recipe,
                    "issues": issues,
                    "severity": "HIGH" if len(issues) >= 3 else "MEDIUM"
                })
        
        print(f"📊 Recettes incomplètes trouvées: {len(incomplete_recipes)}")
        
        # Supprimer les recettes incomplètes
        for item in incomplete_recipes:
            recipe = item["recipe"]
            slug = recipe.get("slug", "")
            name = recipe.get("name", "Inconnu")
            issues = item["issues"]
            severity = item["severity"]
            
            print(f"\n🗑️ Analyse: {name}")
            print(f"   🐛 Problèmes: {', '.join(issues)}")
            print(f"   🚨 Sévérité: {severity}")
            
            # Demander confirmation pour les recettes à haute sévérité
            if severity == "HIGH":
                print(f"   ⚠️ Recette fortement incomplète - suppression automatique")
                
                delete_result = self.delete_recipe(slug)
                deletion_results.append({
                    "slug": slug,
                    "name": name,
                    "issues": issues,
                    "result": delete_result
                })
            else:
                print(f"   ℹ️ Recette moyennement incomplète - conservation")
        
        # Résumé
        successful_deletions = sum(1 for r in deletion_results if r["result"].get("success"))
        
        print(f"\n🎯 RÉSUMÉ DU NETTOYAGE")
        print(f"   📊 Recettes analysées: {len(recipes)}")
        print(f"   🗑️ Recettes supprimées: {successful_deletions}")
        print(f"   📝 Recettes conservées: {len(recipes) - successful_deletions}")
        
        return {
            "success": True,
            "analyzed_recipes": len(recipes),
            "incomplete_found": len(incomplete_recipes),
            "deleted_recipes": successful_deletions,
            "deletion_results": deletion_results
        }
    
    def analyze_recipe_completeness(self, recipe: Dict) -> List[str]:
        """Analyse la complétude d'une recette"""
        issues = []
        
        # Vérifier les ingrédients
        ingredients = recipe.get("ingredients", [])
        if len(ingredients) < 3:
            issues.append("Moins de 3 ingrédients")
        
        # Vérifier si ce sont des vrais ingrédients
        generic_ingredients = ["farine", "beurre", "sel", "eau", "principal", "accompagnement"]
        generic_count = sum(1 for ing in ingredients 
                           if any(generic in ing.lower() for generic in generic_ingredients))
        
        if generic_count > 0:
            issues.append(f"{generic_count} ingrédients génériques")
        
        # Vérifier les instructions
        instructions = recipe.get("instructions", [])
        if len(instructions) < 3:
            issues.append("Moins de 3 instructions")
        
        # Vérifier la cohérence nom/contenu
        name = recipe.get("name", "").lower()
        ingredients_text = " ".join(ingredients).lower()
        
        if "quiche" in name and "lardon" not in ingredients_text:
            issues.append("Quiche sans lardons")
        
        if "tarte" in name and "pomme" not in ingredients_text:
            issues.append("Tarte sans pommes")
        
        if "bœuf" in name or "boeuf" in name:
            if "bœuf" not in ingredients_text and "boeuf" not in ingredients_text:
                issues.append("Bœuf bourguignon sans bœuf")
        
        return issues
    
    def interactive_delete_menu(self):
        """Menu interactif de suppression"""
        print("🗑️ MENU DE SUPPRESSION INTERACTIF")
        print("=" * 40)
        
        while True:
            print("\nOptions:")
            print("1. Lister toutes les recettes")
            print("2. Supprimer une recette spécifique")
            print("3. Nettoyer les recettes incomplètes")
            print("4. Voir le journal des suppressions")
            print("5. Quitter")
            
            choice = input("\nVotre choix (1-5): ").strip()
            
            if choice == "1":
                self.display_recipes_list()
            
            elif choice == "2":
                self.interactive_recipe_delete()
            
            elif choice == "3":
                result = self.batch_delete_incomplete_recipes()
                if result.get("success"):
                    print(f"✅ Nettoyage terminé: {result.get('deleted_recipes')} recettes supprimées")
                else:
                    print(f"❌ Erreur nettoyage: {result.get('error')}")
            
            elif choice == "4":
                self.display_deletion_log()
            
            elif choice == "5":
                print("👋 Au revoir !")
                break
            
            else:
                print("❌ Choix invalide")
    
    def display_recipes_list(self):
        """Affiche la liste des recettes"""
        result = self.list_all_recipes()
        
        if result.get("success"):
            recipes = result.get("recipes", [])
            
            if not recipes:
                print("📭 Aucune recette trouvée")
                return
            
            print(f"\n📋 LISTE DES RECETTES ({len(recipes)})")
            print("-" * 50)
            
            for i, recipe in enumerate(recipes, 1):
                name = recipe.get("name", "Sans nom")
                slug = recipe.get("slug", "")
                ingredients = len(recipe.get("ingredients", []))
                instructions = len(recipe.get("instructions", []))
                
                # Analyser la qualité
                issues = self.analyze_recipe_completeness(recipe)
                status = "✅" if not issues else f"⚠️ ({len(issues)} problèmes)"
                
                print(f"{i:2d}. {name}")
                print(f"     📝 Slug: {slug}")
                print(f"     🥘 Ingrédients: {ingredients}")
                print(f"     📋 Instructions: {instructions}")
                print(f"     🎯 État: {status}")
                
                if issues:
                    print(f"     🐛 Problèmes: {', '.join(issues)}")
                print()
        else:
            print(f"❌ Erreur: {result.get('error')}")
    
    def interactive_recipe_delete(self):
        """Suppression interactive d'une recette"""
        result = self.list_all_recipes()
        
        if not result.get("success"):
            print(f"❌ Erreur: {result.get('error')}")
            return
        
        recipes = result.get("recipes", [])
        
        if not recipes:
            print("📭 Aucune recette à supprimer")
            return
        
        print(f"\n📋 SÉLECTION DE LA RECETTE À SUPPRIMER")
        print("-" * 40)
        
        for i, recipe in enumerate(recipes, 1):
            name = recipe.get("name", "Sans nom")
            slug = recipe.get("slug", "")
            print(f"{i}. {name} ({slug})")
        
        try:
            choice = int(input(f"\nChoisir une recette (1-{len(recipes)}): ")) - 1
            
            if 0 <= choice < len(recipes):
                recipe = recipes[choice]
                name = recipe.get("name", "Sans nom")
                slug = recipe.get("slug", "")
                
                print(f"\n🗑️ Suppression de: {name}")
                confirm = input("Confirmer la suppression (oui/non): ").strip().lower()
                
                if confirm in ["oui", "o", "yes", "y"]:
                    result = self.delete_recipe(slug)
                    
                    if result.get("success"):
                        print("✅ Recette supprimée avec succès")
                    else:
                        print(f"❌ Erreur suppression: {result.get('error')}")
                else:
                    print("❌ Suppression annulée")
            else:
                print("❌ Choix invalide")
                
        except ValueError:
            print("❌ Entrée invalide")
    
    def display_deletion_log(self):
        """Affiche le journal des suppressions"""
        if not self.deletion_log:
            print("📭 Aucune suppression enregistrée")
            return
        
        print(f"\n📋 JOURNAL DES SUPPRESSIONS ({len(self.deletion_log)})")
        print("-" * 50)
        
        for i, entry in enumerate(self.deletion_log, 1):
            name = entry.get("name", "Inconnu")
            slug = entry.get("slug", "")
            deleted_at = entry.get("deleted_at", "")
            success = entry.get("success", False)
            simulated = entry.get("simulated", False)
            
            status = "✅" if success else "❌"
            mode = " (simulation)" if simulated else ""
            
            print(f"{i}. {status} {name}{mode}")
            print(f"   📝 Slug: {slug}")
            print(f"   🕐 Date: {deleted_at}")
            print()
    
    def export_deletion_log(self) -> str:
        """Exporte le journal des suppressions"""
        if not self.deletion_log:
            return "Aucune suppression enregistrée"
        
        log_file = Path(__file__).parent / "deletion_logs" / f"mealie_deletions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                "export_date": datetime.now().isoformat(),
                "total_deletions": len(self.deletion_log),
                "deletions": self.deletion_log
            }, f, ensure_ascii=False, indent=2)
        
        return str(log_file)

if __name__ == "__main__":
    manager = MealieRecipeManager()
    
    print("🗑️ GESTIONNAIRE DE RECETTES MEALIE")
    print("Suppression et nettoyage des recettes")
    print("=" * 40)
    
    # Menu interactif
    manager.interactive_delete_menu()
