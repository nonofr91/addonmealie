#!/usr/bin/env python3
"""
ÉTAPE 2: STRUCTUREUR DE DONNÉES MEALIE
Transforme les données scrapées en format compatible Mealie
"""

import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "mealie_config.json"

class MealieDataStructurer:
    """Structurer de données pour Mealie"""
    
    def __init__(self):
        self.config = self.load_config()
        self.structured_recipes = []
        
    def load_config(self) -> Dict:
        """Charge la configuration Mealie"""
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement config: {e}")
            return {}
    
    def load_scraped_data(self, filename: str) -> List[Dict]:
        """Charge les données scrapées"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = data.get('recipes', [])
            print(f"✅ Données scrapées chargées: {len(recipes)} recettes")
            return recipes
            
        except Exception as e:
            print(f"❌ Erreur chargement données scrapées: {e}")
            return []
    
    def structure_recipe_for_mealie(self, scraped_recipe: Dict) -> Optional[Dict]:
        """Structure une recette scrapée pour le format Mealie"""
        try:
            # Créer le slug
            slug = self.create_slug(scraped_recipe['name'])
            
            # Formater les ingrédients pour Mealie
            formatted_ingredients = self.format_ingredients(scraped_recipe.get('ingredients', []))
            
            # Formater les instructions pour Mealie (avec UUID)
            formatted_instructions = self.format_instructions(scraped_recipe.get('instructions', []))
            
            # Créer la recette Mealie
            mealie_recipe = {
                # Informations de base
                "name": scraped_recipe['name'],
                "slug": slug,
                "description": scraped_recipe.get('description', ''),
                
                # Informations de temps
                "prepTime": f"PT{scraped_recipe.get('prep_time', '15')}M",
                "cookTime": f"PT{scraped_recipe.get('cook_time', '20')}M",
                "totalTime": f"PT{scraped_recipe.get('total_time', '35')}M",
                
                # Portions
                "recipeServings": float(scraped_recipe.get('servings', '4')),
                "recipeYieldQuantity": float(scraped_recipe.get('servings', '4')),
                "recipeYield": f"{scraped_recipe.get('servings', '4')} servings",
                
                # Ingrédients (format Mealie)
                "recipeIngredient": formatted_ingredients,
                
                # Instructions (format Mealie avec UUID)
                "recipeInstructions": formatted_instructions,
                
                # Catégories et tags
                "recipeCategory": self.generate_categories(scraped_recipe),
                "tags": self.generate_tags(scraped_recipe),
                
                # Métadonnées
                "orgURL": scraped_recipe.get('source_url', ''),
                "dateAdded": datetime.now().strftime('%Y-%m-%d'),
                "dateUpdated": datetime.now().isoformat(),
                
                # Informations nutritionnelles
                "nutrition": self.create_nutrition_info(scraped_recipe),
                
                # Paramètres
                "settings": {
                    "public": False,
                    "showNutrition": True,
                    "showAssets": True,
                    "landscapeView": False,
                    "disableComments": False,
                    "locked": False
                },
                
                # Métadonnées supplémentaires
                "language": self.config.get('structuring', {}).get('language', 'fr'),
                "cuisine": self.config.get('structuring', {}).get('cuisine', 'Française'),
                "difficulty": self.estimate_difficulty(scraped_recipe),
                "cost": self.estimate_cost(scraped_recipe),
                "scraped_at": scraped_recipe.get('scraped_at', ''),
                "image_path": scraped_recipe.get('image', '')
            }
            
            return mealie_recipe
            
        except Exception as e:
            print(f"❌ Erreur structuration {scraped_recipe.get('name', 'Inconnue')}: {e}")
            return None
    
    def create_slug(self, name: str) -> str:
        """Crée un slug URL-friendly"""
        # Nettoyer le nom
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[\s_-]+', '-', slug)
        slug = slug.strip('-_')
        
        # Gérer les caractères accentués
        slug = re.sub(r'[àáâãäå]', 'a', slug)
        slug = re.sub(r'[èéêë]', 'e', slug)
        slug = re.sub(r'[ìíîï]', 'i', slug)
        slug = re.sub(r'[òóôõö]', 'o', slug)
        slug = re.sub(r'[ùúûü]', 'u', slug)
        slug = re.sub(r'[ýÿ]', 'y', slug)
        slug = re.sub(r'[ç]', 'c', slug)
        
        return slug[:50] if len(slug) > 50 else slug
    
    def format_ingredients(self, ingredients: List[str]) -> List[Dict]:
        """Formate les ingrédients pour Mealie"""
        formatted = []
        
        for ingredient in ingredients:
            # Parser l'ingrédient
            parsed = self.parse_ingredient(ingredient)
            
            formatted.append({
                "quantity": parsed.get('quantity', 0.0),
                "unit": parsed.get('unit', ''),
                "food": parsed.get('food', ingredient),
                "note": parsed.get('note', ''),
                "display": ingredient,
                "title": None,
                "originalText": ingredient,
                "referenceId": str(uuid.uuid4()),
                "referencedRecipe": None
            })
        
        return formatted
    
    def parse_ingredient(self, ingredient: str) -> Dict:
        """Parse un ingrédient en quantité/unité/aliment"""
        # Patterns pour parser les ingrédients
        patterns = [
            r'^(\d+(?:,\d+)?)\s*([a-zA-Z°]+)?\s+(.+)$',  # "200g farine"
            r'^(\d+(?:,\d+)?)\s*([a-zA-Z°]+)\s+de\s+(.+)$',  # "200g de farine"
            r'^(\d+)\s+(.+)$',  # "3 œufs"
            r'^(.+)$'  # Juste le nom
        ]
        
        for pattern in patterns:
            match = re.match(pattern, ingredient.strip())
            if match:
                groups = match.groups()
                
                if len(groups) == 3:
                    quantity, unit, food = groups
                    return {
                        'quantity': float(quantity.replace(',', '.')),
                        'unit': unit.lower(),
                        'food': food.strip(),
                        'note': ''
                    }
                elif len(groups) == 2:
                    quantity, food = groups
                    return {
                        'quantity': float(quantity),
                        'unit': '',
                        'food': food.strip(),
                        'note': ''
                    }
                elif len(groups) == 1:
                    return {
                        'quantity': 0.0,
                        'unit': '',
                        'food': groups[0].strip(),
                        'note': ''
                    }
        
        return {
            'quantity': 0.0,
            'unit': '',
            'food': ingredient,
            'note': ''
        }
    
    def format_instructions(self, instructions: List[str]) -> List[Dict]:
        """Formate les instructions pour Mealie (avec UUID)"""
        formatted = []
        
        max_instructions = self.config.get('structuring', {}).get('max_instructions', 15)
        
        for i, instruction in enumerate(instructions[:max_instructions], 1):
            formatted.append({
                "id": str(uuid.uuid4()),
                "title": f"Étape {i}",
                "summary": "",
                "text": instruction.strip(),
                "ingredientReferences": []
            })
        
        return formatted
    
    def generate_categories(self, recipe: Dict) -> List[str]:
        """Génère les catégories automatiquement"""
        categories = []
        
        name = recipe.get('name', '').lower()
        ingredients = [ing.lower() for ing in recipe.get('ingredients', [])]
        
        # Catégories basées sur le type de plat
        if any(keyword in name for keyword in ['tarte', 'gâteau', 'dessert', 'crème', 'glace', 'mousse']):
            categories.append('Dessert')
        elif any(keyword in name for keyword in ['soupe', 'potage', 'velouté']):
            categories.append('Soupe')
        elif any(keyword in name for keyword in ['salade']):
            categories.append('Salade')
        elif any(keyword in name for keyword in ['quiche', 'pizza', 'gratin', 'hachis']):
            categories.append('Plat Principal')
        elif any(keyword in name for keyword in ['ratatouille', 'légumes', 'purée']):
            categories.append('Accompagnement')
        elif any(keyword in name for keyword in ['boeuf', 'poulet', 'viande', 'poisson']):
            categories.append('Plat Principal')
        else:
            categories.append('Plat Principal')
        
        # Catégories basées sur les ingrédients
        if any('poisson' in ing or 'saumon' in ing or 'thon' in ing for ing in ingredients):
            categories.append('Poissons')
        elif any('viande' in ing or 'poulet' in ing or 'veau' in ing or 'boeuf' in ing for ing in ingredients):
            categories.append('Viandes')
        elif any('légumes' in ing or 'courgette' in ing or 'tomate' in ing or 'aubergine' in ing for ing in ingredients):
            categories.append('Légumes')
        
        return list(set(categories))  # Éliminer les doublons
    
    def generate_tags(self, recipe: Dict) -> List[str]:
        """Génère les tags automatiquement"""
        tags = []
        
        name = recipe.get('name', '').lower()
        ingredients = [ing.lower() for ing in recipe.get('ingredients', [])]
        instructions = [inst.lower() for inst in recipe.get('instructions', [])]
        
        # Tags basés sur les ingrédients principaux
        main_ingredients = ['pomme', 'saumon', 'lardon', 'oignon', 'courgette', 'aubergine', 'tomate', 'carotte', 'beurre', 'crème']
        for ingredient in main_ingredients:
            if any(ingredient in ing for ing in ingredients):
                tags.append(ingredient)
        
        # Tags basés sur la méthode de cuisson
        cooking_methods = ['four', 'poêle', 'cuisson', 'griller', 'rôtir', 'mijoter']
        for method in cooking_methods:
            if any(method in inst for inst in instructions):
                tags.append(method)
        
        # Tags basés sur les caractéristiques
        if any('rapide' in name or 'facile' in name for name in [name]):
            tags.append('rapide')
        
        if any('traditionnel' in name or 'classique' in name for name in [name]):
            tags.append('traditionnel')
        
        # Tags par défaut
        if not tags:
            tags = ['fait_maison', 'recette']
        
        return list(set(tags))  # Éliminer les doublons
    
    def create_nutrition_info(self, recipe: Dict) -> Dict:
        """Crée les informations nutritionnelles"""
        ingredients = [ing.lower() for ing in recipe.get('ingredients', [])]
        servings = int(recipe.get('servings', '4'))
        
        # Estimation simple des calories
        total_calories = 0
        
        for ingredient in ingredients:
            if 'beurre' in ingredient:
                total_calories += 800
            elif 'sucre' in ingredient:
                total_calories += 400
            elif 'farine' in ingredient:
                total_calories += 350
            elif 'crème' in ingredient:
                total_calories += 300
            elif 'fromage' in ingredient:
                total_calories += 400
            elif 'viande' in ingredient or 'poulet' in ingredient or 'boeuf' in ingredient:
                total_calories += 250
            elif 'saumon' in ingredient:
                total_calories += 200
            elif 'pomme' in ingredient:
                total_calories += 100
            else:
                total_calories += 50
        
        calories_per_serving = round(total_calories / servings)
        
        # Estimation des macronutriments
        protein_count = sum(1 for ing in ingredients 
                           for protein in ['viande', 'poulet', 'saumon', 'thon', 'œuf', 'fromage', 'boeuf'] 
                           if protein in ing)
        
        carb_count = sum(1 for ing in ingredients 
                        for carb in ['farine', 'pomme', 'sucre', 'pommes de terre'] 
                        if carb in ing)
        
        fat_count = sum(1 for ing in ingredients 
                      for fat in ['beurre', 'crème', 'huile', 'fromage'] 
                      if fat in ing)
        
        return {
            "calories": calories_per_serving,
            "carbohydrateContent": f"{carb_count * 15}g",
            "cholesterolContent": None,
            "fatContent": f"{fat_count * 8}g",
            "fiberContent": None,
            "proteinContent": f"{protein_count * 10}g",
            "saturatedFatContent": f"{fat_count * 5}g",
            "sodiumContent": None,
            "sugarContent": f"{carb_count * 8}g",
            "transFatContent": None,
            "unsaturatedFatContent": None
        }
    
    def estimate_difficulty(self, recipe: Dict) -> str:
        """Estime la difficulté de la recette"""
        instructions = recipe.get('instructions', [])
        ingredients = recipe.get('ingredients', [])
        
        if len(instructions) <= 5 and len(ingredients) <= 6:
            return "Facile"
        elif len(instructions) <= 10 and len(ingredients) <= 10:
            return "Moyen"
        else:
            return "Difficile"
    
    def estimate_cost(self, recipe: Dict) -> str:
        """Estime le coût de la recette"""
        ingredients = [ing.lower() for ing in recipe.get('ingredients', [])]
        
        # Compter les ingrédients coûteux
        expensive_count = sum(1 for ing in ingredients 
                            for expensive in ['saumon', 'viande', 'fromage', 'noix', 'boeuf'] 
                            if expensive in ing)
        
        if expensive_count >= 2:
            return "Élevé"
        elif expensive_count >= 1:
            return "Moyen"
        else:
            return "Économique"
    
    def structure_all_recipes(self, scraped_data: List[Dict]) -> bool:
        """Structure toutes les recettes scrapées"""
        print(f"🔧 DÉBUT DE LA STRUCTURATION MEALIE")
        print("=" * 50)
        
        structured = []
        successful = 0
        failed = 0
        
        for i, scraped_recipe in enumerate(scraped_data, 1):
            print(f"\n📊 [{i}/{len(scraped_data)}] Structuration: {scraped_recipe.get('name', 'Sans nom')}")
            
            mealie_recipe = self.structure_recipe_for_mealie(scraped_recipe)
            
            if mealie_recipe:
                structured.append(mealie_recipe)
                successful += 1
                print(f"   ✅ Structuré avec succès")
                print(f"   🆔 Slug: {mealie_recipe['slug']}")
                print(f"   📊 Calories: {mealie_recipe['nutrition']['calories']} par portion")
            else:
                failed += 1
                print(f"   ❌ Échec de la structuration")
        
        self.structured_recipes = structured
        
        print(f"\n{'='*50}")
        print("📊 BILAN DE LA STRUCTURATION")
        print(f"✅ Réussis: {successful}")
        print(f"❌ Échecs: {failed}")
        print(f"📈 Taux de succès: {(successful/len(scraped_data))*100:.1f}%")
        
        return successful > 0
    
    def save_structured_data(self) -> Optional[str]:
        """Sauvegarde les données structurées"""
        try:
            # Créer le dossier structured_data
            output_dir = Path(__file__).parent.parent.parent / "structured_data"
            output_dir.mkdir(exist_ok=True)
            
            # Préparer les données complètes
            structured_database = {
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "total_recipes": len(self.structured_recipes),
                    "format": "mealie_compatible",
                    "language": self.config.get('structuring', {}).get('language', 'fr'),
                    "cuisine": self.config.get('structuring', {}).get('cuisine', 'Française'),
                    "structurer": "mealie_data_structurer"
                },
                "recipes": self.structured_recipes,
                "statistics": self.calculate_structuring_statistics()
            }
            
            # Sauvegarder avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = output_dir / f"mealie_structured_recipes_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(structured_database, f, ensure_ascii=False, indent=2)
            
            # Créer aussi un fichier latest
            latest_filename = output_dir / "latest_mealie_structured_recipes.json"
            with open(latest_filename, 'w', encoding='utf-8') as f:
                json.dump(structured_database, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Données structurées sauvegardées: {filename}")
            print(f"✅ Fichier latest: {latest_filename}")
            
            return str(filename)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde structurée: {e}")
            return None
    
    def calculate_structuring_statistics(self) -> Dict:
        """Calcule les statistiques des recettes structurées"""
        if not self.structured_recipes:
            return {}
        
        categories = []
        tags = []
        difficulties = []
        costs = []
        calories = []
        
        for recipe in self.structured_recipes:
            categories.extend(recipe.get('recipeCategory', []))
            tags.extend(recipe.get('tags', []))
            difficulties.append(recipe.get('difficulty', 'Inconnu'))
            costs.append(recipe.get('cost', 'Inconnu'))
            
            nutrition = recipe.get('nutrition', {})
            if nutrition.get('calories'):
                calories.append(nutrition['calories'])
        
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
            "average_calories": sum(calories) / len(calories) if calories else 0,
            "most_common_categories": self.get_most_common_items(categories, 5),
            "most_common_tags": self.get_most_common_items(tags, 5)
        }
    
    def get_most_common_items(self, items: List[str], limit: int = 5) -> List[str]:
        """Retourne les éléments les plus communs"""
        from collections import Counter
        counter = Counter(items)
        return [item for item, count in counter.most_common(limit)]
    
    def run_structuring_workflow(self, scraped_filename: str) -> Optional[str]:
        """Lance le workflow complet de structuration"""
        print("🎯 WORKFLOW DE STRUCTURATION MEALIE")
        print("📋 Transformation des données scrapées en format Mealie")
        print("=" * 60)
        
        # Étape 1: Charger les données scrapées
        scraped_data = self.load_scraped_data(scraped_filename)
        
        if not scraped_data:
            print("❌ Impossible de charger les données scrapées")
            return None
        
        # Étape 2: Structurer les données
        if self.structure_all_recipes(scraped_data):
            # Étape 3: Sauvegarder les données structurées
            filename = self.save_structured_data()
            
            if filename:
                print(f"\n🎉 ÉTAPE 2 TERMINÉE AVEC SUCCÈS !")
                print(f"📁 Fichier structuré: {filename}")
                print(f"📊 {len(self.structured_recipes)} recettes structurées")
                print(f"🔧 Format compatible Mealie")
                print(f"📋 Prêt pour l'étape 3: Import dans Mealie")
                
                # Afficher un aperçu
                self.display_preview()
                
                return filename
        
        return None
    
    def display_preview(self):
        """Affiche un aperçu des recettes structurées"""
        print(f"\n📋 APERÇU DES RECETTES STRUCTURÉES")
        print("=" * 50)
        
        for i, recipe in enumerate(self.structured_recipes[:3], 1):
            print(f"\n🍽️ {i}. {recipe['name']}")
            print(f"   🆔 Slug: {recipe['slug']}")
            print(f"   ⏱️ Temps: {recipe.get('prepTime', 'N/A')} + {recipe.get('cookTime', 'N/A')}")
            print(f"   👥 Portions: {recipe.get('recipeServings', 'N/A')}")
            print(f"   📊 Calories: {recipe.get('nutrition', {}).get('calories', 'N/A')}")
            print(f"   📂 Catégories: {', '.join(recipe.get('recipeCategory', []))}")
            print(f"   🏷️ Tags: {', '.join(recipe.get('tags', [])[:3])}...")
            print(f"   🥘 Ingrédients: {len(recipe.get('recipeIngredient', []))}")
            print(f"   📝 Instructions: {len(recipe.get('recipeInstructions', []))}")

if __name__ == "__main__":
    structurer = MealieDataStructurer()
    
    # Utiliser le dernier fichier scraped
    scraped_file = "scraped_data/latest_scraped_recipes_mcp.json"
    structurer.run_structuring_workflow(scraped_file)
