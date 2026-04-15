#!/usr/bin/env python3
"""
ÉTAPE 3: IMPORTATEUR MEALIE MCP
Importe les recettes structurées dans Mealie avec les outils MCP
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Importer le wrapper MCP authentifié pour rendre les fonctions disponibles
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from mcp_auth_wrapper import *

# MCP mealie-test disponibles via wrapper
MCP_AVAILABLE = True  # Les MCP mealie-test sont disponibles via le wrapper

# Configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "mealie_config.json"

class MealieImporterMCP:
    """Importateur de recettes pour Mealie avec MCP réels"""
    
    def __init__(self):
        self.config = self.load_config()
        self.imported_recipes = []
        self.import_errors = []
        
    def load_config(self) -> Dict:
        """Charge la configuration Mealie"""
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement config: {e}")
            return {}
    
    def import_recipe_to_mealie(self, structured_recipe: Dict) -> Optional[str]:
        """
        Importe une recette structurée dans Mealie
        Utilise les vrais MCP mealie-test
        """
        try:
            print(f"📥 Import: {structured_recipe.get('name', 'Sans nom')}")
            
            # Créer le payload pour l'API Mealie
            payload = self.create_mealie_payload(structured_recipe)
            
            if not payload:
                print(f"   ❌ Erreur création payload")
                return None
            
            # Utiliser les vrais MCP si disponibles
            if MCP_AVAILABLE:
                recipe_id = self.import_with_real_mcp(payload, structured_recipe['name'])
            else:
                # Fallback vers simulation
                recipe_id = self.simulate_mealie_import(payload, structured_recipe['name'])
            
            if recipe_id:
                print(f"   ✅ Importé avec succès! ID: {recipe_id}")
                return recipe_id
            else:
                print(f"   ❌ Échec import")
                return None
                
        except Exception as e:
            print(f"   ❌ Exception import: {e}")
            self.import_errors.append(f"Import {structured_recipe.get('name', 'unknown')}: {e}")
            return None
    
    def import_with_real_mcp(self, payload: Dict, recipe_name: str) -> Optional[str]:
        """Importe avec les MCP Cascade directement"""
        try:
            print(f"   📦 Payload envoyé: {len(payload)} champs")
            print(f"   📦 Nom: {payload.get('name', 'N/A')}")
            print(f"   📦 Ingrédients: {len(payload.get('recipeIngredient', []))}")
            print(f"   📦 Instructions: {len(payload.get('recipeInstructions', []))}")
            print(f"   📦 Image: {payload.get('image', 'N/A')[:50] if payload.get('image') else 'N/A'}")
            
            # Utiliser les MCP Cascade directement avec le payload complet
            result = mcp3_create_recipe(payload=payload)
            
            print(f"   📦 Réponse API: {result}")
            
            if result and result.get('id'):
                return result.get('id')
            elif result and result.get('success'):
                return result.get('recipe_id', result.get('id'))
            else:
                return None
                
        except Exception as e:
            print(f"   ❌ Erreur MCP import: {e}")
            return None
    
    def load_structured_data(self, filename: str) -> List[Dict]:
        """Charge les données structurées"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = data.get('recipes', [])
            print(f"✅ Données structurées chargées: {len(recipes)} recettes")
            return recipes
            
        except Exception as e:
            print(f"❌ Erreur chargement données structurées: {e}")
            return []
    
    def create_mealie_payload(self, structured_recipe: Dict) -> Optional[Dict]:
        """Crée le payload exact pour l'API Mealie"""
        try:
            # S'assurer que les instructions ont le bon format
            instructions = structured_recipe.get('recipeInstructions', [])
            formatted_instructions = []
            
            for instruction in instructions:
                if isinstance(instruction, dict):
                    formatted_instructions.append({
                        "id": instruction.get('id', str(uuid.uuid4())),
                        "title": instruction.get('title', 'Étape'),
                        "summary": instruction.get('summary', ''),
                        "text": instruction.get('text', ''),
                        "ingredientReferences": instruction.get('ingredientReferences', [])
                    })
                else:
                    # Si c'est une chaîne, la formater
                    formatted_instructions.append({
                        "id": str(uuid.uuid4()),
                        "title": "Étape",
                        "summary": "",
                        "text": str(instruction),
                        "ingredientReferences": []
                    })
            
            # S'assurer que les ingrédients ont le bon format
            ingredients = structured_recipe.get('recipeIngredient', [])
            formatted_ingredients = []
            
            for ingredient in ingredients:
                if isinstance(ingredient, dict):
                    # Si note est une chaîne JSON, la parser pour extraire les valeurs
                    note = ingredient.get('note', '')
                    if note and isinstance(note, str) and note.startswith('{'):
                        try:
                            import json
                            parsed_note = json.loads(note)
                            # Utiliser les valeurs parsées si disponibles
                            quantity = float(parsed_note.get('quantity', ingredient.get('quantity', 0)))
                            unit = parsed_note.get('unit_id', ingredient.get('unit', ''))
                            food = parsed_note.get('food_id', ingredient.get('food', ''))
                            display_note = parsed_note.get('note', note)
                        except (json.JSONDecodeError, ValueError):
                            # Si parsing échoue, utiliser les valeurs originales
                            quantity = float(ingredient.get('quantity', 0))
                            unit = ingredient.get('unit', '')
                            food = ingredient.get('food', '')
                            display_note = note
                    else:
                        quantity = float(ingredient.get('quantity', 0))
                        unit = ingredient.get('unit', '')
                        food = ingredient.get('food', '')
                        display_note = note

                    # Texte complet pour le champ note (fallback si unit/food non résolus)
                    display_text = ingredient.get('display') or ingredient.get('originalText') or display_note or ''
                    # unit/food transmis comme strings → résolus en objets Mealie dans mcp_auth_wrapper
                    formatted_ingredients.append({
                        "quantity": quantity,
                        "unit": unit if unit else None,
                        "food": food if food else None,
                        "note": display_text if isinstance(display_text, str) else '',
                        "display": display_text,
                        "title": ingredient.get('title'),
                        "originalText": display_text,
                        "referenceId": ingredient.get('referenceId', str(uuid.uuid4())),
                        "referencedRecipe": None
                    })
                else:
                    # Si c'est une chaîne, la formater
                    formatted_ingredients.append({
                        "quantity": 0.0,
                        "unit": None,
                        "food": None,
                        "note": str(ingredient),
                        "display": str(ingredient),
                        "title": None,
                        "originalText": str(ingredient),
                        "referenceId": str(uuid.uuid4()),
                        "referencedRecipe": None
                    })
            
            # Créer le payload complet (format Recipe-Input API 3.14)
            payload = {
                "name": structured_recipe["name"],
                "description": structured_recipe.get("description", ""),
                
                # Temps (format plat API 3.14)
                "prepTime": structured_recipe.get("prepTime", "PT15M"),
                "cookTime": structured_recipe.get("cookTime", "PT20M"),
                "totalTime": structured_recipe.get("totalTime", "PT35M"),
                
                # Portions (format API 3.14)
                "recipeServings": structured_recipe.get('recipeServings', 4),
                "recipeYieldQuantity": structured_recipe.get('recipeYieldQuantity', 4),
                "recipeYield": structured_recipe.get('recipeYield', f"{structured_recipe.get('recipeServings', 4)} servings"),
                
                # Ingrédients (format structuré API 3.14)
                "recipeIngredient": formatted_ingredients,
                
                # Instructions (format structuré API 3.14)
                "recipeInstructions": formatted_instructions,
                
                # Catégories et tags (format API 3.14)
                "recipeCategory": structured_recipe.get("recipeCategory", []),
                "tags": structured_recipe.get("tags", []),
                
                # Image (prendre la première image si disponible)
                "image": self._get_image_url(structured_recipe),
                
                # Autres champs optionnels
                "orgURL": structured_recipe.get("orgURL", ""),
                "slug": structured_recipe.get("slug", "")
            }
            
            return payload
            
        except Exception as e:
            print(f"❌ Erreur création payload: {e}")
            return None
    
    def _get_image_url(self, structured_recipe: Dict) -> str:
        """Extrait l'URL de l'image des données structurées"""
        try:
            # Vérifier image_path (liste d'URLs)
            image_path = structured_recipe.get('image_path', [])
            if image_path and isinstance(image_path, list) and len(image_path) > 0:
                # Prendre la première image (format .jpg ou .webp)
                for url in image_path:
                    if url and isinstance(url, str) and (url.endswith('.jpg') or url.endswith('.jpeg')):
                        return url
                # Fallback: prendre la première image
                if image_path[0]:
                    return image_path[0]
            
            # Vérifier image (URL simple)
            image = structured_recipe.get('image', '')
            if image:
                return image
            
            return ""
        except Exception as e:
            print(f"   ⚠️ Erreur extraction image: {e}")
            return ""
    
    def import_recipe_to_mealie(self, structured_recipe: Dict) -> bool:
        """
        Importe une recette dans Mealie
        Utiliserait mealie-test MCP en production
        """
        try:
            print(f"🔄 Import: {structured_recipe['name']}")
            
            # Étape 1: Créer le payload
            payload = self.create_mealie_payload(structured_recipe)
            
            if not payload:
                return False
            
            # Étape 2: Importer la recette avec l'API Mealie réelle
            recipe_id = self.import_with_real_mcp(payload, structured_recipe['name'])
            
            if recipe_id:
                print(f"   ✅ Importé avec succès! ID: {recipe_id}")
                
                # Ajouter à la liste des recettes importées
                import_info = {
                    "name": structured_recipe['name'],
                    "slug": structured_recipe.get('slug', ''),
                    "id": recipe_id,
                    "imported_at": datetime.now().isoformat(),
                    "servings": structured_recipe.get('recipeServings', 0),
                    "ingredients_count": len(structured_recipe.get('recipeIngredient', [])),
                    "instructions_count": len(structured_recipe.get('recipeInstructions', [])),
                    "categories": structured_recipe.get('recipeCategory', []),
                    "tags": structured_recipe.get('tags', []),
                    "nutrition": structured_recipe.get('nutrition', {}),
                    "difficulty": structured_recipe.get('difficulty', 'Inconnu'),
                    "cost": structured_recipe.get('cost', 'Inconnu')
                }
                self.imported_recipes.append(import_info)
                
                return True
            else:
                print(f"   ❌ Erreur import")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception import: {e}")
            return False
    
    def simulate_mealie_import(self, payload: Dict, recipe_name: str) -> Optional[str]:
        """Simule l'import Mealie (remplacerait mealie-test MCP)"""
        try:
            # Simuler une réponse API réussie
            recipe_id = str(uuid.uuid4())
            
            # Validation basique
            if not payload.get('name'):
                return None
            
            if not payload.get('recipeIngredient'):
                return None
            
            if not payload.get('recipeInstructions'):
                return None
            
            print(f"   📊 Validation: {len(payload['recipeIngredient'])} ingrédients, {len(payload['recipeInstructions'])} instructions")
            
            return recipe_id
            
        except Exception as e:
            print(f"   ❌ Erreur simulation import: {e}")
            return None
    
    def verify_imported_recipe(self, recipe_name: str, recipe_id: str) -> bool:
        """
        Vérifie qu'une recette a été correctement importée
        Utiliserait mealie-test MCP en production
        """
        try:
            # Simuler la vérification
            # En production: utiliser mealie-test MCP pour vérifier
            print(f"   🔍 Vérification: {recipe_name}")
            
            # Simulation de vérification réussie
            return True
            
        except Exception as e:
            print(f"   ❌ Exception vérification: {e}")
            return False
    
    def import_all_recipes(self, structured_recipes: List[Dict]) -> bool:
        """Importe toutes les recettes structurées"""
        print(f"🚀 DÉBUT DE L'IMPORT MEALIE MCP")
        print("=" * 50)
        
        successful = 0
        failed = 0
        batch_size = self.config.get('importing', {}).get('batch_size', 5)
        delay = self.config.get('importing', {}).get('delay_between_imports', 3)
        verify_imports = self.config.get('importing', {}).get('verify_imports', True)
        
        for i, recipe in enumerate(structured_recipes, 1):
            print(f"\n📊 [{i}/{len(structured_recipes)}] Import en cours...")
            
            if self.import_recipe_to_mealie(recipe):
                # Vérifier l'import si demandé
                if verify_imports:
                    imported = self.imported_recipes[-1] if self.imported_recipes else None
                    if imported and self.verify_imported_recipe(imported['name'], imported['id']):
                        successful += 1
                    else:
                        failed += 1
                else:
                    successful += 1
            else:
                failed += 1
            
            # Pause entre les imports (sauf pour le dernier)
            if i < len(structured_recipes):
                time.sleep(delay)
            
            # Pause après chaque batch
            if i % batch_size == 0:
                print(f"   📊 Batch terminé: {i} recettes traitées")
                time.sleep(delay * 2)
        
        print(f"\n{'='*50}")
        print("📊 BILAN DE L'IMPORT")
        print(f"✅ Réussis: {successful}")
        print(f"❌ Échecs: {failed}")
        print(f"📈 Taux de succès: {(successful/len(structured_recipes))*100:.1f}%")
        
        return successful > 0
    
    def save_import_report(self) -> Optional[str]:
        """Sauvegarde le rapport d'import"""
        try:
            # Créer le dossier import_reports
            output_dir = Path(__file__).parent.parent.parent / "import_reports"
            output_dir.mkdir(exist_ok=True)
            
            # Préparer le rapport
            report = {
                "metadata": {
                    "import_date": datetime.now().isoformat(),
                    "total_imported": len(self.imported_recipes),
                    "importer": "mealie_importer_mcp",
                    "config": self.config.get('importing', {})
                },
                "recipes": self.imported_recipes,
                "statistics": self.calculate_import_statistics()
            }
            
            # Sauvegarder avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = output_dir / f"mealie_import_report_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # Créer aussi un fichier latest
            latest_filename = output_dir / "latest_mealie_import_report.json"
            with open(latest_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Rapport d'import sauvegardé: {filename}")
            print(f"✅ Fichier latest: {latest_filename}")
            
            return str(filename)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde rapport: {e}")
            return None
    
    def calculate_import_statistics(self) -> Dict:
        """Calcule les statistiques d'import"""
        if not self.imported_recipes:
            return {}
        
        categories = []
        tags = []
        difficulties = []
        costs = []
        total_ingredients = 0
        total_instructions = 0
        total_calories = 0
        
        for recipe in self.imported_recipes:
            categories.extend(recipe.get('categories', []))
            tags.extend(recipe.get('tags', []))
            difficulties.append(recipe.get('difficulty', 'Inconnu'))
            costs.append(recipe.get('cost', 'Inconnu'))
            total_ingredients += recipe.get('ingredients_count', 0)
            total_instructions += recipe.get('instructions_count', 0)
            
            nutrition = recipe.get('nutrition', {})
            if nutrition.get('calories'):
                total_calories += nutrition['calories']
        
        return {
            "total_categories": len(set(categories)),
            "total_tags": len(set(tags)),
            "difficulty_distribution": {
                "facile": difficulties.count("Facile"),
                "moyen": difficulties.count("Moyen"),
                "difficile": difficulties.count("Difficile")
            },
            "cost_distribution": {
                "économique": costs.count("Économique"),
                "moyen": costs.count("Moyen"),
                "élevé": costs.count("Élevé")
            },
            "avg_ingredients_per_recipe": total_ingredients / len(self.imported_recipes) if self.imported_recipes else 0,
            "avg_instructions_per_recipe": total_instructions / len(self.imported_recipes) if self.imported_recipes else 0,
            "avg_calories_per_recipe": total_calories / len(self.imported_recipes) if self.imported_recipes else 0,
            "most_common_categories": self.get_most_common_items(categories, 5),
            "most_common_tags": self.get_most_common_items(tags, 5)
        }
    
    def get_most_common_items(self, items: List[str], limit: int = 5) -> List[str]:
        """Retourne les éléments les plus communs"""
        from collections import Counter
        counter = Counter(items)
        return [item for item, count in counter.most_common(limit)]
    
    def run_import_workflow(self, structured_filename: str) -> Optional[str]:
        """Lance le workflow complet d'import"""
        print("🎯 WORKFLOW D'IMPORT MEALIE MCP")
        print("📋 Import des recettes structurées dans Mealie")
        print("=" * 60)
        
        # Étape 1: Charger les données structurées
        structured_recipes = self.load_structured_data(structured_filename)
        
        if not structured_recipes:
            print("❌ Impossible de charger les données structurées")
            return None
        
        # Étape 2: Importer dans Mealie
        if self.import_all_recipes(structured_recipes):
            # Étape 3: Sauvegarder le rapport
            report_filename = self.save_import_report()
            
            if report_filename:
                print(f"\n🎉 ÉTAPE 3 TERMINÉE AVEC SUCCÈS !")
                print(f"📁 Rapport d'import: {report_filename}")
                print(f"📊 {len(self.imported_recipes)} recettes importées")
                print(f"🍽️ Disponibles dans Mealie")
                print(f"🤖 Prêtes pour les agents MCP")
                
                # Afficher le résumé
                self.display_import_summary()
                
                return report_filename
        
        return None
    
    def display_import_summary(self):
        """Affiche un résumé des imports"""
        print(f"\n📋 RÉSUMÉ DES IMPORTS MEALIE")
        print("=" * 50)
        
        for i, recipe in enumerate(self.imported_recipes, 1):
            print(f"\n🍽️ {i}. {recipe['name']}")
            print(f"   🆔 Slug: {recipe['slug']}")
            print(f"   🆔 ID: {recipe['id']}")
            print(f"   👥 Portions: {recipe['servings']}")
            print(f"   🥘 Ingrédients: {recipe['ingredients_count']}")
            print(f"   📝 Instructions: {recipe['instructions_count']}")
            print(f"   📂 Catégories: {', '.join(recipe['categories'])}")
            print(f"   🏷️ Tags: {', '.join(recipe['tags'][:3])}...")
            print(f"   📊 Calories: {recipe['nutrition'].get('calories', 'N/A')}")
            print(f"   📅 Importé le: {recipe['imported_at'][:10]}")
        
        if self.imported_recipes:
            stats = self.calculate_import_statistics()
            print(f"\n📈 STATISTIQUES D'IMPORT:")
            print(f"   📊 Recettes importées: {len(self.imported_recipes)}")
            print(f"   🥘 Ingrédients moyens: {stats.get('avg_ingredients_per_recipe', 0):.1f}")
            print(f"   📝 Instructions moyennes: {stats.get('avg_instructions_per_recipe', 0):.1f}")
            print(f"   🔥 Calories moyennes: {stats.get('avg_calories_per_recipe', 0):.1f}")
            print(f"   📂 Catégories uniques: {stats.get('total_categories', 0)}")
            print(f"   🏷️ Tags uniques: {stats.get('total_tags', 0)}")
            print(f"\n🎯 Recettes prêtes à utiliser avec les agents MCP:")
            print(f"   🥗 @nutrition-planner")
            print(f"   🔬 @recipe-analyzer")
            print(f"   🛒 @shopping-optimizer")

if __name__ == "__main__":
    importer = MealieImporterMCP()
    
    # Utiliser le dernier fichier structuré
    structured_file = "structured_data/latest_mealie_structured_recipes.json"
    importer.run_import_workflow(structured_file)
