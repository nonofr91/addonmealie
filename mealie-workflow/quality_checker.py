#!/usr/bin/env python3
"""
QUALITY CHECKER WORKFLOW MEALIE
Vérification complète de la qualité des résultats du workflow
"""

import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import Counter, defaultdict

class WorkflowQualityChecker:
    """Vérificateur de qualité pour le workflow Mealie"""
    
    def __init__(self):
        self.quality_results = {}
        self.quality_scores = {}
        self.issues_found = []
        
    def check_structural_quality(self, scraped_file: str, structured_file: str, import_file: str) -> Dict:
        """
        Vérification Niveau 1: Qualité structurelle
        Format JSON, champs requis, UUIDs, types de données
        """
        print("🔍 NIVEAU 1: VÉRIFICATION STRUCTURELLE")
        print("=" * 50)
        
        structural_results = {
            "scraped_data": self.check_scraped_structure(scraped_file),
            "structured_data": self.check_structured_data_structure(structured_file),
            "import_data": self.check_import_structure(import_file),
            "overall_score": 0
        }
        
        # Calculer le score global structurel
        scores = [
            structural_results["scraped_data"]["score"],
            structural_results["structured_data"]["score"], 
            structural_results["import_data"]["score"]
        ]
        structural_results["overall_score"] = sum(scores) / len(scores)
        
        self.quality_results["structural"] = structural_results
        self.quality_scores["structural"] = structural_results["overall_score"]
        
        return structural_results
    
    def check_scraped_structure(self, filename: str) -> Dict:
        """Vérifie la structure des données scrapées"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            checks = {
                "valid_json": True,
                "metadata_present": "metadata" in data,
                "recipes_present": "recipes" in data,
                "statistics_present": "statistics" in data,
                "recipe_fields": [],
                "issues": []
            }
            
            score = 0
            max_score = 5
            
            # Vérifications de base
            if checks["metadata_present"]:
                score += 1
                metadata = data["metadata"]
                if "version" in metadata and "scraped_at" in metadata and "total_recipes" in metadata:
                    score += 1
                else:
                    checks["issues"].append("Metadata incomplets")
            else:
                checks["issues"].append("Metadata manquant")
            
            if checks["recipes_present"]:
                score += 1
                recipes = data["recipes"]
                if isinstance(recipes, list) and len(recipes) > 0:
                    score += 1
                    # Vérifier les champs des recettes
                    required_fields = ["name", "ingredients", "instructions", "servings"]
                    field_scores = []
                    
                    for recipe in recipes[:3]:  # Vérifier les 3 premières
                        recipe_score = 0
                        for field in required_fields:
                            if field in recipe and recipe[field]:
                                recipe_score += 1
                        field_scores.append(recipe_score / len(required_fields))
                    
                    avg_field_score = sum(field_scores) / len(field_scores)
                    checks["recipe_fields"] = [f"{score*100:.0f}%" for score in field_scores]
                    
                    if avg_field_score >= 0.8:
                        score += 1
                    else:
                        checks["issues"].append("Champs des recettes incomplets")
                else:
                    checks["issues"].append("Recipes vide ou format incorrect")
            else:
                checks["issues"].append("Recipes manquant")
            
            checks["score"] = (score / max_score) * 100
            
            return checks
            
        except Exception as e:
            return {
                "valid_json": False,
                "score": 0,
                "issues": [f"Erreur lecture fichier: {str(e)}"]
            }
    
    def check_structured_data_structure(self, filename: str) -> Dict:
        """Vérifie la structure des données structurées (format Mealie)"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            checks = {
                "valid_json": True,
                "metadata_present": "metadata" in data,
                "recipes_present": "recipes" in data,
                "mealie_format": False,
                "uuids_valid": False,
                "time_format_valid": False,
                "issues": []
            }
            
            score = 0
            max_score = 6
            
            if checks["metadata_present"]:
                score += 1
            else:
                checks["issues"].append("Metadata manquant")
            
            if checks["recipes_present"]:
                score += 1
                recipes = data["recipes"]
                if isinstance(recipes, list) and len(recipes) > 0:
                    recipe = recipes[0]  # Vérifier la première recette
                    
                    # Vérifier le format Mealie
                    mealie_fields = ["name", "slug", "recipeIngredient", "recipeInstructions", "recipeServings"]
                    mealie_score = 0
                    for field in mealie_fields:
                        if field in recipe:
                            mealie_score += 1
                    
                    if mealie_score >= 4:
                        checks["mealie_format"] = True
                        score += 2
                    else:
                        checks["issues"].append(f"Format Mealie incomplet: {mealie_score}/{len(mealie_fields)} champs")
                    
                    # Vérifier les UUIDs
                    if "recipeInstructions" in recipe:
                        uuids_valid = True
                        for instruction in recipe["recipeInstructions"]:
                            if not isinstance(instruction, dict) or "id" not in instruction:
                                uuids_valid = False
                                break
                            try:
                                uuid.UUID(instruction["id"])
                            except ValueError:
                                uuids_valid = False
                                break
                        
                        if uuids_valid:
                            checks["uuids_valid"] = True
                            score += 1
                        else:
                            checks["issues"].append("UUIDs invalides dans les instructions")
                    
                    # Vérifier le format des temps
                    time_fields = ["prepTime", "cookTime", "totalTime"]
                    time_valid = True
                    for field in time_fields:
                        if field in recipe:
                            time_value = recipe[field]
                            if not re.match(r'^PT\d+M$', time_value):
                                time_valid = False
                                break
                    
                    if time_valid or not any(field in recipe for field in time_fields):
                        checks["time_format_valid"] = True
                        score += 1
                    else:
                        checks["issues"].append("Format temps invalide (attendu: PT15M)")
                else:
                    checks["issues"].append("Recipes vide")
            else:
                checks["issues"].append("Recipes manquant")
            
            checks["score"] = (score / max_score) * 100
            
            return checks
            
        except Exception as e:
            return {
                "valid_json": False,
                "score": 0,
                "issues": [f"Erreur lecture fichier: {str(e)}"]
            }
    
    def check_import_structure(self, filename: str) -> Dict:
        """Vérifie la structure du rapport d'import"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            checks = {
                "valid_json": True,
                "metadata_present": "metadata" in data,
                "recipes_present": "recipes" in data,
                "statistics_present": "statistics" in data,
                "recipe_ids_valid": False,
                "issues": []
            }
            
            score = 0
            max_score = 5
            
            if checks["metadata_present"]:
                score += 1
                metadata = data["metadata"]
                if "import_date" in metadata and "total_imported" in metadata:
                    score += 1
                else:
                    checks["issues"].append("Metadata import incomplets")
            else:
                checks["issues"].append("Metadata import manquant")
            
            if checks["recipes_present"]:
                score += 1
                recipes = data["recipes"]
                if isinstance(recipes, list) and len(recipes) > 0:
                    # Vérifier les IDs des recettes
                    ids_valid = True
                    for recipe in recipes:
                        if not isinstance(recipe, dict) or "id" not in recipe:
                            ids_valid = False
                            break
                        try:
                            uuid.UUID(recipe["id"])
                        except ValueError:
                            ids_valid = False
                            break
                    
                    if ids_valid:
                        checks["recipe_ids_valid"] = True
                        score += 1
                    else:
                        checks["issues"].append("IDs de recettes invalides")
                else:
                    checks["issues"].append("Recipes import vide")
            else:
                checks["issues"].append("Recipes import manquant")
            
            if checks["statistics_present"]:
                score += 1
            else:
                checks["issues"].append("Statistics import manquant")
            
            checks["score"] = (score / max_score) * 100
            
            return checks
            
        except Exception as e:
            return {
                "valid_json": False,
                "score": 0,
                "issues": [f"Erreur lecture fichier: {str(e)}"]
            }
    
    def check_content_quality(self, scraped_file: str, structured_file: str) -> Dict:
        """
        Vérification Niveau 2: Qualité du contenu
        Doublons, cohérence, spécificité
        """
        print("\n🔬 NIVEAU 2: VÉRIFICATION CONTENU")
        print("=" * 50)
        
        content_results = {
            "duplicates": self.check_duplicates(scraped_file),
            "time_consistency": self.check_time_consistency(scraped_file),
            "ingredient_quality": self.check_ingredient_quality(structured_file),
            "instruction_quality": self.check_instruction_quality(structured_file),
            "image_quality": self.check_image_quality(scraped_file),
            "overall_score": 0
        }
        
        # Calculer le score global de contenu
        scores = [
            content_results["duplicates"]["score"],
            content_results["time_consistency"]["score"],
            content_results["ingredient_quality"]["score"],
            content_results["instruction_quality"]["score"],
            content_results["image_quality"]["score"]
        ]
        content_results["overall_score"] = sum(scores) / len(scores)
        
        self.quality_results["content"] = content_results
        self.quality_scores["content"] = content_results["overall_score"]
        
        return content_results
    
    def check_duplicates(self, filename: str) -> Dict:
        """Vérifie les doublons de recettes"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = data.get("recipes", [])
            
            # Analyser les doublons
            duplicate_analysis = {
                "total_recipes": len(recipes),
                "unique_names": len(set(r.get("name", "") for r in recipes)),
                "unique_content": 0,
                "duplicate_groups": [],
                "issues": []
            }
            
            # Vérifier les doublons de contenu exact
            content_hashes = {}
            for i, recipe in enumerate(recipes):
                # Créer un hash du contenu (ingrédients + instructions)
                ingredients = tuple(sorted(recipe.get("ingredients", [])))
                instructions = tuple(recipe.get("instructions", []))
                content_hash = hash(ingredients + instructions)
                
                if content_hash in content_hashes:
                    content_hashes[content_hash].append(i)
                else:
                    content_hashes[content_hash] = [i]
            
            # Identifier les groupes de doublons
            for content_hash, indices in content_hashes.items():
                if len(indices) > 1:
                    duplicate_group = {
                        "indices": indices,
                        "names": [recipes[i].get("name", "Sans nom") for i in indices],
                        "sources": [recipes[i].get("source_url", "") for i in indices]
                    }
                    duplicate_analysis["duplicate_groups"].append(duplicate_group)
            
            duplicate_analysis["unique_content"] = len(content_hashes)
            
            # Calculer le score
            if duplicate_analysis["total_recipes"] == 0:
                score = 0
            else:
                duplicate_ratio = (duplicate_analysis["total_recipes"] - duplicate_analysis["unique_content"]) / duplicate_analysis["total_recipes"]
                score = (1 - duplicate_ratio) * 100
            
            duplicate_analysis["score"] = score
            
            if duplicate_ratio > 0.5:
                duplicate_analysis["issues"].append(f"Taux de doublons élevé: {duplicate_ratio*100:.1f}%")
            
            return duplicate_analysis
            
        except Exception as e:
            return {
                "score": 0,
                "issues": [f"Erreur analyse doublons: {str(e)}"]
            }
    
    def check_time_consistency(self, filename: str) -> Dict:
        """Vérifie la cohérence des temps"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = data.get("recipes", [])
            
            time_analysis = {
                "total_recipes": len(recipes),
                "consistent_times": 0,
                "inconsistent_times": [],
                "parsing_errors": [],
                "issues": []
            }
            
            for i, recipe in enumerate(recipes):
                try:
                    prep_time = self.parse_time_value(recipe.get("prep_time", "0"))
                    cook_time = self.parse_time_value(recipe.get("cook_time", "0"))
                    total_time = self.parse_time_value(recipe.get("total_time", "0"))
                    
                    # Vérifier la cohérence (prep + cook ≈ total)
                    calculated_total = prep_time + cook_time
                    
                    # Tolérance de 10 minutes
                    if abs(calculated_total - total_time) <= 10:
                        time_analysis["consistent_times"] += 1
                    else:
                        time_analysis["inconsistent_times"].append({
                            "recipe": recipe.get("name", "Sans nom"),
                            "prep": prep_time,
                            "cook": cook_time,
                            "total": total_time,
                            "calculated": calculated_total,
                            "difference": abs(calculated_total - total_time)
                        })
                
                except Exception as e:
                    time_analysis["parsing_errors"].append({
                        "recipe": recipe.get("name", "Sans nom"),
                        "error": str(e)
                    })
            
            # Calculer le score
            if time_analysis["total_recipes"] == 0:
                score = 0
            else:
                consistency_ratio = time_analysis["consistent_times"] / time_analysis["total_recipes"]
                score = consistency_ratio * 100
            
            time_analysis["score"] = score
            
            if time_analysis["inconsistent_times"]:
                time_analysis["issues"].append(f"{len(time_analysis['inconsistent_times'])} recettes avec temps incohérents")
            
            if time_analysis["parsing_errors"]:
                time_analysis["issues"].append(f"{len(time_analysis['parsing_errors'])} erreurs de parsing temps")
            
            return time_analysis
            
        except Exception as e:
            return {
                "score": 0,
                "issues": [f"Erreur analyse temps: {str(e)}"]
            }
    
    def parse_time_value(self, time_str: str) -> int:
        """Parse une valeur de temps en minutes"""
        if not time_str:
            return 0
        
        time_str = time_str.strip().lower()
        
        # Patterns différents
        patterns = [
            (r'(\d+)\s*heures?', lambda m: int(m.group(1)) * 60),
            (r'(\d+)\s*h', lambda m: int(m.group(1)) * 60),
            (r'(\d+)\s*minutes?', lambda m: int(m.group(1))),
            (r'(\d+)\s*min', lambda m: int(m.group(1))),
            (r'(\d+)$', lambda m: int(m.group(1))),
        ]
        
        for pattern, converter in patterns:
            match = re.search(pattern, time_str)
            if match:
                return converter(match)
        
        # Cas spécial: "2h30"
        match = re.search(r'(\d+)h(\d+)', time_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return hours * 60 + minutes
        
        return 0
    
    def check_ingredient_quality(self, filename: str) -> Dict:
        """Vérifie la qualité des ingrédients"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = data.get("recipes", [])
            
            ingredient_analysis = {
                "total_recipes": len(recipes),
                "total_ingredients": 0,
                "specific_ingredients": 0,
                "generic_ingredients": 0,
                "parsed_correctly": 0,
                "generic_examples": [],
                "issues": []
            }
            
            generic_keywords = ["principal", "accomplement", "exemple", "varié", "assaisonnement"]
            
            for recipe in recipes:
                ingredients = recipe.get("recipeIngredient", [])
                ingredient_analysis["total_ingredients"] += len(ingredients)
                
                for ingredient in ingredients:
                    if isinstance(ingredient, dict):
                        food = ingredient.get("food", "").lower()
                        quantity = ingredient.get("quantity", 0)
                        
                        # Vérifier si c'est générique
                        is_generic = any(keyword in food for keyword in generic_keywords)
                        
                        if is_generic:
                            ingredient_analysis["generic_ingredients"] += 1
                            if len(ingredient_analysis["generic_examples"]) < 5:
                                ingredient_analysis["generic_examples"].append(food)
                        else:
                            ingredient_analysis["specific_ingredients"] += 1
                        
                        # Vérifier le parsing
                        if quantity > 0 or food:
                            ingredient_analysis["parsed_correctly"] += 1
            
            # Calculer le score
            if ingredient_analysis["total_ingredients"] == 0:
                score = 0
            else:
                specificity_ratio = ingredient_analysis["specific_ingredients"] / ingredient_analysis["total_ingredients"]
                parsing_ratio = ingredient_analysis["parsed_correctly"] / ingredient_analysis["total_ingredients"]
                score = (specificity_ratio * 0.7 + parsing_ratio * 0.3) * 100
            
            ingredient_analysis["score"] = score
            
            generic_ratio = ingredient_analysis["generic_ingredients"] / ingredient_analysis["total_ingredients"] if ingredient_analysis["total_ingredients"] > 0 else 0
            if generic_ratio > 0.3:
                ingredient_analysis["issues"].append(f"Taux d'ingrédients génériques élevé: {generic_ratio*100:.1f}%")
            
            return ingredient_analysis
            
        except Exception as e:
            return {
                "score": 0,
                "issues": [f"Erreur analyse ingrédients: {str(e)}"]
            }
    
    def check_instruction_quality(self, filename: str) -> Dict:
        """Vérifie la qualité des instructions"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = data.get("recipes", [])
            
            instruction_analysis = {
                "total_recipes": len(recipes),
                "total_instructions": 0,
                "detailed_instructions": 0,
                "vague_instructions": 0,
                "valid_format": 0,
                "vague_examples": [],
                "issues": []
            }
            
            vague_keywords = ["selon", "comme voulu", "au goût", "général", "exemple", "adapter"]
            
            for recipe in recipes:
                instructions = recipe.get("recipeInstructions", [])
                instruction_analysis["total_instructions"] += len(instructions)
                
                for instruction in instructions:
                    if isinstance(instruction, dict):
                        text = instruction.get("text", "").lower()
                        
                        # Vérifier le format
                        if "id" in instruction and "text" in instruction:
                            instruction_analysis["valid_format"] += 1
                        
                        # Vérifier le niveau de détail
                        word_count = len(text.split())
                        is_vague = any(keyword in text for keyword in vague_keywords) or word_count < 5
                        
                        if is_vague:
                            instruction_analysis["vague_instructions"] += 1
                            if len(instruction_analysis["vague_examples"]) < 3:
                                instruction_analysis["vague_examples"].append(text[:50] + "...")
                        else:
                            instruction_analysis["detailed_instructions"] += 1
            
            # Calculer le score
            if instruction_analysis["total_instructions"] == 0:
                score = 0
            else:
                detail_ratio = instruction_analysis["detailed_instructions"] / instruction_analysis["total_instructions"]
                format_ratio = instruction_analysis["valid_format"] / instruction_analysis["total_instructions"]
                score = (detail_ratio * 0.7 + format_ratio * 0.3) * 100
            
            instruction_analysis["score"] = score
            
            vague_ratio = instruction_analysis["vague_instructions"] / instruction_analysis["total_instructions"] if instruction_analysis["total_instructions"] > 0 else 0
            if vague_ratio > 0.4:
                instruction_analysis["issues"].append(f"Taux d'instructions vagues élevé: {vague_ratio*100:.1f}%")
            
            return instruction_analysis
            
        except Exception as e:
            return {
                "score": 0,
                "issues": [f"Erreur analyse instructions: {str(e)}"]
            }
    
    def check_image_quality(self, filename: str) -> Dict:
        """Vérifie la qualité des images"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = data.get("recipes", [])
            
            image_analysis = {
                "total_recipes": len(recipes),
                "recipes_with_images": 0,
                "valid_urls": 0,
                "local_paths": 0,
                "missing_images": 0,
                "image_sources": [],
                "issues": []
            }
            
            for recipe in recipes:
                image_path = recipe.get("image", "")
                
                if image_path:
                    image_analysis["recipes_with_images"] += 1
                    
                    if image_path.startswith("http"):
                        image_analysis["valid_urls"] += 1
                        image_analysis["image_sources"].append("url")
                    elif image_path.startswith("scraped_images/"):
                        image_analysis["local_paths"] += 1
                        image_analysis["image_sources"].append("local")
                    else:
                        image_analysis["missing_images"] += 1
                        image_analysis["image_sources"].append("invalid")
                else:
                    image_analysis["missing_images"] += 1
            
            # Calculer le score
            if image_analysis["total_recipes"] == 0:
                score = 0
            else:
                url_ratio = image_analysis["valid_urls"] / image_analysis["total_recipes"]
                score = url_ratio * 100  # Seules les URLs valides ont 100%
            
            image_analysis["score"] = score
            
            if image_analysis["local_paths"] > 0:
                image_analysis["issues"].append(f"{image_analysis['local_paths']} chemins locaux (non fonctionnels)")
            
            if image_analysis["missing_images"] > 0:
                image_analysis["issues"].append(f"{image_analysis['missing_images']} recettes sans image")
            
            return image_analysis
            
        except Exception as e:
            return {
                "score": 0,
                "issues": [f"Erreur analyse images: {str(e)}"]
            }
    
    def check_business_quality(self, structured_file: str, import_file: str) -> Dict:
        """
        Vérification Niveau 3: Qualité métier
        Nutrition, catégories, utilisabilité
        """
        print("\n🎯 NIVEAU 3: VÉRIFICATION MÉTIER")
        print("=" * 50)
        
        business_results = {
            "nutrition_quality": self.check_nutrition_quality(structured_file),
            "category_quality": self.check_category_quality(structured_file),
            "usability_quality": self.check_usability_quality(structured_file, import_file),
            "overall_score": 0
        }
        
        # Calculer le score global métier
        scores = [
            business_results["nutrition_quality"]["score"],
            business_results["category_quality"]["score"],
            business_results["usability_quality"]["score"]
        ]
        business_results["overall_score"] = sum(scores) / len(scores)
        
        self.quality_results["business"] = business_results
        self.quality_scores["business"] = business_results["overall_score"]
        
        return business_results
    
    def check_nutrition_quality(self, filename: str) -> Dict:
        """Vérifie la qualité des informations nutritionnelles"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = data.get("recipes", [])
            
            nutrition_analysis = {
                "total_recipes": len(recipes),
                "with_nutrition": 0,
                "valid_calories": 0,
                "valid_macros": 0,
                "calorie_ranges": {"low": 0, "medium": 0, "high": 0},
                "issues": []
            }
            
            for recipe in recipes:
                nutrition = recipe.get("nutrition", {})
                
                if nutrition and "calories" in nutrition:
                    nutrition_analysis["with_nutrition"] += 1
                    
                    calories = nutrition["calories"]
                    if isinstance(calories, (int, float)) and calories > 0:
                        nutrition_analysis["valid_calories"] += 1
                        
                        # Catégoriser les calories
                        if calories < 200:
                            nutrition_analysis["calorie_ranges"]["low"] += 1
                        elif calories < 600:
                            nutrition_analysis["calorie_ranges"]["medium"] += 1
                        else:
                            nutrition_analysis["calorie_ranges"]["high"] += 1
                    
                    # Vérifier les macros
                    macros = ["proteinContent", "carbohydrateContent", "fatContent"]
                    valid_macros = 0
                    for macro in macros:
                        if macro in nutrition and nutrition[macro]:
                            valid_macros += 1
                    
                    if valid_macros >= 2:
                        nutrition_analysis["valid_macros"] += 1
            
            # Calculer le score
            if nutrition_analysis["total_recipes"] == 0:
                score = 0
            else:
                nutrition_ratio = nutrition_analysis["with_nutrition"] / nutrition_analysis["total_recipes"]
                calorie_ratio = nutrition_analysis["valid_calories"] / nutrition_analysis["total_recipes"]
                macro_ratio = nutrition_analysis["valid_macros"] / nutrition_analysis["total_recipes"]
                score = (nutrition_ratio * 0.4 + calorie_ratio * 0.4 + macro_ratio * 0.2) * 100
            
            nutrition_analysis["score"] = score
            
            if nutrition_ratio < 0.5:
                nutrition_analysis["issues"].append("Moins de 50% des recettes ont des infos nutritionnelles")
            
            return nutrition_analysis
            
        except Exception as e:
            return {
                "score": 0,
                "issues": [f"Erreur analyse nutrition: {str(e)}"]
            }
    
    def check_category_quality(self, filename: str) -> Dict:
        """Vérifie la qualité des catégories et tags"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipes = data.get("recipes", [])
            
            category_analysis = {
                "total_recipes": len(recipes),
                "with_categories": 0,
                "with_tags": 0,
                "unique_categories": set(),
                "unique_tags": set(),
                "avg_categories_per_recipe": 0,
                "avg_tags_per_recipe": 0,
                "issues": []
            }
            
            total_categories = 0
            total_tags = 0
            
            for recipe in recipes:
                categories = recipe.get("recipeCategory", [])
                tags = recipe.get("tags", [])
                
                if categories:
                    category_analysis["with_categories"] += 1
                    category_analysis["unique_categories"].update(categories)
                    total_categories += len(categories)
                
                if tags:
                    category_analysis["with_tags"] += 1
                    category_analysis["unique_tags"].update(tags)
                    total_tags += len(tags)
            
            category_analysis["unique_categories"] = list(category_analysis["unique_categories"])
            category_analysis["unique_tags"] = list(category_analysis["unique_tags"])
            
            if category_analysis["total_recipes"] > 0:
                category_analysis["avg_categories_per_recipe"] = total_categories / category_analysis["total_recipes"]
                category_analysis["avg_tags_per_recipe"] = total_tags / category_analysis["total_recipes"]
            
            # Calculer le score
            if category_analysis["total_recipes"] == 0:
                score = 0
            else:
                category_ratio = category_analysis["with_categories"] / category_analysis["total_recipes"]
                tag_ratio = category_analysis["with_tags"] / category_analysis["total_recipes"]
                diversity_bonus = min(len(category_analysis["unique_categories"]) / 5, 1.0) * 20  # Bonus pour diversité
                score = (category_ratio * 0.4 + tag_ratio * 0.4 + diversity_bonus * 0.2) * 100
            
            category_analysis["score"] = score
            
            if category_ratio < 0.5:
                category_analysis["issues"].append("Moins de 50% des recettes ont des catégories")
            
            return category_analysis
            
        except Exception as e:
            return {
                "score": 0,
                "issues": [f"Erreur analyse catégories: {str(e)}"]
            }
    
    def check_usability_quality(self, structured_file: str, import_file: str) -> Dict:
        """Vérifie l'utilisabilité pour les agents MCP"""
        try:
            with open(structured_file, 'r', encoding='utf-8') as f:
                structured_data = json.load(f)
            
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            recipes = structured_data.get("recipes", [])
            imported_recipes = import_data.get("recipes", [])
            
            usability_analysis = {
                "total_structured": len(recipes),
                "total_imported": len(imported_recipes),
                "import_success_rate": 0,
                "complete_recipes": 0,
                "agent_ready": 0,
                "issues": []
            }
            
            if usability_analysis["total_structured"] > 0:
                usability_analysis["import_success_rate"] = usability_analysis["total_imported"] / usability_analysis["total_structured"]
            
            # Vérifier les recettes complètes
            for recipe in recipes:
                required_fields = ["name", "recipeIngredient", "recipeInstructions", "recipeServings"]
                if all(field in recipe and recipe[field] for field in required_fields):
                    usability_analysis["complete_recipes"] += 1
                    
                    # Vérifier si prête pour les agents
                    nutrition = recipe.get("nutrition", {})
                    categories = recipe.get("recipeCategory", [])
                    
                    if (nutrition.get("calories", 0) > 0 and 
                        categories and 
                        len(recipe.get("recipeIngredient", [])) >= 3):
                        usability_analysis["agent_ready"] += 1
            
            # Calculer le score
            scores = [
                usability_analysis["import_success_rate"] * 100,
                (usability_analysis["complete_recipes"] / usability_analysis["total_structured"]) * 100 if usability_analysis["total_structured"] > 0 else 0,
                (usability_analysis["agent_ready"] / usability_analysis["total_structured"]) * 100 if usability_analysis["total_structured"] > 0 else 0
            ]
            
            usability_analysis["score"] = sum(scores) / len(scores)
            
            if usability_analysis["import_success_rate"] < 0.8:
                usability_analysis["issues"].append(f"Taux d'import faible: {usability_analysis['import_success_rate']*100:.1f}%")
            
            if usability_analysis["agent_ready"] < usability_analysis["total_structured"]:
                usability_analysis["issues"].append(f"{usability_analysis['total_structured'] - usability_analysis['agent_ready']} recettes non prêtes pour les agents")
            
            return usability_analysis
            
        except Exception as e:
            return {
                "score": 0,
                "issues": [f"Erreur analyse utilisabilité: {str(e)}"]
            }
    
    def generate_quality_report(self) -> Dict:
        """Génère le rapport complet de qualité"""
        print("\n📋 RAPPORT COMPLET DE QUALITÉ")
        print("=" * 60)
        
        # Calculer les scores globaux
        global_scores = {
            "structural": self.quality_scores.get("structural", 0),
            "content": self.quality_scores.get("content", 0),
            "business": self.quality_scores.get("business", 0)
        }
        
        # Score global pondéré
        weights = {"structural": 0.3, "content": 0.4, "business": 0.3}
        global_score = sum(global_scores[level] * weights[level] for level in global_scores)
        
        # Collecter tous les problèmes
        all_issues = []
        for level, results in self.quality_results.items():
            if isinstance(results, dict):
                for category, analysis in results.items():
                    if isinstance(analysis, dict) and "issues" in analysis:
                        for issue in analysis["issues"]:
                            all_issues.append({
                                "level": level,
                                "category": category,
                                "issue": issue
                            })
        
        # Déterminer le statut
        status = "EXCELLENT" if global_score >= 90 else "BON" if global_score >= 75 else "ACCEPTABLE" if global_score >= 60 else "INSUFFISANT"
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "global_score": global_score,
            "status": status,
            "level_scores": global_scores,
            "detailed_results": self.quality_results,
            "total_issues": len(all_issues),
            "critical_issues": [issue for issue in all_issues if any(keyword in issue["issue"].lower() for keyword in ["doublon", "erreur", "manquant", "invalide"])],
            "recommendations": self.generate_recommendations(global_scores, all_issues),
            "next_steps": self.generate_next_steps(status, global_scores)
        }
        
        # Afficher le résumé
        print(f"🎯 SCORE GLOBAL: {global_score:.1f}/100 - {status}")
        print(f"📊 Niveaux: Structurel {global_scores['structural']:.1f} | Contenu {global_scores['content']:.1f} | Métier {global_scores['business']:.1f}")
        print(f"🚨 Problèmes: {len(all_issues)} au total, {len(report['critical_issues'])} critiques")
        
        return report
    
    def generate_recommendations(self, scores: Dict, issues: List) -> List[str]:
        """Génère les recommandations basées sur les résultats"""
        recommendations = []
        
        # Recommandations par niveau
        if scores["structural"] < 80:
            recommendations.append("🔧 Améliorer la structure des données (JSON, UUIDs, format temps)")
        
        if scores["content"] < 80:
            recommendations.append("📝 Améliorer la qualité du contenu (réduire les doublons, corriger les temps)")
        
        if scores["business"] < 80:
            recommendations.append("🎯 Améliorer l'utilisabilité (nutrition, catégories, agents MCP)")
        
        # Recommandations spécifiques
        duplicate_issues = [issue for issue in issues if "doublon" in issue["issue"].lower()]
        if duplicate_issues:
            recommendations.append("🔄 Corriger les templates de scraping pour éliminer les doublons")
        
        time_issues = [issue for issue in issues if "temps" in issue["issue"].lower()]
        if time_issues:
            recommendations.append("⏰ Améliorer le parsing des temps (gérer '2h30', '2 heures')")
        
        image_issues = [issue for issue in issues if "image" in issue["issue"].lower()]
        if image_issues:
            recommendations.append("🖼️ Implémenter la recherche d'images réelles avec mcp2_search_images")
        
        return recommendations
    
    def generate_next_steps(self, status: str, scores: Dict) -> List[str]:
        """Génère les prochaines étapes"""
        if status == "EXCELLENT":
            return ["✅ Workflow validé - Prêt pour la production", "🚀 Déployer en environnement réel"]
        
        steps = []
        
        if scores["structural"] < 90:
            steps.append("1. Corriger les problèmes structurels")
        
        if scores["content"] < 90:
            steps.append("2. Améliorer la qualité du contenu")
        
        if scores["business"] < 90:
            steps.append("3. Optimiser l'utilisabilité métier")
        
        steps.append("4. Relancer la vérification complète")
        steps.append("5. Valider pour la production")
        
        return steps
    
    def save_quality_report(self, report: Dict) -> str:
        """Sauvegarde le rapport de qualité"""
        try:
            output_dir = Path(__file__).parent.parent / "quality_reports"
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = output_dir / f"mealie_quality_report_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # Créer aussi un fichier latest
            latest_filename = output_dir / "latest_mealie_quality_report.json"
            with open(latest_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Rapport sauvegardé: {filename}")
            return str(filename)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde rapport: {e}")
            return ""
    
    def run_complete_quality_check(self, scraped_file: str, structured_file: str, import_file: str) -> Dict:
        """Lance la vérification qualité complète"""
        print("🎯 VÉRIFICATION QUALITÉ COMPLÈTE WORKFLOW MEALIE")
        print("📋 Analyse structurelle, contenu et utilité métier")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Niveau 1: Structurelle
        structural_results = self.check_structural_quality(scraped_file, structured_file, import_file)
        
        # Niveau 2: Contenu
        content_results = self.check_content_quality(scraped_file, structured_file)
        
        # Niveau 3: Métier
        business_results = self.check_business_quality(structured_file, import_file)
        
        # Rapport final
        report = self.generate_quality_report()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        report["duration"] = duration
        report["files_analyzed"] = {
            "scraped": scraped_file,
            "structured": structured_file,
            "import": import_file
        }
        
        # Sauvegarder le rapport
        report_file = self.save_quality_report(report)
        
        print(f"\n🎉 VÉRIFICATION TERMINÉE en {duration:.1f}s")
        print(f"📊 Score global: {report['global_score']:.1f}/100 - {report['status']}")
        
        return report

if __name__ == "__main__":
    # Test du quality checker
    checker = WorkflowQualityChecker()
    
    scraped_file = "scraped_data/latest_scraped_recipes_mcp.json"
    structured_file = "structured_data/latest_mealie_structured_recipes.json"
    import_file = "import_reports/latest_mealie_import_report.json"
    
    report = checker.run_complete_quality_check(scraped_file, structured_file, import_file)
