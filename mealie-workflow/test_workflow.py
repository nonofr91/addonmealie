#!/usr/bin/env python3
"""
TEST DU WORKFLOW MEALIE
Test complet du workflow de scraping à l'import
"""

import sys
import time
from pathlib import Path

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

from workflow_orchestrator import run_full_workflow, get_workflow_status, save_workflow_report

def test_complete_workflow():
    """Test le workflow complet"""
    print("🧪 TEST COMPLET DU WORKFLOW MEALIE")
    print("=" * 60)
    
    try:
        # Lancer le workflow complet
        print("🚀 Lancement du workflow complet...")
        start_time = time.time()
        
        result = run_full_workflow()
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        print(f"\n⏱️ Test terminé en {test_duration:.2f} secondes")
        
        # Analyser les résultats
        if result.get('success'):
            print("✅ SUCCÈS DU WORKFLOW!")
            
            # Afficher les statistiques
            workflow = result.get('workflow', {})
            results = result.get('results', {})
            
            print(f"\n📊 STATISTIQUES:")
            print(f"   ⏱️ Temps total: {workflow.get('total_time', 0):.1f}s")
            print(f"   🔍 Scraping: {results.get('scraping', {}).get('total_recipes', 0)} recettes")
            print(f"   🔧 Structuration: {results.get('structuring', {}).get('total_recipes', 0)} recettes")
            print(f"   📥 Import: {results.get('importing', {}).get('total_imported', 0)} recettes")
            
            # Afficher les fichiers générés
            files = result.get('files', {})
            print(f"\n📁 FICHIERS GÉNÉRÉS:")
            print(f"   📄 Scraped: {files.get('scraped', 'N/A')}")
            print(f"   📄 Structured: {files.get('structured', 'N/A')}")
            print(f"   📄 Import Report: {files.get('import_report', 'N/A')}")
            
            # Sauvegarder le rapport de test
            report_file = save_workflow_report(result)
            if report_file:
                print(f"\n📋 Rapport de test: {report_file}")
            
            return True
        else:
            print("❌ ÉCHEC DU WORKFLOW!")
            print(f"   Erreur: {result.get('error', 'Inconnue')}")
            print(f"   Étape: {result.get('step', 'Inconnue')}")
            print(f"   Message: {result.get('message', 'Pas de message')}")
            
            return False
            
    except Exception as e:
        print(f"❌ ERREUR DE TEST: {e}")
        return False

def test_step_by_step():
    """Test les étapes individuellement"""
    print("\n🧪 TEST ÉTAPE PAR ÉTAPE")
    print("=" * 60)
    
    from workflow_orchestrator import run_workflow_step
    
    steps = ['scraping', 'structuring', 'importing']
    
    for step in steps:
        print(f"\n🔧 Test de l'étape: {step}")
        print("-" * 40)
        
        try:
            step_start = time.time()
            result = run_workflow_step(step)
            step_time = time.time() - step_start
            
            if result.get('success'):
                print(f"✅ {step} réussi en {step_time:.1f}s")
                print(f"   📊 Résultat: {result.get('message', 'OK')}")
            else:
                print(f"❌ {step} échoué")
                print(f"   Erreur: {result.get('error', 'Inconnue')}")
                break
                
        except Exception as e:
            print(f"❌ Erreur test {step}: {e}")
            break

def test_skills_individually():
    """Test les skills MCP individuellement"""
    print("\n🧪 TEST DES SKILLS MCP")
    print("=" * 60)
    
    # Test Recipe Scraper Skill
    print("\n🔍 TEST: Recipe Scraper Skill")
    try:
        from skills.recipe_scraper_skill import list_sources, scrape_recipes, get_scraping_info
        
        # Lister les sources
        sources = list_sources()
        print(f"   📊 Sources: {sources.get('success', False)}")
        
        # Scraper (test avec peu de sources)
        scrape_result = scrape_recipes(['marmiton'])
        print(f"   🔧 Scraping: {scrape_result.get('success', False)}")
        
        # Statistiques
        stats = get_scraping_info()
        print(f"   📈 Stats: {stats.get('success', False)}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test Data Structurer Skill
    print("\n🔧 TEST: Data Structurer Skill")
    try:
        from skills.data_structurer_skill import structure_data, get_structure_info, validate_mealie_data
        
        # Structurer (si des données scrapées existent)
        structure_result = structure_data("scraped_data/latest_scraped_recipes_mcp.json")
        print(f"   🔧 Structuration: {structure_result.get('success', False)}")
        
        # Statistiques
        stats = get_structure_info()
        print(f"   📈 Stats: {stats.get('success', False)}")
        
        # Validation
        validation = validate_mealie_data()
        print(f"   ✅ Validation: {validation.get('success', False)}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test Recipe Importer Skill
    print("\n📥 TEST: Recipe Importer Skill")
    try:
        from skills.recipe_importer_skill import import_recipes, get_import_info, list_imported
        
        # Importer (si des données structurées existent)
        import_result = import_recipes("structured_data/latest_mealie_structured_recipes.json")
        print(f"   📥 Import: {import_result.get('success', False)}")
        
        # Statistiques
        stats = get_import_info()
        print(f"   📈 Stats: {stats.get('success', False)}")
        
        # Liste
        imported_list = list_imported()
        print(f"   📋 Liste: {imported_list.get('success', False)}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def main():
    """Fonction principale de test"""
    print("🎯 SUITE DE TESTS DU WORKFLOW MEALIE")
    print("📋 Test complet du système de scraping à l'import")
    print("=" * 80)
    
    # Test 1: Workflow complet
    workflow_success = test_complete_workflow()
    
    # Test 2: Étapes individuelles (si le workflow complet a échoué)
    if not workflow_success:
        test_step_by_step()
    
    # Test 3: Skills individuels
    test_skills_individually()
    
    # Test 4: Statut final
    print("\n🧪 STATUT FINAL")
    print("=" * 60)
    
    try:
        status = get_workflow_status()
        if status.get('success'):
            status_data = status.get('status', {})
            print(f"   📊 Progression: {status_data.get('overall_progress', 0):.1f}%")
            print(f"   ✅ Étapes complétées: {', '.join(status_data.get('completed_steps', []))}")
        else:
            print(f"   ❌ Erreur statut: {status.get('error', 'Inconnue')}")
    except Exception as e:
        print(f"   ❌ Erreur statut: {e}")
    
    print(f"\n🏆 RÉSULTAT FINAL: {'SUCCÈS' if workflow_success else 'ÉCHEC PARTIEL'}")
    print("=" * 80)

if __name__ == "__main__":
    main()
