#!/usr/bin/env python3
"""
TEST SUITE QUALITY WORKFLOW MEALIE
Suite de tests automatisés pour la qualité du workflow
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
import sys

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

from quality_checker import WorkflowQualityChecker

class TestWorkflowQuality(unittest.TestCase):
    """Suite de tests pour la qualité du workflow Mealie"""
    
    def setUp(self):
        """Configuration des tests"""
        self.checker = WorkflowQualityChecker()
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Créer des fichiers de test
        self.create_test_files()
    
    def create_test_files(self):
        """Crée les fichiers de test"""
        
        # Fichier scraped test
        scraped_test = {
            "metadata": {
                "version": "1.0",
                "scraped_at": "2026-04-02T12:00:00",
                "total_recipes": 2,
                "sources": ["test_source"],
                "scraper": "test"
            },
            "recipes": [
                {
                    "name": "Test Recipe 1",
                    "description": "Test description",
                    "ingredients": ["200g flour", "2 eggs", "100ml milk"],
                    "instructions": ["Mix ingredients", "Cook for 20 min", "Serve hot"],
                    "prep_time": "10",
                    "cook_time": "20",
                    "total_time": "30",
                    "servings": "4",
                    "image": "test_image1.jpg",
                    "source_url": "https://test.com/recipe1"
                },
                {
                    "name": "Test Recipe 2",
                    "description": "Another test",
                    "ingredients": ["1kg meat", "2 onions", "3 carrots"],
                    "instructions": ["Prepare meat", "Add vegetables", "Cook 1 hour"],
                    "prep_time": "15",
                    "cook_time": "60",
                    "total_time": "75",
                    "servings": "6",
                    "image": "test_image2.jpg",
                    "source_url": "https://test.com/recipe2"
                }
            ],
            "statistics": {
                "total_instructions": 6,
                "total_ingredients": 6,
                "avg_instructions_per_recipe": 3.0,
                "avg_ingredients_per_recipe": 3.0
            }
        }
        
        with open(self.test_data_dir / "test_scraped.json", 'w', encoding='utf-8') as f:
            json.dump(scraped_test, f, ensure_ascii=False, indent=2)
        
        # Fichier structuré test
        structured_test = {
            "metadata": {
                "version": "1.0",
                "created_at": "2026-04-02T12:00:00",
                "total_recipes": 2,
                "format": "mealie_compatible",
                "language": "fr",
                "cuisine": "Française"
            },
            "recipes": [
                {
                    "name": "Test Recipe 1",
                    "slug": "test-recipe-1",
                    "description": "Test description",
                    "prepTime": "PT10M",
                    "cookTime": "PT20M",
                    "totalTime": "PT30M",
                    "recipeServings": 4.0,
                    "recipeYieldQuantity": 4.0,
                    "recipeYield": "4 servings",
                    "recipeIngredient": [
                        {
                            "quantity": 200.0,
                            "unit": "g",
                            "food": "flour",
                            "note": "",
                            "display": "200g flour",
                            "title": None,
                            "originalText": "200g flour",
                            "referenceId": "test-uuid-1",
                            "referencedRecipe": None
                        },
                        {
                            "quantity": 2.0,
                            "unit": "",
                            "food": "eggs",
                            "note": "",
                            "display": "2 eggs",
                            "title": None,
                            "originalText": "2 eggs",
                            "referenceId": "test-uuid-2",
                            "referencedRecipe": None
                        }
                    ],
                    "recipeInstructions": [
                        {
                            "id": "instruction-uuid-1",
                            "title": "Étape 1",
                            "summary": "",
                            "text": "Mix ingredients",
                            "ingredientReferences": []
                        },
                        {
                            "id": "instruction-uuid-2",
                            "title": "Étape 2",
                            "summary": "",
                            "text": "Cook for 20 min",
                            "ingredientReferences": []
                        }
                    ],
                    "recipeCategory": ["Plat Principal"],
                    "tags": ["test", "recipe"],
                    "nutrition": {
                        "calories": 300,
                        "proteinContent": "15g",
                        "carbohydrateContent": "30g",
                        "fatContent": "10g"
                    }
                }
            ]
        }
        
        with open(self.test_data_dir / "test_structured.json", 'w', encoding='utf-8') as f:
            json.dump(structured_test, f, ensure_ascii=False, indent=2)
        
        # Fichier import test
        import_test = {
            "metadata": {
                "import_date": "2026-04-02T12:00:00",
                "total_imported": 1,
                "importer": "test_importer"
            },
            "recipes": [
                {
                    "name": "Test Recipe 1",
                    "slug": "test-recipe-1",
                    "id": "import-uuid-1",
                    "imported_at": "2026-04-02T12:00:00",
                    "servings": 4.0,
                    "ingredients_count": 2,
                    "instructions_count": 2,
                    "categories": ["Plat Principal"],
                    "tags": ["test", "recipe"]
                }
            ],
            "statistics": {
                "total_categories": 1,
                "total_tags": 2
            }
        }
        
        with open(self.test_data_dir / "test_import.json", 'w', encoding='utf-8') as f:
            json.dump(import_test, f, ensure_ascii=False, indent=2)
    
    def test_no_duplicates(self):
        """Test qu'il n'y a pas de doublons"""
        result = self.checker.check_duplicates(str(self.test_data_dir / "test_scraped.json"))
        
        self.assertEqual(result["total_recipes"], 2)
        self.assertEqual(result["unique_content"], 2)
        self.assertEqual(len(result["duplicate_groups"]), 0)
        self.assertEqual(result["score"], 100.0)
    
    def test_time_consistency(self):
        """Test la cohérence des temps"""
        result = self.checker.check_time_consistency(str(self.test_data_dir / "test_scraped.json"))
        
        self.assertEqual(result["total_recipes"], 2)
        self.assertEqual(result["consistent_times"], 2)
        self.assertEqual(len(result["inconsistent_times"]), 0)
        self.assertEqual(result["score"], 100.0)
    
    def test_ingredient_parsing(self):
        """Test le parsing des ingrédients"""
        result = self.checker.check_ingredient_quality(str(self.test_data_dir / "test_structured.json"))
        
        self.assertEqual(result["total_recipes"], 1)
        self.assertEqual(result["specific_ingredients"], 2)
        self.assertEqual(result["generic_ingredients"], 0)
        self.assertGreater(result["score"], 80.0)
    
    def test_instruction_quality(self):
        """Test la qualité des instructions"""
        result = self.checker.check_instruction_quality(str(self.test_data_dir / "test_structured.json"))
        
        self.assertEqual(result["total_recipes"], 1)
        self.assertEqual(result["valid_format"], 2)
        self.assertGreater(result["score"], 80.0)
    
    def test_image_availability(self):
        """Test la disponibilité des images"""
        result = self.checker.check_image_quality(str(self.test_data_dir / "test_scraped.json"))
        
        self.assertEqual(result["total_recipes"], 2)
        self.assertEqual(result["recipes_with_images"], 2)
        # Les images locales ont un score de 0
        self.assertEqual(result["score"], 0.0)
    
    def test_structural_quality(self):
        """Test la qualité structurelle"""
        scraped_file = str(self.test_data_dir / "test_scraped.json")
        structured_file = str(self.test_data_dir / "test_structured.json")
        import_file = str(self.test_data_dir / "test_import.json")
        
        result = self.checker.check_structural_quality(scraped_file, structured_file, import_file)
        
        self.assertEqual(result["scraped_data"]["valid_json"], True)
        self.assertEqual(result["structured_data"]["mealie_format"], True)
        self.assertEqual(result["import_data"]["recipe_ids_valid"], True)
        self.assertEqual(result["overall_score"], 100.0)
    
    def test_content_quality(self):
        """Test la qualité du contenu"""
        scraped_file = str(self.test_data_dir / "test_scraped.json")
        structured_file = str(self.test_data_dir / "test_structured.json")
        
        result = self.checker.check_content_quality(scraped_file, structured_file)
        
        self.assertEqual(result["duplicates"]["score"], 100.0)
        self.assertEqual(result["time_consistency"]["score"], 100.0)
        self.assertGreater(result["overall_score"], 70.0)
    
    def test_business_quality(self):
        """Test la qualité métier"""
        structured_file = str(self.test_data_dir / "test_structured.json")
        import_file = str(self.test_data_dir / "test_import.json")
        
        result = self.checker.check_business_quality(structured_file, import_file)
        
        self.assertEqual(result["nutrition_quality"]["score"], 100.0)
        self.assertEqual(result["usability_quality"]["score"], 100.0)
        self.assertEqual(result["overall_score"], 100.0)
    
    def test_duplicate_detection(self):
        """Test la détection de doublons"""
        # Créer un fichier avec doublons
        duplicate_data = {
            "metadata": {"version": "1.0", "total_recipes": 3},
            "recipes": [
                {
                    "name": "Same Recipe",
                    "ingredients": ["flour", "eggs"],
                    "instructions": ["Mix", "Cook"]
                },
                {
                    "name": "Same Recipe",  # Doublon exact
                    "ingredients": ["flour", "eggs"],
                    "instructions": ["Mix", "Cook"]
                },
                {
                    "name": "Different Recipe",
                    "ingredients": ["meat", "vegetables"],
                    "instructions": ["Prepare", "Cook"]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(duplicate_data, f)
            duplicate_file = f.name
        
        try:
            result = self.checker.check_duplicates(duplicate_file)
            
            self.assertEqual(result["total_recipes"], 3)
            self.assertEqual(result["unique_content"], 2)
            self.assertEqual(len(result["duplicate_groups"]), 1)
            self.assertEqual(result["score"], 66.7)  # 2/3 unique
        finally:
            os.unlink(duplicate_file)
    
    def test_time_parsing(self):
        """Test le parsing des temps"""
        # Test de la fonction parse_time_value
        test_cases = [
            ("30", 30),
            ("2 heures", 120),
            ("1h30", 90),
            ("45 minutes", 45),
            ("2h", 120),
            ("invalide", 0),
            ("", 0)
        ]
        
        for time_str, expected in test_cases:
            result = self.checker.parse_time_value(time_str)
            self.assertEqual(result, expected, f"Failed for '{time_str}'")
    
    def test_complete_quality_check(self):
        """Test la vérification complète"""
        scraped_file = str(self.test_data_dir / "test_scraped.json")
        structured_file = str(self.test_data_dir / "test_structured.json")
        import_file = str(self.test_data_dir / "test_import.json")
        
        result = self.checker.run_complete_quality_check(scraped_file, structured_file, import_file)
        
        self.assertIn("global_score", result)
        self.assertIn("status", result)
        self.assertIn("level_scores", result)
        self.assertGreater(result["global_score"], 80.0)
        self.assertEqual(result["status"], "BON")
    
    def tearDown(self):
        """Nettoyage des tests"""
        # Nettoyer les fichiers de test
        import shutil
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)

class TestQualityThresholds(unittest.TestCase):
    """Test des seuils de qualité"""
    
    def setUp(self):
        self.checker = WorkflowQualityChecker()
    
    def test_excellent_threshold(self):
        """Test du seuil EXCELLENT (>=90)"""
        # Simuler un score excellent
        scores = {"structural": 95, "content": 92, "business": 90}
        issues = []
        
        recommendations = self.checker.generate_recommendations(scores, issues)
        self.assertEqual(len(recommendations), 0)  # Pas de recommandations pour excellent
    
    def test_good_threshold(self):
        """Test du seuil BON (75-89)"""
        scores = {"structural": 85, "content": 80, "business": 78}
        issues = []
        
        recommendations = self.checker.generate_recommendations(scores, issues)
        self.assertGreater(len(recommendations), 0)
    
    def test_poor_threshold(self):
        """Test du seuil INSUFFISANT (<60)"""
        scores = {"structural": 50, "content": 45, "business": 55}
        issues = [{"level": "content", "category": "duplicates", "issue": "Beaucoup de doublons"}]
        
        recommendations = self.checker.generate_recommendations(scores, issues)
        self.assertGreater(len(recommendations), 2)

def run_quality_tests():
    """Lance tous les tests de qualité"""
    print("🧪 LANCEMENT DE LA SUITE DE TESTS QUALITÉ")
    print("=" * 60)
    
    # Créer la suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter les tests
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityThresholds))
    
    # Lancer les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Afficher le résumé
    print(f"\n📊 RÉSULTATS DES TESTS:")
    print(f"   ✅ Tests exécutés: {result.testsRun}")
    print(f"   ❌ Échecs: {len(result.failures)}")
    print(f"   🚨 Erreurs: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ ÉCHECS:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n🚨 ERREURS:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\n🎯 TAUX DE SUCCÈS: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 QUALITÉ EXCELLENTE")
    elif success_rate >= 75:
        print("✅ QUALITÉ BONNE")
    else:
        print("⚠️ QUALITÉ À AMÉLIORER")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_quality_tests()
    exit(0 if success else 1)
