#!/usr/bin/env python3
"""
TEST DE VALIDATION DES CORRECTIONS MCP
Vérifie que les corrections MCP fonctionnent correctement
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

def test_scraper_improvements():
    """Test les améliorations du scraper"""
    print("🧪 TEST DES AMÉLIORATIONS SCRAPER")
    print("=" * 50)
    
    from src.scraping.recipe_scraper_mcp import RecipeScraperMCP
    
    scraper = RecipeScraperMCP()
    
    # Test URLs
    test_urls = [
        "https://www.marmiton.org/recettes/quiche-lorraine",
        "https://www.meilleurduchef.com/fr/recette/boeuf-bourguignon.html",
        "https://www.750g.com/recette/tarte-tatin.html"
    ]
    
    results = []
    
    for url in test_urls:
        print(f"\n🔍 Test: {url}")
        result = scraper.extract_recipe_content(url)
        
        if result:
            print(f"   ✅ Succès: {result['name']}")
            print(f"      📊 Ingrédients: {len(result['ingredients'])}")
            print(f"      📝 Instructions: {len(result['instructions'])}")
            print(f"      🍽️ Type: {result['recipe_type']}")
            
            # Validation de la qualité
            quality_score = validate_recipe_quality(result)
            print(f"      🎯 Qualité: {quality_score}/100")
            
            results.append({
                "url": url,
                "success": True,
                "recipe": result,
                "quality": quality_score
            })
        else:
            print(f"   ❌ Échec")
            results.append({
                "url": url,
                "success": False,
                "recipe": None,
                "quality": 0
            })
    
    return results

def validate_recipe_quality(recipe: dict) -> int:
    """Valide la qualité d'une recette"""
    score = 0
    
    # Nom (20 points)
    if recipe.get('name') and len(recipe['name']) > 3:
        score += 20
    
    # Ingrédients (30 points)
    ingredients = recipe.get('ingredients', [])
    if len(ingredients) >= 5:
        score += 15
    if len(ingredients) >= 8:
        score += 15
    
    # Vérifier ingrédients spécifiques
    recipe_type = recipe.get('recipe_type', '')
    if 'quiche' in recipe_type.lower():
        # Quiche doit avoir lardons, œufs, crème
        ingredients_text = ' '.join(ingredients).lower()
        if 'lardon' in ingredients_text:
            score += 5
        if 'œuf' in ingredients_text or 'oeuf' in ingredients_text:
            score += 5
        if 'crème' in ingredients_text:
            score += 5
    
    # Instructions (30 points)
    instructions = recipe.get('instructions', [])
    if len(instructions) >= 5:
        score += 15
    if len(instructions) >= 8:
        score += 15
    
    # Vérifier instructions spécifiques
    instructions_text = ' '.join(instructions).lower()
    if 'cuire' in instructions_text:
        score += 5
    if 'préparer' in instructions_text:
        score += 5
    
    # Métadonnées (20 points)
    if recipe.get('prep_time') and recipe.get('cook_time'):
        score += 10
    if recipe.get('servings'):
        score += 5
    if recipe.get('image') and not recipe['image'].startswith('scraped_images/'):
        score += 5
    
    return min(100, score)

def test_importer_improvements():
    """Test les améliorations de l'importateur"""
    print("\n🧪 TEST DES AMÉLIORATIONS IMPORTATEUR")
    print("=" * 50)
    
    from src.importing.mealie_importer_mcp import MealieImporterMCP
    
    importer = MealieImporterMCP()
    
    # Charger les données scrapées
    scraped_file = Path(__file__).parent / "scraped_data/latest_scraped_recipes_mcp.json"
    
    if scraped_file.exists():
        with open(scraped_file, 'r', encoding='utf-8') as f:
            scraped_data = json.load(f)
        
        recipes = scraped_data.get('recipes', [])
        print(f"📊 Recettes scrapées: {len(recipes)}")
        
        # Tester l'import
        import_results = []
        
        for recipe in recipes[:2]:  # Limiter à 2 pour le test
            result = importer.import_recipe_to_mealie(recipe)
            
            if result:
                print(f"   ✅ Import réussi: {recipe['name']}")
                import_results.append({
                    "recipe_name": recipe['name'],
                    "success": True,
                    "recipe_id": result
                })
            else:
                print(f"   ❌ Import échoué: {recipe['name']}")
                import_results.append({
                    "recipe_name": recipe['name'],
                    "success": False,
                    "recipe_id": None
                })
        
        return import_results
    else:
        print("❌ Fichier scrapé non trouvé")
        return []

def test_workflow_integration():
    """Test l'intégration complète du workflow"""
    print("\n🧪 TEST D'INTÉGRATION WORKFLOW")
    print("=" * 50)
    
    from workflow_orchestrator import MealieWorkflowOrchestrator
    
    orchestrator = MealieWorkflowOrchestrator()
    
    # Lancer le workflow avec la bonne méthode
    result = orchestrator.run_complete_workflow()
    
    if result.get('success'):
        print("✅ Workflow complet réussi")
        print(f"   📊 Recettes scrapées: {result.get('scraped_count', 0)}")
        print(f"   📝 Recettes structurées: {result.get('structured_count', 0)}")
        print(f"   📥 Recettes importées: {result.get('imported_count', 0)}")
        print(f"   📁 Rapport: {result.get('report_file', 'N/A')}")
    else:
        print("❌ Workflow échoué")
        print(f"   Erreur: {result.get('error', 'Inconnue')}")
    
    return result

def generate_validation_report(scraper_results, importer_results, workflow_result):
    """Génère un rapport de validation"""
    print("\n📋 RAPPORT DE VALIDATION")
    print("=" * 50)
    
    # Statistiques scraper
    successful_scrapes = sum(1 for r in scraper_results if r['success'])
    avg_quality = sum(r['quality'] for r in scraper_results if r['success']) / len(scraper_results) if scraper_results else 0
    
    print(f"🔍 SCRAPER:")
    print(f"   ✅ Succès: {successful_scrapes}/{len(scraper_results)} ({successful_scrapes/len(scraper_results)*100:.1f}%)")
    print(f"   🎯 Qualité moyenne: {avg_quality:.1f}/100")
    
    # Statistiques importer
    successful_imports = sum(1 for r in importer_results if r['success'])
    print(f"\n📥 IMPORTATEUR:")
    print(f"   ✅ Succès: {successful_imports}/{len(importer_results)} ({successful_imports/len(importer_results)*100:.1f}%)")
    
    # Statistiques workflow
    workflow_success = workflow_result.get('success', False)
    print(f"\n🔄 WORKFLOW:")
    print(f"   ✅ Succès: {'Oui' if workflow_success else 'Non'}")
    
    # Validation des recettes
    print(f"\n🍽️ VALIDATION RECETTES:")
    for result in scraper_results:
        if result['success']:
            recipe = result['recipe']
            name = recipe['name']
            ingredients = len(recipe['ingredients'])
            instructions = len(recipe['instructions'])
            quality = result['quality']
            
            print(f"   📖 {name}:")
            print(f"      🥘 Ingrédients: {ingredients}")
            print(f"      📝 Instructions: {instructions}")
            print(f"      🎯 Qualité: {quality}/100")
            
            # Validation spécifique
            if 'quiche' in name.lower():
                ingredients_text = ' '.join(recipe['ingredients']).lower()
                has_lardons = 'lardon' in ingredients_text
                has_eggs = 'œuf' in ingredients_text or 'oeuf' in ingredients_text
                has_cream = 'crème' in ingredients_text
                
                print(f"      ✅ Lardons: {'Oui' if has_lardons else '❌'}")
                print(f"      ✅ Œufs: {'Oui' if has_eggs else '❌'}")
                print(f"      ✅ Crème: {'Oui' if has_cream else '❌'}")
    
    # Conclusion
    print(f"\n🎯 CONCLUSION:")
    if avg_quality >= 80 and successful_imports >= len(importer_results) * 0.8:
        print("   ✅ CORRECTIONS MCP RÉUSSIES")
        print("   🎉 Les recettes sont maintenant de qualité !")
    else:
        print("   ⚠️ CORRECTIONS PARTIELLES")
        print("   🔧 Améliorations supplémentaires nécessaires")
    
    # Sauvegarder le rapport
    report = {
        "validation_date": str(Path(__file__).parent),
        "scraper_results": scraper_results,
        "importer_results": importer_results,
        "workflow_result": workflow_result,
        "statistics": {
            "scraper_success_rate": successful_scrapes / len(scraper_results) if scraper_results else 0,
            "average_quality": avg_quality,
            "importer_success_rate": successful_imports / len(importer_results) if importer_results else 0,
            "workflow_success": workflow_success
        }
    }
    
    report_file = Path(__file__).parent / "validation_reports" / f"mcp_correction_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📁 Rapport sauvegardé: {report_file}")

if __name__ == "__main__":
    print("🚀 VALIDATION DES CORRECTIONS MCP SKILLS")
    print("🔧 Test des vrais MCP et IA intelligente")
    print("=" * 60)
    
    # Tests
    scraper_results = test_scraper_improvements()
    importer_results = test_importer_improvements()
    workflow_result = test_workflow_integration()
    
    # Rapport
    generate_validation_report(scraper_results, importer_results, workflow_result)
