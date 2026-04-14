#!/usr/bin/env python3
"""
ADVANCED RECIPE CLEANER
Nettoyage avancé et préparation pour expansion des recettes
"""

import json
import re
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from urllib.parse import urlparse

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

class AdvancedRecipeCleaner:
    """Nettoyeur avancé pour recettes Mealie"""
    
    def __init__(self):
        self.cleaning_log = []
        self.image_dir = Path(__file__).parent / "real_images"
        self.image_dir.mkdir(exist_ok=True)
        
    def clean_all_recipes(self, scraped_file: str) -> Dict:
        """Nettoie complètement toutes les recettes"""
        print("🧹 NETTOYAGE AVANCÉ DES RECETTES")
        print("🔧 Préparation pour expansion et production")
        print("=" * 80)
        
        try:
            with open(scraped_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = data.get("recipes", [])
            original_count = len(recipes)
            
            print(f"📊 Recettes à nettoyer: {original_count}")
            
            # Étape 1: Nettoyage des images
            print("\n🖼️ ÉTAPE 1: NETTOYAGE DES IMAGES")
            image_results = self.clean_all_images(recipes)
            
            # Étape 2: Standardisation des unités
            print("\n📏 ÉTAPE 2: STANDARDISATION DES UNITÉS")
            unit_results = self.standardize_all_units(recipes)
            
            # Étape 3: Validation du contenu
            print("\n✅ ÉTAPE 3: VALIDATION CONTENU")
            validation_results = self.validate_all_content(recipes)
            
            # Étape 4: Enrichissement des métadonnées
            print("\n📊 ÉTAPE 4: ENRICHISSEMENT MÉTADONNÉES")
            enrichment_results = self.enrich_all_metadata(recipes)
            
            # Étape 5: Finalisation
            print("\n🎯 ÉTAPE 5: FINALISATION")
            final_results = self.finalize_recipes(recipes, data)
            
            # Sauvegarder les résultats
            cleaned_file = self.save_cleaned_recipes(data, scraped_file)
            
            # Résumé
            print(f"\n🎉 NETTOYAGE TERMINÉ")
            print(f"📊 Recettes traitées: {original_count}")
            print(f"🖼️ Images nettoyées: {image_results['cleaned']}")
            print(f"📏 Unités standardisées: {unit_results['standardized']}")
            print(f"✅ Validations: {validation_results['passed']}/{validation_results['total']}")
            print(f"📊 Enrichissements: {enrichment_results['enriched']}")
            print(f"💾 Fichier sauvegardé: {cleaned_file}")
            
            return {
                "success": True,
                "original_count": original_count,
                "cleaned_file": cleaned_file,
                "results": {
                    "images": image_results,
                    "units": unit_results,
                    "validation": validation_results,
                    "enrichment": enrichment_results,
                    "final": final_results
                }
            }
            
        except Exception as e:
            print(f"❌ Erreur nettoyage: {e}")
            return {"success": False, "error": str(e)}
    
    def clean_all_images(self, recipes: List[Dict]) -> Dict:
        """Nettoie et remplace toutes les images"""
        cleaned_count = 0
        errors = 0
        
        for recipe in recipes:
            try:
                old_image = recipe.get("image", "")
                recipe_name = recipe.get("name", "").lower()
                
                # Générer une image réaliste basée sur le nom
                new_image = self.generate_realistic_image(recipe_name, old_image)
                
                if new_image and new_image != old_image:
                    recipe["image"] = new_image
                    recipe["image_source"] = "generated"
                    cleaned_count += 1
                    print(f"   ✅ {recipe.get('name')}: {old_image} → {new_image}")
                else:
                    recipe["image_source"] = "local"
                    
            except Exception as e:
                errors += 1
                print(f"   ❌ Erreur image {recipe.get('name')}: {e}")
        
        self.cleaning_log.append(f"Images nettoyées: {cleaned_count}")
        
        return {
            "cleaned": cleaned_count,
            "errors": errors,
            "total": len(recipes)
        }
    
    def generate_realistic_image(self, recipe_name: str, old_image: str) -> str:
        """Génère une URL d'image réaliste basée sur la recette"""
        
        # Mapping des recettes vers des images réelles
        image_mapping = {
            "boeuf bourguignon": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=800&h=600&fit=crop",
            "tarte tatin": "https://images.unsplash.com/photo-1586987288743-2c1e6e8d637b?w=800&h=600&fit=crop",
            "quiche lorraine": "https://images.unsplash.com/photo-1555939594-58dcbcb1dce0?w=800&h=600&fit=crop",
            "ratatouille": "https://images.unsplash.com/photo-1546548970-71785318a17b?w=800&h=600&fit=crop",
            "lasagnes": "https://images.unsplash.com/photo-1574894709920-9b35ed3a7cbc?w=800&h=600&fit=crop",
            "mousse chocolat": "https://images.unsplash.com/photo-1577666597629-0ae603b2b74c?w=800&h=600&fit=crop",
            "poulet curry": "https://images.unsplash.com/photo-1585937429242-9d75e031a9e0?w=800&h=600&fit=crop",
            "salade caesar": "https://images.unsplash.com/photo-1550309789-719f6af8012f?w=800&h=600&fit=crop"
        }
        
        # Chercher une correspondance
        for key, url in image_mapping.items():
            if key in recipe_name:
                return url
        
        # Image par défaut si aucune correspondance
        return "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=600&fit=crop"
    
    def standardize_all_units(self, recipes: List[Dict]) -> Dict:
        """Standardise toutes les unités dans les ingrédients"""
        standardized_count = 0
        
        # Mapping des standardisations
        unit_mapping = {
            "grammes": "g",
            "gramme": "g", 
            "kilo": "kg",
            "kilogramme": "kg",
            "litre": "l",
            "litres": "l",
            "millilitre": "ml",
            "millilitres": "ml",
            "centilitre": "cl",
            "centilitres": "cl",
            "cuillère à soupe": "c. à soupe",
            "cuillères à soupe": "c. à soupe",
            "cuillère à café": "c. à café",
            "cuillères à café": "c. à café",
            "verre": "verre",
            "verres": "verre"
        }
        
        for recipe in recipes:
            ingredients = recipe.get("ingredients", [])
            for i, ingredient in enumerate(ingredients):
                original = ingredient
                # Standardiser les unités
                for old_unit, new_unit in unit_mapping.items():
                    ingredient = re.sub(rf'\b{old_unit}\b', new_unit, ingredient, flags=re.IGNORECASE)
                
                if ingredient != original:
                    ingredients[i] = ingredient
                    standardized_count += 1
        
        self.cleaning_log.append(f"Unités standardisées: {standardized_count}")
        
        return {
            "standardized": standardized_count,
            "total_ingredients": sum(len(r.get("ingredients", [])) for r in recipes)
        }
    
    def validate_all_content(self, recipes: List[Dict]) -> Dict:
        """Valide la cohérence de tous les contenus"""
        passed = 0
        total = len(recipes)
        issues = []
        
        for recipe in recipes:
            recipe_issues = []
            
            # Validation 1: Nom non vide
            name = recipe.get("name", "")
            if not name or len(name.strip()) < 3:
                recipe_issues.append("Nom trop court ou vide")
            
            # Validation 2: Ingrédients
            ingredients = recipe.get("ingredients", [])
            if len(ingredients) < 3:
                recipe_issues.append("Moins de 3 ingrédients")
            
            # Validation 3: Instructions
            instructions = recipe.get("instructions", [])
            if len(instructions) < 3:
                recipe_issues.append("Moins de 3 instructions")
            
            # Validation 4: Temps cohérents
            try:
                prep = int(recipe.get("prep_time", 0))
                cook = int(recipe.get("cook_time", 0))
                total = int(recipe.get("total_time", 0))
                
                if prep + cook > total + 30:  # Tolérance 30min
                    recipe_issues.append("Temps incohérents")
            except ValueError:
                recipe_issues.append("Temps invalides")
            
            # Validation 5: Portions
            try:
                servings = int(recipe.get("servings", 0))
                if servings < 1 or servings > 20:
                    recipe_issues.append("Portions irréalistes")
            except ValueError:
                recipe_issues.append("Portions invalides")
            
            if recipe_issues:
                issues.append({
                    "recipe": name,
                    "issues": recipe_issues
                })
            else:
                passed += 1
        
        self.cleaning_log.append(f"Validations: {passed}/{total} passées")
        
        return {
            "passed": passed,
            "total": total,
            "issues": issues
        }
    
    def enrich_all_metadata(self, recipes: List[Dict]) -> Dict:
        """Enrichit les métadonnées de toutes les recettes"""
        enriched_count = 0
        
        # Catégories par type de plat
        category_mapping = {
            "boeuf": "Plat Principal",
            "poulet": "Plat Principal", 
            "viande": "Plat Principal",
            "poisson": "Plat Principal",
            "tarte": "Dessert",
            "mousse": "Dessert",
            "gâteau": "Dessert",
            "salade": "Entrée",
            "soupe": "Entrée",
            "ratatouille": "Accompagnement",
            "purée": "Accompagnement",
            "quiche": "Plat Principal",
            "lasagnes": "Plat Principal"
        }
        
        # Tags par ingrédients
        tag_mapping = {
            "légumes": "végétarien",
            "fruits": "fruité",
            "chocolat": "chocolat",
            "fromage": "fromage",
            "crème": "crémeux",
            "vin": "alcoolisé",
            "ail": "aromatique",
            "oignon": "aromatique"
        }
        
        for recipe in recipes:
            name = recipe.get("name", "").lower()
            ingredients = [ing.lower() for ing in recipe.get("ingredients", [])]
            
            # Déterminer la catégorie
            category = "Plat Principal"  # Par défaut
            for keyword, cat in category_mapping.items():
                if keyword in name:
                    category = cat
                    break
            
            # Générer des tags
            tags = ["fait_maison", "recette_facile"]
            for keyword, tag in tag_mapping.items():
                for ingredient in ingredients:
                    if keyword in ingredient:
                        tags.append(tag)
                        break
            
            # Ajouter les métadonnées
            recipe["recipeCategory"] = [category]
            recipe["tags"] = list(set(tags))  # Éliminer les doublons
            recipe["difficulty"] = self.estimate_difficulty(recipe)
            recipe["cost"] = self.estimate_cost(recipe)
            
            enriched_count += 1
        
        self.cleaning_log.append(f"Métadonnées enrichies: {enriched_count}")
        
        return {
            "enriched": enriched_count,
            "categories": len(set(r.get("recipeCategory", ["Plat Principal"])[0] for r in recipes)),
            "tags": len(set(tag for r in recipes for tag in r.get("tags", [])))
        }
    
    def estimate_difficulty(self, recipe: Dict) -> str:
        """Estime la difficulté de la recette"""
        ingredients = len(recipe.get("ingredients", []))
        instructions = len(recipe.get("instructions", []))
        prep_time = int(recipe.get("prep_time", 0))
        cook_time = int(recipe.get("cook_time", 0))
        
        score = 0
        
        # Complexité des ingrédients
        if ingredients > 10:
            score += 2
        elif ingredients > 5:
            score += 1
        
        # Complexité des instructions
        if instructions > 8:
            score += 2
        elif instructions > 5:
            score += 1
        
        # Temps total
        total_time = prep_time + cook_time
        if total_time > 120:
            score += 2
        elif total_time > 60:
            score += 1
        
        if score >= 4:
            return "Difficile"
        elif score >= 2:
            return "Moyen"
        else:
            return "Facile"
    
    def estimate_cost(self, recipe: Dict) -> str:
        """Estime le coût de la recette"""
        ingredients = recipe.get("ingredients", [])
        
        # Compter les ingrédients "chers"
        expensive_ingredients = ["viande", "poisson", "crevettes", "saumon", "fromage", "vin"]
        expensive_count = sum(1 for ing in ingredients if any(exp in ing.lower() for exp in expensive_ingredients))
        
        # Compter les ingrédients bon marché
        cheap_ingredients = ["légumes", "pommes de terre", "riz", "pâtes", "farine", "œufs"]
        cheap_count = sum(1 for ing in ingredients if any(cheap in ing.lower() for cheap in cheap_ingredients))
        
        if expensive_count >= 3:
            return "Élevé"
        elif expensive_count >= 1 or len(ingredients) > 8:
            return "Moyen"
        else:
            return "Économique"
    
    def finalize_recipes(self, recipes: List[Dict], data: Dict) -> Dict:
        """Finalise et prépare les recettes pour l'import"""
        final_count = 0
        
        for recipe in recipes:
            # Ajouter des timestamps
            recipe["cleaned_at"] = datetime.now().isoformat()
            recipe["quality_score"] = self.calculate_quality_score(recipe)
            
            # S'assurer que tous les champs requis existent
            if "servings" not in recipe:
                recipe["servings"] = 4
            
            if "prep_time" not in recipe:
                recipe["prep_time"] = "15"
            
            if "cook_time" not in recipe:
                recipe["cook_time"] = "30"
            
            if "total_time" not in recipe:
                recipe["total_time"] = str(int(recipe["prep_time"]) + int(recipe["cook_time"]))
            
            final_count += 1
        
        # Mettre à jour les métadonnées globales
        data["metadata"]["cleaned_at"] = datetime.now().isoformat()
        data["metadata"]["total_recipes"] = len(recipes)
        data["metadata"]["cleaner"] = "advanced_recipe_cleaner"
        
        # Recalculer les statistiques
        data["statistics"] = self.calculate_global_statistics(recipes)
        
        self.cleaning_log.append(f"Recettes finalisées: {final_count}")
        
        return {
            "finalized": final_count,
            "avg_quality": sum(r.get("quality_score", 0) for r in recipes) / len(recipes)
        }
    
    def calculate_quality_score(self, recipe: Dict) -> float:
        """Calcule un score de qualité pour une recette"""
        score = 0.0
        max_score = 10.0
        
        # Nom (1 point)
        if recipe.get("name") and len(recipe["name"]) > 3:
            score += 1
        
        # Description (1 point)
        if recipe.get("description") and len(recipe["description"]) > 10:
            score += 1
        
        # Ingrédients (2 points)
        ingredients = recipe.get("ingredients", [])
        if len(ingredients) >= 3:
            score += 1
        if len(ingredients) >= 5:
            score += 1
        
        # Instructions (2 points)
        instructions = recipe.get("instructions", [])
        if len(instructions) >= 3:
            score += 1
        if len(instructions) >= 5:
            score += 1
        
        # Temps (1 point)
        try:
            prep = int(recipe.get("prep_time", 0))
            cook = int(recipe.get("cook_time", 0))
            total = int(recipe.get("total_time", 0))
            if prep + cook <= total + 30:
                score += 1
        except ValueError:
            pass
        
        # Image (1 point)
        if recipe.get("image") and recipe["image"].startswith("http"):
            score += 1
        
        # Métadonnées (2 points)
        if recipe.get("recipeCategory"):
            score += 1
        if recipe.get("tags"):
            score += 1
        
        return (score / max_score) * 100
    
    def calculate_global_statistics(self, recipes: List[Dict]) -> Dict:
        """Calcule les statistiques globales"""
        total_instructions = sum(len(r.get("instructions", [])) for r in recipes)
        total_ingredients = sum(len(r.get("ingredients", [])) for r in recipes)
        
        return {
            "total_instructions": total_instructions,
            "total_ingredients": total_ingredients,
            "avg_instructions_per_recipe": total_instructions / len(recipes) if recipes else 0,
            "avg_ingredients_per_recipe": total_ingredients / len(recipes) if recipes else 0,
            "avg_quality_score": sum(r.get("quality_score", 0) for r in recipes) / len(recipes) if recipes else 0,
            "categories": list(set(r.get("recipeCategory", ["Plat Principal"])[0] for r in recipes)),
            "total_tags": len(set(tag for r in recipes for tag in r.get("tags", [])))
        }
    
    def save_cleaned_recipes(self, data: Dict, original_file: str) -> str:
        """Sauvegarde les recettes nettoyées"""
        output_dir = Path(__file__).parent / "cleaned_data"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_dir / f"cleaned_recipes_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Créer aussi un fichier latest
        latest_filename = output_dir / "latest_cleaned_recipes.json"
        with open(latest_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(filename)
    
    def get_cleaning_report(self) -> Dict:
        """Retourne le rapport de nettoyage"""
        return {
            "cleaning_log": self.cleaning_log,
            "cleaned_at": datetime.now().isoformat(),
            "total_operations": len(self.cleaning_log)
        }

if __name__ == "__main__":
    # Test du nettoyeur avancé
    cleaner = AdvancedRecipeCleaner()
    
    scraped_file = "scraped_data/latest_scraped_recipes_mcp.json"
    
    if Path(scraped_file).exists():
        result = cleaner.clean_all_recipes(scraped_file)
        print(f"\n🎉 Nettoyage terminé: {result.get('success', False)}")
    else:
        print(f"❌ Fichier non trouvé: {scraped_file}")
