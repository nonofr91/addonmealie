#!/usr/bin/env python3
"""
MEALIE RECIPE DELETER
Suppression directe des recettes Mealie via MCP
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Importer le wrapper MCP authentifié pour rendre les fonctions disponibles
sys.path.append(str(Path(__file__).parent))
from mcp_auth_wrapper import *

def list_mealie_recipes():
    """Liste les recettes Mealie via MCP"""
    try:
        # Utiliser directement mcp3_list_recipes sans import
        recipes = mcp3_list_recipes()
        return recipes
        
    except NameError:
        print("❌ MCP mcp3_list_recipes non disponible")
        return []
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

def delete_mealie_recipe(recipe_slug: str) -> bool:
    """Supprime une recette Mealie via MCP"""
    try:
        # Utiliser le nouveau MCP de suppression
        result = delete_recipe(recipe_slug)
        return result.get("success", False)
        
    except NameError:
        print("❌ MCP delete_recipe non disponible")
        return False
    except Exception as e:
        print(f"❌ Erreur suppression: {e}")
        return False

def get_recipe_details(recipe_slug: str):
    """Obtient les détails d'une recette"""
    try:
        # Utiliser directement mcp3_get_recipe_details sans import
        details = mcp3_get_recipe_details(recipe_slug)
        return details
        
    except NameError:
        print("❌ MCP mcp3_get_recipe_details non disponible")
        return None
    except Exception as e:
        print(f"❌ Erreur détails: {e}")
        return None

def analyze_recipe_quality(recipe_slug: str) -> dict:
    """Analyse la qualité d'une recette"""
    details = get_recipe_details(recipe_slug)
    
    if not details:
        return {"error": "Impossible d'obtenir les détails"}
    
    ingredients = details.get("ingredients", [])
    instructions = details.get("instructions", [])
    name = details.get("name", "")
    
    issues = []
    
    # Vérifier les ingrédients
    if len(ingredients) < 3:
        issues.append("Moins de 3 ingrédients")
    
    # Vérifier si ce sont des vrais ingrédients
    generic_ingredients = ["farine", "beurre", "sel", "eau", "principal", "accompagnement"]
    generic_count = sum(1 for ing in ingredients 
                       if any(generic in ing.lower() for generic in generic_ingredients))
    
    if generic_count > 0:
        issues.append(f"{generic_count} ingrédients génériques")
    
    # Vérifier les instructions
    if len(instructions) < 3:
        issues.append("Moins de 3 instructions")
    
    # Vérifier la cohérence nom/contenu
    name_lower = name.lower()
    ingredients_text = " ".join(ingredients).lower()
    
    if "quiche" in name_lower and "lardon" not in ingredients_text:
        issues.append("Quiche sans lardons")
    
    if "tarte" in name_lower and "pomme" not in ingredients_text:
        issues.append("Tarte sans pommes")
    
    if "bœuf" in name_lower or "boeuf" in name_lower:
        if "bœuf" not in ingredients_text and "boeuf" not in ingredients_text:
            issues.append("Bœuf bourguignon sans bœuf")
    
    # Calculer un score de qualité
    score = 100
    score -= len(issues) * 10
    score = max(0, score)
    
    return {
        "name": name,
        "slug": recipe_slug,
        "ingredients_count": len(ingredients),
        "instructions_count": len(instructions),
        "issues": issues,
        "quality_score": score,
        "should_delete": len(issues) >= 3
    }

def interactive_recipe_manager():
    """Gestionnaire interactif de recettes"""
    print("🗑️ GESTIONNAIRE DE RECETTES MEALIE")
    print("Suppression et analyse des recettes")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Lister toutes les recettes")
        print("2. Analyser la qualité des recettes")
        print("3. Supprimer une recette spécifique")
        print("4. Nettoyer les recettes de mauvaise qualité")
        print("5. Quitter")
        
        try:
            choice = input("\nVotre choix (1-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Au revoir !")
            break
        
        if choice == "1":
            list_all_recipes()
        
        elif choice == "2":
            analyze_all_recipes()
        
        elif choice == "3":
            delete_specific_recipe()
        
        elif choice == "4":
            cleanup_bad_recipes()
        
        elif choice == "5":
            print("👋 Au revoir !")
            break
        
        else:
            print("❌ Choix invalide")

def list_all_recipes():
    """Liste toutes les recettes"""
    print("\n📋 LISTE DES RECETTES")
    print("-" * 30)
    
    recipes = list_mealie_recipes()
    
    if not recipes:
        print("📭 Aucune recette trouvée")
        return
    
    print(f"Total: {len(recipes)} recettes\n")
    
    for i, recipe in enumerate(recipes, 1):
        name = recipe.get("name", "Sans nom")
        slug = recipe.get("slug", "")
        
        print(f"{i:2d}. {name}")
        print(f"     📝 Slug: {slug}")

def analyze_all_recipes():
    """Analyse la qualité de toutes les recettes"""
    print("\n🔍 ANALYSE DE QUALITÉ")
    print("-" * 30)
    
    recipes = list_mealie_recipes()
    
    if not recipes:
        print("📭 Aucune recette à analyser")
        return
    
    analysis_results = []
    
    for recipe in recipes:
        slug = recipe.get("slug", "")
        if slug:
            analysis = analyze_recipe_quality(slug)
            analysis_results.append(analysis)
    
    # Afficher les résultats
    print(f"\n📊 RÉSULTATS D'ANALYSE ({len(analysis_results)} recettes)")
    print("-" * 50)
    
    good_recipes = []
    bad_recipes = []
    
    for result in analysis_results:
        if "error" in result:
            continue
            
        if result["should_delete"]:
            bad_recipes.append(result)
        else:
            good_recipes.append(result)
    
    print(f"✅ Recettes de bonne qualité: {len(good_recipes)}")
    print(f"❌ Recettes de mauvaise qualité: {len(bad_recipes)}")
    
    if bad_recipes:
        print(f"\n🚨 RECETTES À SUPPRIMER:")
        for recipe in bad_recipes:
            name = recipe["name"]
            score = recipe["quality_score"]
            issues = ", ".join(recipe["issues"])
            print(f"   ❌ {name} (Score: {score}/100)")
            print(f"      🐛 Problèmes: {issues}")

def delete_specific_recipe():
    """Supprime une recette spécifique"""
    print("\n🗑️ SUPPRESSION SPÉCIFIQUE")
    print("-" * 30)
    
    recipes = list_mealie_recipes()
    
    if not recipes:
        print("📭 Aucune recette à supprimer")
        return
    
    print("Recettes disponibles:")
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
            
            # Analyser avant suppression
            analysis = analyze_recipe_quality(slug)
            if "issues" in analysis:
                issues = ", ".join(analysis["issues"])
                print(f"🐛 Problèmes détectés: {issues}")
                print(f"🎯 Score de qualité: {analysis['quality_score']}/100")
            
            confirm = input("Confirmer la suppression (oui/non): ").strip().lower()
            
            if confirm in ["oui", "o", "yes", "y"]:
                success = delete_mealie_recipe(slug)
                
                if success:
                    print("✅ Recette supprimée avec succès")
                else:
                    print("❌ Erreur lors de la suppression")
            else:
                print("❌ Suppression annulée")
        else:
            print("❌ Choix invalide")
            
    except ValueError:
        print("❌ Entrée invalide")

def cleanup_bad_recipes():
    """Nettoie les recettes de mauvaise qualité"""
    print("\n🧹 NETTOYAGE AUTOMATIQUE")
    print("-" * 30)
    
    recipes = list_mealie_recipes()
    
    if not recipes:
        print("📭 Aucune recette à nettoyer")
        return
    
    # Analyser toutes les recettes
    bad_recipes = []
    
    for recipe in recipes:
        slug = recipe.get("slug", "")
        if slug:
            analysis = analyze_recipe_quality(slug)
            if analysis.get("should_delete"):
                bad_recipes.append({
                    "recipe": recipe,
                    "analysis": analysis
                })
    
    if not bad_recipes:
        print("✅ Aucune recette de mauvaise qualité trouvée")
        return
    
    print(f"🚨 {len(bad_recipes)} recettes de mauvaise qualité trouvées:")
    
    for item in bad_recipes:
        recipe = item["recipe"]
        analysis = item["analysis"]
        name = recipe.get("name", "Sans nom")
        score = analysis["quality_score"]
        issues = ", ".join(analysis["issues"])
        
        print(f"\n❌ {name}")
        print(f"   🎯 Score: {score}/100")
        print(f"   🐛 Problèmes: {issues}")
    
    # Demander confirmation
    print(f"\n⚠️ Voulez-vous supprimer ces {len(bad_recipes)} recettes ?")
    confirm = input("Confirmer le nettoyage (oui/non): ").strip().lower()
    
    if confirm in ["oui", "o", "yes", "y"]:
        deleted_count = 0
        
        for item in bad_recipes:
            recipe = item["recipe"]
            slug = recipe.get("slug", "")
            name = recipe.get("name", "Sans nom")
            
            success = delete_mealie_recipe(slug)
            if success:
                deleted_count += 1
                print(f"   ✅ {name} supprimée")
            else:
                print(f"   ❌ {name} - erreur suppression")
        
        print(f"\n🎯 Nettoyage terminé: {deleted_count}/{len(bad_recipes)} recettes supprimées")
    else:
        print("❌ Nettoyage annulé")

if __name__ == "__main__":
    interactive_recipe_manager()
