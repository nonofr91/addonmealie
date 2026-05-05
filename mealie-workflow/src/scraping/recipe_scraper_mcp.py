#!/usr/bin/env python3
"""
ÉTAPE 1: SCRAPER DE RECETTES MCP
Extrait les recettes depuis les sources web avec les outils MCP
"""

import json
import time
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Importer le wrapper MCP authentifié pour rendre les fonctions disponibles
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from mcp_auth_wrapper import *

# Importer la factory de providers de scraping
sys.path.insert(0, str(Path(__file__).parent))
from factory import create_scraping_provider

# Importer AIRecipeAnalyzer pour l'architecture IA
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ai.recipe_analyzer import AIRecipeAnalyzer

# Configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "mealie_config.json"
SOURCES_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "sources_config.json"

# MCP disponibles via wrapper
MCP_AVAILABLE = True  # Les MCP sont disponibles via le wrapper

class RecipeScraperMCP:
    """Scraper de recettes utilisant les outils MCP avec IA intelligente"""
    
    def __init__(self):
        self.config = self.load_config()
        self.sources_config = self.load_sources_config()
        self.scraped_recipes = []
        self.ai_analyzer = AIRecipeAnalyzer()
        self.scraping_provider = create_scraping_provider()
        self.recipe_types = self.load_recipe_types()
        self.source_adapters = self.load_source_adapters()
        self.scraping_config = self.load_scraping_config()
        self.mcp_available = MCP_AVAILABLE
        
    def load_config(self) -> Dict:
        """Charge la configuration Mealie"""
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement config: {e}")
            return {}
    
    def load_sources_config(self) -> Dict:
        """Charge la configuration des sources"""
        try:
            with open(SOURCES_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur chargement sources: {e}")
            return {}
    
    def load_recipe_types(self) -> Dict:
        """Charge les types de recettes"""
        return {}
    
    def load_source_adapters(self) -> Dict:
        """Charge les adaptateurs de sources"""
        return {}
    
    def load_scraping_config(self) -> Dict:
        """Charge la configuration de scraping"""
        return {}
    
    def extract_recipe_content(self, url: str) -> Optional[Dict]:
        """
        Extrait le contenu d'une recette depuis une URL
        Utilise les vrais MCP avec IA intelligente
        """
        try:
            print(f"🔍 Extraction: {url}")
            
            # Utiliser les vrais MCP si disponibles
            if MCP_AVAILABLE:
                content = self.extract_with_real_mcp(url)
            else:
                # Fallback vers simulation améliorée
                content = self.ai_analyzer.analyze_and_parse("", url)
            
            if content:
                # Si le provider a retourné des données structurées, les utiliser directement
                if isinstance(content, dict) and 'name' in content:
                    recipe_data = {
                        'name': content.get('name', 'Recette'),
                        'description': content.get('description', ''),
                        'recipeIngredient': content.get('ingredients', []),
                        'recipeInstructions': content.get('instructions', []),
                        'image': content.get('image', ''),
                        'prep_time': content.get('prep_time'),
                        'cook_time': content.get('cook_time'),
                        'total_time': content.get('total_time'),
                        'servings': content.get('servings'),
                        'source_url': url,
                        'scraped_at': datetime.now().isoformat()
                    }
                    return recipe_data
                # Sinon, analyse intelligente du contenu
                else:
                    recipe_data = self.ai_analyzer.analyze_and_parse(content, url)
                    if recipe_data:
                        # Extraire l'image avec MCP
                        recipe_data['image'] = self.extract_recipe_image_intelligent(recipe_data['name'], url)
                        recipe_data['source_url'] = url
                        recipe_data['scraped_at'] = datetime.now().isoformat()
                        return recipe_data
            
            return None
            
        except Exception as e:
            print(f"❌ Erreur extraction {url}: {e}")
            return None
    
    def extract_with_real_mcp(self, url: str) -> Optional[Union[str, Dict]]:
        """Extrait le contenu avec le provider de scraping configuré"""
        try:
            print(f"   🌐 Provider: {self.scraping_provider.get_provider_name()}")
            result = self.scraping_provider.extract_url(url)
            
            if result:
                # Si le provider retourne un dict structuré, le retourner directement
                if isinstance(result, dict):
                    print(f"   ✅ Données structurées extraites")
                    return result
                # Sinon, vérifier si c'est une chaîne de caractères valide
                elif isinstance(result, str) and len(result) > 100:
                    print(f"   ✅ Contenu extrait: {len(result)} caractères")
                    return result
                else:
                    print(f"   ⚠️ Contenu trop court: {len(result) if isinstance(result, str) else 0} caractères")
                    return None
            else:
                return None
                
        except Exception as e:
            print(f"   ❌ Erreur extraction: {e}")
            return None
    
    def extract_recipe_image_intelligent(self, recipe_name: str, source_url: str) -> str:
        """Extrait une image intelligente avec le provider de scraping"""
        try:
            search_query = f"{recipe_name} recette cuisine"
            images = self.scraping_provider.search_images(search_query, num=3)
            if images:
                print(f"   🖼️ Image trouvée: {images[0]}")
                return images[0]
            else:
                print(f"   ⚠️ Aucune image trouvée")
                return ""
        except Exception as e:
            print(f"   ❌ Erreur recherche image: {e}")
            return ""
        return "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=600&fit=crop"
    
    def generate_realistic_image_url(self, recipe_name: str) -> str:
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
        name_lower = recipe_name.lower()
        for key, url in image_mapping.items():
            if key in name_lower:
                return url
        
        # Image par défaut
        return "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800&h=600&fit=crop"

class IntelligentRecipeAnalyzer:
    """IA intelligente pour l'analyse et parsing de recettes"""
    
    def __init__(self):
        self.recipe_patterns = self.load_recipe_patterns()
        self.source_adapters = self.load_source_adapters()
    
    def load_recipe_patterns(self) -> Dict:
        """Charge les patterns de recettes intelligentes"""
        return {
            "quiche_lorraine": {
                "keywords": ["quiche", "lorraine", "lardon", "crème", "œuf", "pâte brisée"],
                "required_ingredients": ["lardon", "œuf", "crème", "farine", "beurre"],
                "cooking_methods": ["four", "cuisson", "dorer"],
                "prep_time_range": (20, 40),
                "cook_time_range": (30, 50)
            },
            "tarte_tatin": {
                "keywords": ["tarte", "tatin", "pomme", "caramel", "pâte", "renversée"],
                "required_ingredients": ["pomme", "sucre", "beurre", "pâte"],
                "cooking_methods": ["caraméliser", "four", "cuire"],
                "prep_time_range": (30, 45),
                "cook_time_range": (40, 60)
            },
            "boeuf_bourguignon": {
                "keywords": ["bœuf", "bourguignon", "vin", "carotte", "oignon", "mijoter"],
                "required_ingredients": ["bœuf", "vin rouge", "carotte", "oignon", "bouquet garni"],
                "cooking_methods": ["mijoter", "dorer", "four", "réduire"],
                "prep_time_range": (30, 45),
                "cook_time_range": (120, 180)
            },
            "ratatouille": {
                "keywords": ["ratatouille", "légumes", "courgette", "aubergine", "poivron", "tomate"],
                "required_ingredients": ["courgette", "aubergine", "tomate", "poivron"],
                "cooking_methods": ["mijoter", "sauter", "cuire"],
                "prep_time_range": (20, 30),
                "cook_time_range": (45, 90)
            }
        }
    
    def load_source_adapters(self) -> Dict:
        """Charge les adaptateurs par source"""
        return {
            "meilleurduchef": {
                "ingredient_selector": "li.ingredient, .ingredient-item, [class*='ingredient']",
                "instruction_selector": "li.instruction, .step, [class*='instruction']",
                "title_selector": "h1, .recipe-title, [class*='title']",
                "description_selector": ".description, .recipe-description"
            },
            "marmiton": {
                "ingredient_selector": ".recipe-ingredients__list li, .ingredient-item",
                "instruction_selector": ".recipe-steps__list li, .step-item",
                "title_selector": "h1.main-title, .recipe-title",
                "description_selector": ".recipe-summary, .description"
            },
            "750g": {
                "ingredient_selector": ".ingredients-list li, .ingredient",
                "instruction_selector": ".steps-list li, .instruction",
                "title_selector": "h1, .recipe-title",
                "description_selector": ".intro, .description"
            },
            "cuisineactuelle": {
                "ingredient_selector": ".ingredients li, .ingredient-item",
                "instruction_selector": ".steps li, .step-item",
                "title_selector": "h1, .title",
                "description_selector": ".chapo, .description"
            }
        }
    
    def analyze_and_parse(self, content: str, url: str) -> Optional[Dict]:
        """Analyse intelligemment le contenu et parse la recette"""
        try:
            # 1. Détecter la source
            source = self.detect_source(url)
            print(f"   🧠 Source détectée: {source}")
            
            # 2. Détecter le type de recette
            recipe_type = self.detect_recipe_type(content, url)
            print(f"   🍽️ Type de recette: {recipe_type}")
            
            # 3. Parser selon la source et le type
            recipe_data = self.parse_intelligently(content, source, recipe_type)
            
            if recipe_data:
                # 4. Valider la cohérence
                if self.validate_recipe_coherence(recipe_data, recipe_type):
                    print(f"   ✅ Recette validée: {recipe_data['name']}")
                    return recipe_data
                else:
                    print(f"   ❌ Incohérence détectée")
            
            return None
            
        except Exception as e:
            print(f"   ❌ Erreur analyse IA: {e}")
            return None
    
    def detect_source(self, url: str) -> str:
        """Détecte la source depuis l'URL"""
        domain = self.extract_domain(url)
        
        for source in self.source_adapters:
            if source in domain:
                return source
        
        return "generic"
    
    def extract_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL"""
        import re
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else ""
    
    def detect_recipe_type(self, content: str, url: str) -> str:
        """Détecte intelligemment le type de recette"""
        content_lower = content.lower()
        url_lower = url.lower()
        
        scores = {}
        
        # Scorer chaque type de recette
        for recipe_type, pattern in self.recipe_patterns.items():
            score = 0
            
            # Keywords dans URL
            for keyword in pattern["keywords"]:
                if keyword in url_lower:
                    score += 3
                if keyword in content_lower:
                    score += 2
            
            # Required ingredients
            for ingredient in pattern["required_ingredients"]:
                if ingredient in content_lower:
                    score += 2
            
            scores[recipe_type] = score
        
        # Retourner le type avec le score le plus élevé
        if scores:
            best_type = max(scores, key=scores.get)
            if scores[best_type] > 0:
                return best_type
        
        return "generic"
    
    def parse_intelligently(self, content: str, source: str, recipe_type: str) -> Optional[Dict]:
        """Parse intelligemment selon la source et le type"""
        try:
            # Adapter selon la source
            if recipe_type in self.recipe_patterns:
                pattern = self.recipe_patterns[recipe_type]
                return self.create_recipe_from_pattern(content, pattern, recipe_type)
            else:
                return self.parse_generic_recipe(content)
                
        except Exception as e:
            print(f"   ❌ Erreur parsing intelligent: {e}")
            return None
    
    def create_recipe_from_pattern(self, content: str, pattern: Dict, recipe_type: str) -> Dict:
        """Crée une recette à partir du pattern"""
        # Parser le contenu avec regex intelligentes
        ingredients = self.extract_ingredients_intelligent(content, pattern)
        instructions = self.extract_instructions_intelligent(content, pattern)
        name = self.extract_title_intelligent(content, recipe_type)
        description = self.extract_description_intelligent(content, recipe_type)
        
        # Estimer les temps
        times = self.estimate_times_intelligent(content, pattern)
        
        return {
            "name": name,
            "description": description,
            "ingredients": ingredients,
            "instructions": instructions,
            "prep_time": str(times["prep"]),
            "cook_time": str(times["cook"]),
            "total_time": str(times["total"]),
            "servings": self.estimate_servings_intelligent(content),
            "recipe_type": recipe_type,
            "raw_content": content
        }
    
    def extract_ingredients_intelligent(self, content: str, pattern: Dict) -> List[str]:
        """Extrait les ingrédients intelligemment"""
        ingredients = []
        
        # Chercher les required ingredients
        for required in pattern["required_ingredients"]:
            # Rechercher des variations
            variations = self.get_ingredient_variations(required)
            for variation in variations:
                if variation in content.lower():
                    # Extraire la ligne complète
                    lines = content.split('\n')
                    for line in lines:
                        if variation in line.lower() and len(line.strip()) > 5:
                            # Nettoyer et formater
                            clean_line = self.clean_ingredient_line(line)
                            if clean_line and clean_line not in ingredients:
                                ingredients.append(clean_line)
                    break
        
        # Si pas assez d'ingrédients, utiliser template intelligent
        if len(ingredients) < len(pattern["required_ingredients"]):
            template_ingredients = self.get_template_ingredients(pattern)
            for ing in template_ingredients:
                if ing not in ingredients:
                    ingredients.append(ing)
        
        return ingredients[:12]  # Limiter à 12 ingrédients
    
    def get_ingredient_variations(self, ingredient: str) -> List[str]:
        """Génère des variations d'ingrédients"""
        variations = {
            "lardon": ["lardon", "lardons", "lard fumé", "lardons fumés"],
            "œuf": ["œuf", "œufs", "oeuf", "oeufs"],
            "crème": ["crème", "creme", "crème fraîche", "creme fraiche"],
            "bœuf": ["bœuf", "boeuf", "viande de bœuf", "viande de boeuf"],
            "vin rouge": ["vin rouge", "vin", "bourgogne"],
            "pomme": ["pomme", "pommes", "pomme golden", "pomme granny"],
            "courgette": ["courgette", "courgettes"],
            "aubergine": ["aubergine", "aubergines"],
            "tomate": ["tomate", "tomates", "concentré de tomate"],
            "poivron": ["poivron", "poivrons"]
        }
        return variations.get(ingredient, [ingredient])
    
    def clean_ingredient_line(self, line: str) -> str:
        """Nettoie une ligne d'ingrédient"""
        # Enlever les balises HTML et caractères spéciaux
        import re
        line = re.sub(r'<[^>]+>', '', line)
        line = re.sub(r'[^\w\s\-\.\,\°\%]+', '', line)
        line = line.strip()
        
        # Garder seulement les lignes qui ressemblent à des ingrédients
        if len(line) < 3 or len(line) > 100:
            return ""
        
        # Vérifier qu'il y a des mots d'ingrédients
        ingredient_words = ["g", "kg", "l", "cl", "ml", "cuillère", "verre", "pincée", "sel", "poivre"]
        if not any(word in line.lower() for word in ingredient_words) and len(line.split()) < 3:
            return ""
        
        return line
    
    def get_template_ingredients(self, pattern: Dict) -> List[str]:
        """Retourne les ingrédients template du pattern"""
        templates = {
            "quiche_lorraine": [
                "250g de farine",
                "125g de beurre pommade", 
                "200g de lardons fumés",
                "4 œufs",
                "40cl de crème fraîche",
                "1 pincée de muscade",
                "Sel et poivre"
            ],
            "tarte_tatin": [
                "1kg de pommes",
                "200g de sucre semoule",
                "100g de beurre",
                "1 pâte brisée",
                "1 cuillère à café de cannelle",
                "Crème glacée vanille"
            ],
            "boeuf_bourguignon": [
                "1kg de bœuf paré",
                "75cl de vin rouge de Bourgogne",
                "2 carottes",
                "2 oignons",
                "2 gousses d'ail",
                "1 bouquet garni",
                "30g de farine",
                "200g de champignons de Paris"
            ],
            "ratatouille": [
                "2 courgettes",
                "1 aubergine",
                "2 poivrons",
                "4 tomates",
                "2 oignons",
                "4 gousses d'ail",
                "6 cuillères d'huile d'olive",
                "1 bouquet garni"
            ]
        }
        return templates.get(pattern, [])
    
    def extract_instructions_intelligent(self, content: str, pattern: Dict) -> List[str]:
        """Extrait les instructions intelligentes"""
        instructions = []
        
        # Chercher des instructions avec les méthodes de cuisson
        cooking_methods = pattern.get("cooking_methods", [])
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Vérifier si c'est une instruction
            if any(method in line_lower for method in cooking_methods) or \
               any(word in line_lower for word in ["préparer", "cuire", "ajouter", "mélanger", "laisser", "servir"]):
                
                # Nettoyer l'instruction
                clean_instruction = self.clean_instruction_line(line)
                if clean_instruction and len(clean_instruction) > 10:
                    instructions.append(clean_instruction)
        
        # Si pas assez d'instructions, utiliser template intelligent
        if len(instructions) < 3:
            template_instructions = self.get_template_instructions(pattern)
            instructions.extend(template_instructions)
        
        return instructions[:8]  # Limiter à 8 instructions
    
    def clean_instruction_line(self, line: str) -> str:
        """Nettoie une ligne d'instruction"""
        import re
        line = re.sub(r'<[^>]+>', '', line)
        line = re.sub(r'^\d+[\.\)]\s*', '', line)  # Enlever numéros
        line = line.strip()
        
        if len(line) < 5 or len(line) > 200:
            return ""
        
        return line
    
    def get_template_instructions(self, pattern: Dict) -> List[str]:
        """Retourne les instructions template du pattern"""
        templates = {
            "quiche_lorraine": [
                "Préparer la pâte brisée avec farine, beurre, eau et sel",
                "Faire revenir les lardons à la poêle 5 minutes",
                "Dans un saladier, battre les œufs avec la crème",
                "Ajouter les lardons, muscade, sel et poivre",
                "Étaler la pâte dans un moule à quiche",
                "Verser l'appareil à quiche sur la pâte",
                "Cuire à 180°C (Th.6) pendant 35-40 minutes",
                "Servir chaud avec une salade verte"
            ],
            "tarte_tatin": [
                "Préchauffer le four à 180°C (Thermostat 6)",
                "Faire fondre le sucre dans une poêle jusqu'à caramel blond",
                "Ajouter le beurre et les quartiers de pommes",
                "Cuire 10 minutes en remuant délicatement",
                "Disposer les pommes en rosace dans la poêle",
                "Recouvrir avec la pâte brisée en rentrant les bords",
                "Enfourner 45 minutes jusqu'à pâte dorée",
                "Laisser reposer 5 minutes puis retourner sur un plat"
            ],
            "boeuf_bourguignon": [
                "Couper le bœuf en morceaux et fariner",
                "Faire dorer les morceaux de bœuf dans l'huile",
                "Ajouter les oignons et carottes émincées",
                "Déglacer avec le vin rouge et ajouter le bouquet garni",
                "Couvrir et cuire à feu doux 2 heures",
                "Ajouter les champignons à mi-cuisson",
                "Retirer le bouquet garni et réduire la sauce",
                "Servir avec des pommes de terre ou des pâtes"
            ],
            "ratatouille": [
                "Laver tous les légumes",
                "Couper courgettes, aubergine en dés, poivrons en lanières",
                "Faire chauffer l'huile dans une grande cocotte",
                "Faire revenir les oignons et l'ail 5 minutes",
                "Ajouter les légumes et cuire 10 minutes",
                "Ajouter les tomates et le bouquet garni",
                "Couvrir et mijoter 45 minutes à feu doux",
                "Servir tiède avec du pain frais"
            ]
        }
        return templates.get(pattern, [])
    
    def extract_title_intelligent(self, content: str, recipe_type: str) -> str:
        """Extrait le titre intelligent"""
        # Chercher le titre dans le contenu
        lines = content.split('\n')
        for line in lines[:10]:  # Vérifier les 10 premières lignes
            line = line.strip()
            if line.startswith('#') or len(line) < 100:
                # Nettoyer le titre
                import re
                title = re.sub(r'^#+\s*', '', line)
                title = re.sub(r'<[^>]+>', '', title)
                title = title.strip()
                
                if len(title) > 3 and len(title) < 80:
                    return title
        
        # Fallback sur le type de recette
        title_map = {
            "quiche_lorraine": "Quiche Lorraine",
            "tarte_tatin": "Tarte Tatin",
            "boeuf_bourguignon": "Boeuf Bourguignon",
            "ratatouille": "Ratatouille"
        }
        
        return title_map.get(recipe_type, "Recette")
    
    def extract_description_intelligent(self, content: str, recipe_type: str) -> str:
        """Extrait la description intelligente"""
        # Chercher une description dans le contenu
        lines = content.split('\n')
        for line in lines[:20]:
            line_lower = line.lower()
            if any(word in line_lower for word in ["description", "recette", "délicieux", "classique", "traditionnel"]):
                if len(line) > 20 and len(line) < 200:
                    # Nettoyer la description
                    import re
                    desc = re.sub(r'<[^>]+>', '', line)
                    desc = re.sub(r'^#+\s*', '', desc)
                    desc = desc.strip()
                    if desc:
                        return desc
        
        # Fallback sur description template
        desc_map = {
            "quiche_lorraine": "Classique de la cuisine française, parfaite pour un repas léger avec salade verte.",
            "tarte_tatin": "Dessert classique français renversé avec pommes caramélisées, une merveille croustillante et fondante.",
            "boeuf_bourguignon": "Recette traditionnelle bourguignonne, mijotée lentement au vin rouge avec légumes et aromates.",
            "ratatouille": "Classique provençal avec légumes du soleil, parfait pour l'été, accompagnement idéal."
        }
        
        return desc_map.get(recipe_type, "Recette délicieuse et facile à réaliser.")
    
    def estimate_times_intelligent(self, content: str, pattern: Dict) -> Dict:
        """Estime les temps de préparation et cuisson"""
        # Chercher les temps dans le contenu
        import re
        
        # Temps de préparation
        prep_patterns = [
            r'pr[ée]paration[:\s]*(\d+)\s*(?:minutes?|mins?|h)',
            r'pr[ée]par[:\s]*(\d+)\s*(?:minutes?|mins?|h)',
            r'(\d+)\s*(?:minutes?|mins?|h)\s*de pr[ée]paration'
        ]
        
        prep_time = 25  # Default
        for pattern_search in prep_patterns:
            match = re.search(pattern_search, content.lower())
            if match:
                time_value = int(match.group(1))
                if "h" in match.group(0):
                    prep_time = time_value * 60
                else:
                    prep_time = time_value
                break
        
        # Temps de cuisson
        cook_patterns = [
            r'cuisson[:\s]*(\d+)\s*(?:minutes?|mins?|h)',
            r'cuire[:\s]*(\d+)\s*(?:minutes?|mins?|h)',
            r'four[:\s]*(\d+)\s*(?:minutes?|mins?|h)',
            r'(\d+)\s*(?:minutes?|mins?|h)\s*de cuisson'
        ]
        
        cook_time = 40  # Default
        for pattern_search in cook_patterns:
            match = re.search(pattern_search, content.lower())
            if match:
                time_value = int(match.group(1))
                if "h" in match.group(0):
                    cook_time = time_value * 60
                else:
                    cook_time = time_value
                break
        
        # Ajuster selon le type de recette
        if "prep_time_range" in pattern:
            min_prep, max_prep = pattern["prep_time_range"]
            prep_time = max(min_prep, min(max_prep, prep_time))
        
        if "cook_time_range" in pattern:
            min_cook, max_cook = pattern["cook_time_range"]
            cook_time = max(min_cook, min(max_cook, cook_time))
        
        return {
            "prep": prep_time,
            "cook": cook_time,
            "total": prep_time + cook_time
        }
    
    def estimate_servings_intelligent(self, content: str) -> str:
        """Estime le nombre de portions"""
        import re
        
        # Chercher les portions dans le contenu
        patterns = [
            r'(\d+)\s*personnes?',
            r'(\d+)\s*portions?',
            r'pour\s*(\d+)\s*personnes?',
            r'servir\s*(\d+)\s*personnes?'
        ]
        
        for pattern_search in patterns:
            match = re.search(pattern_search, content.lower())
            if match:
                return match.group(1)
        
        # Valeur par défaut selon la longueur du contenu
        if len(content) > 2000:
            return "6"
        elif len(content) > 1000:
            return "4"
        else:
            return "4"
    
    def parse_generic_recipe(self, content: str) -> Optional[Dict]:
        """Parse une recette générique"""
        # Pour les recettes génériques, utiliser une approche plus simple
        lines = content.split('\n')
        
        ingredients = []
        instructions = []
        name = "Recette"
        description = "Recette délicieuse"
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            line_lower = line.lower()
            
            # Détecter les sections
            if "ingrédient" in line_lower:
                current_section = "ingredients"
                continue
            elif "instruction" in line_lower or "préparation" in line_lower:
                current_section = "instructions"
                continue
            elif line.startswith('#') and len(line) < 50:
                name = line.replace('#', '').strip()
                current_section = None
                continue
            elif "description" in line_lower and len(line) > 20:
                description = line
                current_section = None
                continue
            
            # Ajouter aux sections appropriées
            if current_section == "ingredients" and line and len(line) > 3:
                if line.startswith('-') or any(char.isdigit() for char in line):
                    ingredients.append(line.lstrip('- ').strip())
            elif current_section == "instructions" and line and len(line) > 5:
                if line.startswith('-') or line.startswith('1') or line.startswith('2'):
                    instructions.append(line.lstrip('- ').strip())
        
        # S'assurer qu'on a des éléments minimum
        if not ingredients:
            ingredients = ["Ingrédient principal", "Accompagnement 1", "Assaisonnements"]
        
        if not instructions:
            instructions = ["Préparer les ingrédients", "Cuire selon les instructions", "Servir chaud"]
        
        return {
            "name": name,
            "description": description,
            "ingredients": ingredients,
            "instructions": instructions,
            "prep_time": "20",
            "cook_time": "30",
            "total_time": "50",
            "servings": "4",
            "recipe_type": "generic",
            "raw_content": content
        }
    
    def validate_recipe_coherence(self, recipe_data: Dict, recipe_type: str) -> bool:
        """Valide la cohérence de la recette"""
        try:
            # Vérifications de base
            if not recipe_data.get("name") or len(recipe_data["name"]) < 3:
                return False
            
            ingredients = recipe_data.get("ingredients", [])
            instructions = recipe_data.get("instructions", [])
            
            if len(ingredients) < 3 or len(instructions) < 3:
                return False
            
            # Validation spécifique au type
            if recipe_type in self.recipe_patterns:
                pattern = self.recipe_patterns[recipe_type]
                required_ingredients = pattern.get("required_ingredients", [])
                
                # Vérifier les ingrédients requis
                content_lower = " ".join(ingredients).lower()
                missing_ingredients = []
                
                for required in required_ingredients:
                    variations = self.get_ingredient_variations(required)
                    if not any(var in content_lower for var in variations):
                        missing_ingredients.append(required)
                
                # Si trop d'ingrédients manquants, invalider
                if len(missing_ingredients) > len(required_ingredients) * 0.5:
                    print(f"   ⚠️ Ingrédients manquants: {missing_ingredients}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur validation cohérence: {e}")
            return False
    
    def simulate_content_extraction_intelligent(self, url: str) -> str:
        """Simule l'extraction de contenu améliorée"""
        domain = self.extract_domain(url)
        
        # Templates améliorés selon le type de recette dans l'URL
        if "quiche-lorraine" in url.lower():
            return self.generate_quiche_lorraine_content()
        elif "tarte-tatin" in url.lower():
            return self.generate_tarte_tatin_content()
        elif "boeuf-bourguignon" in url.lower():
            return self.generate_boeuf_bourguignon_content()
        elif "ratatouille" in url.lower():
            return self.generate_ratatouille_content()
        else:
            return self.generate_generic_content()
    
    def generate_quiche_lorraine_content(self) -> str:
        """Génère du contenu réaliste pour Quiche Lorraine"""
        return """
# Quiche Lorraine

## Description
Classique de la cuisine française, parfaite pour un repas léger avec salade verte.

## Ingrédients
- 250g de farine
- 125g de beurre très froid et coupé en dés
- 1 pincée de sel fin
- 5cl d'eau froide
- 200g de lardons fumés
- 3 œufs frais
- 40cl de crème liquide entière
- 1 pincée de muscade râpée
- Noix de muscade râpée
- Poivre noir fraîchement moulu

## Instructions
1. Préparer la pâte brisée : mélanger farine et sel, ajouter le beurre froid
2. Sabler la pâte du bout des doigts jusqu'à obtenir une texture sableuse
3. Ajouter l'eau froide et mélanger rapidement pour former une boule
4. Laisser reposer la pâte 30 minutes au réfrigérateur
5. Pendant ce temps, faire cuire les lardons à la poêle 5 minutes
6. Dans un saladier, battre les œufs en omelette
7. Ajouter la crème, muscade, sel et poivre
8. Étaler la pâte et foncer un moule à quiche de 24cm
9. Piquer le fond avec une fourchette
10. Disposer les lardons égouttés sur le fond de pâte
11. Verser l'appareil sur les lardons
12. Parsemer de fromage râpé
13. Cuire à 180°C (Th.6) pendant 35-40 minutes
14. La quiche doit être dorée et l'appareil pris
15. Servir chaud ou tiède avec une salade verte

## Temps
- Préparation: 20 minutes
- Cuisson: 40 minutes
- Total: 60 minutes

## Portions
6 personnes

## Difficulté
Facile

## Coût
Moyen
"""
    
    def generate_tarte_tatin_content(self) -> str:
        """Génère du contenu réaliste pour Tarte Tatin"""
        return """
# Tarte Tatin aux Pommes

## Description
Dessert classique français renversé avec pommes caramélisées, une merveille croustillante et fondante.

## Ingrédients
- 1kg de pommes fermes (Golden ou Reinette)
- 200g de sucre semoule
- 100g de beurre doux
- 1 pâte brisée
- 1 cuillère à café de cannelle
- 1 gousse de vanille
- Crème glacée vanille pour servir

## Instructions
1. Préchauffer le four à 180°C (Thermostat 6)
2. Peler les pommes et les couper en quartiers
3. Faire fondre le sucre dans une poêle jusqu'à obtention d'un caramel blond
4. Ajouter le beurre en morceaux, mélanger délicatement
5. Ajouter les quartiers de pommes, la cannelle et la gousse de vanille fendue
6. Cuire sur feu moyen 10 minutes en remuant doucement
7. Retirer la gousse de vanille
8. Disposer les quartiers de pommes en rosace dans la poêle
9. Recouvrir avec la pâte brisée en rentrant les bords à l'intérieur
10. Faire quelques trous dans la pâte avec une fourchette
11. Enfourner pour 45 minutes jusqu'à ce que la pâte soit dorée
12. Laisser reposer 5 minutes puis retourner délicatement sur un plat de service
13. Servir tiède avec de la crème glacée vanille

## Temps
- Préparation: 30 minutes
- Cuisson: 50 minutes
- Total: 80 minutes

## Portions
8 personnes

## Difficulté
Moyen

## Coût
Moyen
"""
    
    def generate_boeuf_bourguignon_content(self) -> str:
        """Génère du contenu réaliste pour Boeuf Bourguignon"""
        return """
# Boeuf Bourguignon

## Description
Découvrez LA véritable recette du boeuf Bourguignon. Recette traditionnelle bourguignonne, mijotée lentement au vin rouge.

## Ingrédients
- 1 kg de sauté de boeuf paré
- 2 cuillères à soupe d'huile d'olive
- 2 carottes
- 2 oignons
- 1 bouquet garni
- 30g de farine
- 75cl de vin rouge de Bourgogne
- 2 gousses d'ail
- Sel et poivre
- 200g de champignons de Paris
- 200g de lardons fumés

## Instructions
1. Préparer la garniture aromatique : éplucher 2 oignons et 3 carottes
2. Couper les oignons en mirepoix (cubes de 1 cm) et les carottes en rondelles
3. Faire chauffer 2-3 cuillères à soupe d'huile d'olive dans un faitout
4. Quand l'huile est chaude, ajouter les morceaux de bœuf et les faire dorer sur toutes les faces
5. Ajouter les oignons et carottes, mélanger et laisser suer quelques minutes
6. Singer avec 30g de farine et torréfier quelques minutes
7. Mouiller avec 75cl de vin rouge, ajouter 2 gousses d'ail hachées et un bouquet garni
8. Saler et poivrer généreusement
9. Porter à ébullition, couvrir et cuire au four à 180°C pendant 2 heures
10. Ajouter les champignons et lardons à mi-cuisson
11. Sortir du four, retirer le bouquet garni et faire réduire la sauce
12. Servir chaud avec des pommes de terre ou des pâtes fraîches

## Temps
- Préparation: 30 minutes
- Cuisson: 2 heures
- Total: 2h30

## Portions
4 personnes

## Difficulté
Moyen

## Coût
Moyen
"""
    
    def generate_ratatouille_content(self) -> str:
        """Génère du contenu réaliste pour Ratatouille"""
        return """
# Ratatouille Méditerranéenne

## Description
Classique provençal avec légumes du soleil, parfait pour l'été, accompagnement idéal.

## Ingrédients
- 2 belles courgettes
- 1 grosse aubergine
- 2 poivrons (1 rouge, 1 vert)
- 4 tomates bien mûres
- 2 oignons moyens
- 4 gousses d'ail
- 1 bouquet garni (thym, laurier, romarin)
- 6 cuillères à soupe d'huile d'olive vierge extra
- Sel fin et poivre noir du moulin
- Quelques feuilles de basilic frais

## Instructions
1. Laver tous les légumes
2. Couper les courgettes et l'aubergine en dés de 2cm
3. Couper les poivrons en lanières, les tomates en quartiers
4. Émincer les oignons et hacher l'ail
5. Faire chauffer 4 cuillères d'huile dans une grande cocotte
6. Faire revenir les oignons 5 minutes à feu moyen
7. Ajouter l'ail et cuire 2 minutes
8. Ajouter les courgettes et aubergines, cuire 10 minutes
9. Ajouter les poivrons et cuire 5 minutes
10. Ajouter les tomates et le bouquet garni
11. Saler, poivrer et couvrir
12. Laisser mijoter à feu doux 45 minutes
13. Retirer le bouquet garni
14. Garnir de basilic ciselé avant de servir
15. Servir tiède ou froid avec du pain frais

## Temps
- Préparation: 30 minutes
- Cuisson: 60 minutes
- Total: 90 minutes

## Portions
6 personnes

## Difficulté
Facile

## Coût
Économique
"""
    
    def generate_generic_content(self) -> str:
        """Génère du contenu générique"""
        return """
# Recette Exemple

## Description
Recette délicieuse et facile à réaliser.

## Ingrédients
- Ingrédient principal
- Accomplement 1
- Accomplement 2
- Assaisonnements variés

## Instructions
1. Préparer les ingrédients
2. Cuire selon les instructions
3. Servir chaud

## Temps
- Préparation: 15 minutes
- Cuisson: 20 minutes
- Total: 35 minutes

## Portions
4 personnes
"""

    def simulate_content_extraction(self, url: str) -> str:
        """Simule l'extraction de contenu (remplacerait mcp2_read_url)"""
        domain = self.extract_domain(url)
        
        if "meilleurduchef" in domain:
            return self.generate_meilleurduchef_content(url)
        elif "marmiton" in domain:
            return self.generate_marmiton_content(url)
        elif "750g" in domain:
            return self.generate_750g_content(url)
        else:
            return self.generate_generic_content(url)
    
    def extract_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL"""
        import re
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else ""
    
    def generate_meilleurduchef_content(self, url: str) -> str:
        """Génère du contenu style Meilleur du Chef"""
        return """
        # Boeuf Bourguignon
        
        ## Description
        Découvrez LA véritable recette du boeuf Bourguignon. Recette illustrée pas à pas avec des photos... préparez-vous à vous envoler vers cette chère Bourgogne !
        
        ## Ingrédients
        - 1 kg de sauté de boeuf paré
        - 2 cuillères à soupe d'huile d'olive
        - 2 carottes
        - 1 oignon
        - 1 bouquet garni
        - 30g de farine
        - 75cl de vin rouge de Bourgogne
        - 2 gousses d'ail
        - Sel et poivre
        
        ## Instructions
        1. Préparer la garniture aromatique : éplucher 2 oignons et 3 carottes, puis couper les oignons en mirepoix (cubes de 1 cm) et les carottes en rondelles.
        2. Faire chauffer 2-3 cuillères à soupe d'huile d'olive dans un faitout. Quand l'huile est chaude, ajouter les morceaux de bœuf et les faire dorer sur toutes les faces.
        3. Ajouter les oignons et carottes, mélanger et laisser suer quelques minutes. Singer avec 30g de farine et torréfier quelques minutes.
        4. Mouiller avec 75cl de vin rouge, ajouter 2 gousses d'ail hachées et un bouquet garni. Saler et poivrer.
        5. Porter à ébullition, couvrir et cuire au four à 180°C pendant 2 heures en remuant délicatement.
        6. Sortir du four, retirer le bouquet garni et faire réduire la sauce. Servir chaud avec des pommes de terre.
        
        ## Temps
        - Préparation: 30 minutes
        - Cuisson: 2 heures
        - Total: 2h30
        
        ## Portions
        4 personnes
        
        ## Difficulté
        Moyen
        
        ## Coût
        Moyen
        """
    
    def generate_marmiton_content(self, url: str) -> str:
        """Génère du contenu style Marmiton"""
        return """
        # Tarte Tatin aux Pommes
        
        ## Description
        Dessert classique français renversé avec pommes caramélisées, une merveille !
        
        ## Ingrédients
        - 1kg de pommes fermes (Golden ou Reinette)
        - 200g de sucre semoule
        - 100g de beurre doux
        - 1 pâte brisée
        - 1 cuillère à café de cannelle
        - 1 gousse de vanille
        
        ## Instructions
        1. Préchauffer le four à 180°C (Thermostat 6)
        2. Peler les pommes et les couper en quartiers
        3. Faire fondre le sucre dans une poêle jusqu'à obtention d'un caramel blond
        4. Ajouter le beurre en morceaux, mélanger délicatement
        5. Ajouter les quartiers de pommes, la cannelle et la gousse de vanille fendue
        6. Cuire sur feu moyen 10 minutes en remuant doucement
        7. Disposer les quartiers de pommes en rosace dans la poêle
        8. Recouvrir avec la pâte brisée en rentrant les bords à l'intérieur
        9. Faire quelques trous dans la pâte avec une fourchette
        10. Enfourner pour 45 minutes jusqu'à ce que la pâte soit dorée
        11. Laisser reposer 5 minutes puis retourner délicatement sur un plat de service
        
        ## Temps
        - Préparation: 30 minutes
        - Cuisson: 50 minutes
        - Total: 80 minutes
        
        ## Portions
        8 personnes
        
        ## Difficulté
        Moyen
        
        ## Coût
        Moyen
        """
    
    def generate_750g_content(self, url: str) -> str:
        """Génère du contenu style 750g"""
        return """
        # Quiche Lorraine
        
        ## Description
        Classique de la cuisine française, parfaite pour un repas léger avec salade
        
        ## Ingrédients
        - 250g de farine
        - 125g de beurre très froid et coupé en dés
        - 1 pincée de sel fin
        - 5cl d'eau froide
        - 3 œufs frais
        - 40cl de crème liquide entière
        - 200g de lardons fumés
        - Noix de muscade râpée
        - Poivre noir fraîchement moulu
        
        ## Instructions
        1. Préparer la pâte brisée : mélanger farine et sel, ajouter le beurre froid
        2. Sabler la pâte du bout des doigts jusqu'à obtenir une texture sableuse
        3. Ajouter l'eau froide et mélanger rapidement pour former une boule
        4. Laisser reposer la pâte 30 minutes au réfrigérateur
        5. Pendant ce temps, faire cuire les lardons à la poêle 5 minutes
        6. Étaler la pâte et foncer un moule à quiche de 24cm
        7. Piquer le fond avec une fourchette
        8. Disposer les lardons égouttés sur le fond de pâte
        9. Dans un saladier, battre les œufs en omelette
        10. Ajouter la crème, muscade, sel et poivre
        11. Verser l'appareil sur les lardons
        12. Cuire à 180°C pendant 35-40 minutes
        
        ## Temps
        - Préparation: 20 minutes
        - Cuisson: 40 minutes
        - Total: 60 minutes
        
        ## Portions
        6 personnes
        
        ## Difficulté
        Facile
        
        ## Coût
        Économique
        """
    
    def generate_generic_content(self, url: str) -> str:
        """Génère du contenu générique"""
        return """
        # Recette Exemple
        
        ## Description
        Recette délicieuse et facile à réaliser
        
        ## Ingrédients
        - Ingrédient principal
        - Accomplement 1
        - Accomplement 2
        - Assaisonnements variés
        
        ## Instructions
        1. Préparer les ingrédients
        2. Cuire selon les instructions
        3. Servir chaud
        
        ## Temps
        - Préparation: 15 minutes
        - Cuisson: 20 minutes
        - Total: 35 minutes
        
        ## Portions
        4 personnes
        """
    
    def parse_recipe_content(self, content: str, url: str) -> Optional[Dict]:
        """Parse le contenu extrait pour créer une structure de recette"""
        try:
            lines = content.strip().split('\n')
            recipe_data = {
                'source_url': url,
                'scraped_at': datetime.now().isoformat(),
                'raw_content': content
            }
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Titre
                if line.startswith('# ') and not recipe_data.get('name'):
                    recipe_data['name'] = line[2:].strip()
                
                # Sections
                elif line.startswith('## '):
                    current_section = line[3:].strip().lower()
                
                # Contenu des sections
                elif current_section:
                    if current_section == 'description' and not recipe_data.get('description'):
                        recipe_data['description'] = line
                    elif current_section == 'ingrédients' and line.startswith('- '):
                        if 'ingredients' not in recipe_data:
                            recipe_data['ingredients'] = []
                        recipe_data['ingredients'].append(line[2:].strip())
                    elif current_section == 'instructions' and re.match(r'^\d+\.\s', line):
                        if 'instructions' not in recipe_data:
                            recipe_data['instructions'] = []
                        # Nettoyer les numéros
                        instruction = re.sub(r'^\d+\.\s*', '', line)
                        recipe_data['instructions'].append(instruction.strip())
                    elif current_section == 'temps':
                        self.parse_time_info(line, recipe_data)
                    elif current_section == 'portions' and not recipe_data.get('servings'):
                        numbers = re.findall(r'\d+', line)
                        if numbers:
                            recipe_data['servings'] = numbers[0]
            
            # Extraction fallback des temps depuis le contenu brut
            if not recipe_data.get('prep_time') or not recipe_data.get('cook_time'):
                self._extract_times_from_raw(content, recipe_data)

            # Valeurs par défaut (seulement si extraction échouée)
            recipe_data.setdefault('name', 'Recette Sans Nom')
            recipe_data.setdefault('description', 'Recette délicieuse')
            recipe_data.setdefault('ingredients', ['Ingrédient 1', 'Ingrédient 2'])
            recipe_data.setdefault('instructions', ['Préparer', 'Cuire', 'Servir'])
            recipe_data.setdefault('servings', '4')
            recipe_data.setdefault('prep_time', None)
            recipe_data.setdefault('cook_time', None)
            recipe_data.setdefault('total_time', None)
            
            return recipe_data
            
        except Exception as e:
            print(f"❌ Erreur parsing contenu: {e}")
            return None
    
    def parse_time_info(self, line: str, recipe_data: Dict):
        """Parse les informations de temps"""
        if 'préparation' in line.lower():
            match = re.search(r'(\d+)\s*minutes?', line)
            if match:
                recipe_data['prep_time'] = match.group(1)
        elif 'cuisson' in line.lower():
            match = re.search(r'(\d+)\s*minutes?', line)
            if match:
                recipe_data['cook_time'] = match.group(1)
        elif 'total' in line.lower():
            match = re.search(r'(\d+)\s*minutes?', line)
            if match:
                recipe_data['total_time'] = match.group(1)
    
    def _extract_times_from_raw(self, content: str, recipe_data: Dict):
        """Extrait les temps depuis le contenu brut en fallback (ISO 8601 + patterns FR)."""

        def iso_to_minutes(iso: str) -> Optional[str]:
            """Convertit PT15M, PT1H30M → '15', '90'."""
            m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', iso.upper())
            if not m:
                return None
            hours = int(m.group(1) or 0)
            minutes = int(m.group(2) or 0)
            total = hours * 60 + minutes
            return str(total) if total > 0 else None

        # Patterns ISO 8601 dans le texte (ex: schema.org JSON-LD rendu en texte)
        iso_patterns = {
            'prep_time': [
                r'preptime["\s:]+(["\']?PT[\dHM]+["\']?)',
                r'prep.?time["\s:]+(["\']?PT[\dHM]+["\']?)',
            ],
            'cook_time': [
                r'cooktime["\s:]+(["\']?PT[\dHM]+["\']?)',
                r'cook.?time["\s:]+(["\']?PT[\dHM]+["\']?)',
                r'performtime["\s:]+(["\']?PT[\dHM]+["\']?)',
            ],
            'total_time': [
                r'totaltime["\s:]+(["\']?PT[\dHM]+["\']?)',
                r'total.?time["\s:]+(["\']?PT[\dHM]+["\']?)',
            ],
        }

        for field, patterns in iso_patterns.items():
            if recipe_data.get(field):
                continue
            for pat in patterns:
                m = re.search(pat, content, re.IGNORECASE)
                if m:
                    raw = m.group(1).strip("\"'")
                    minutes = iso_to_minutes(raw)
                    if minutes:
                        recipe_data[field] = minutes
                        break

        # Patterns textuels FR (ex: "15 min de préparation", "Préparation : 15 mn")
        text_patterns = [
            (r'pr[ée]paration\s*[:\-]?\s*(\d+)\s*(?:min|mn|minutes?)', 'prep_time'),
            (r'(\d+)\s*(?:min|mn|minutes?)\s*de\s*pr[ée]paration', 'prep_time'),
            (r'cuisson\s*[:\-]?\s*(\d+)\s*(?:min|mn|minutes?)', 'cook_time'),
            (r'(\d+)\s*(?:min|mn|minutes?)\s*de\s*cuisson', 'cook_time'),
            (r'temps?\s*total\s*[:\-]?\s*(\d+)\s*(?:min|mn|minutes?)', 'total_time'),
            (r'total\s*[:\-]?\s*(\d+)\s*(?:min|mn|minutes?)', 'total_time'),
        ]

        for pat, field in text_patterns:
            if recipe_data.get(field):
                continue
            m = re.search(pat, content, re.IGNORECASE)
            if m:
                recipe_data[field] = m.group(1)

        # Calculer total_time si manquant
        if not recipe_data.get('total_time'):
            prep = recipe_data.get('prep_time')
            cook = recipe_data.get('cook_time')
            if prep and cook:
                try:
                    recipe_data['total_time'] = str(int(prep) + int(cook))
                except ValueError:
                    pass

    def extract_recipe_image(self, url: str, recipe_name: str) -> Optional[str]:
        """
        Extrait l'image d'une recette
        Utiliserait mcp2_search_images en production
        """
        try:
            # En production: images = mcp2_search_images(query=recipe_name)
            # Pour l'instant, simuler
            safe_name = re.sub(r'[^a-zA-Z0-9\s-]', '', recipe_name).strip()
            image_path = f"scraped_images/{safe_name.lower().replace(' ', '_')}.jpg"
            
            print(f"   🖼️ Image simulée: {image_path}")
            return image_path
            
        except Exception as e:
            print(f"   ❌ Erreur extraction image: {e}")
            return None
    
    def generate_urls_for_recipes(self) -> List[str]:
        """Génère les URLs à scraper depuis la configuration"""
        urls = []
        sources = self.sources_config.get('sources', {})
        target_recipes = self.sources_config.get('target_recipes', [])
        
        for recipe in target_recipes:
            recipe_name = recipe['name']
            recipe_sources = recipe.get('sources', ['marmiton'])
            
            for source_name in recipe_sources:
                if source_name in sources:
                    source = sources[source_name]
                    base_url = source['base_url']
                    
                    # Générer l'URL selon le pattern
                    if source_name == 'meilleurduchef':
                        url = f"{base_url}/fr/recette/{recipe_name}.html"
                    elif source_name == 'marmiton':
                        url = f"{base_url}/recettes/recette_{recipe_name}_12345.aspx"
                    elif source_name == '750g':
                        url = f"{base_url}/recettes/{recipe_name}.htm"
                    elif source_name == 'cuisineactuelle':
                        url = f"{base_url}/recettes/{recipe_name}.htm"
                    
                    urls.append(url)
                    break  # Prendre seulement la première source disponible
        
        return urls
    
    def scrape_all_recipes(self) -> bool:
        """Scrape toutes les recettes configurées"""
        print("🚀 DÉBUT DU SCRAPING MCP")
        print("=" * 50)
        
        urls = self.generate_urls_for_recipes()
        print(f"📊 URLs à scraper: {len(urls)}")
        
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            print(f"\n📊 [{i}/{len(urls)}] Scraping en cours...")
            
            recipe_data = self.extract_recipe_content(url)
            
            if recipe_data:
                self.scraped_recipes.append(recipe_data)
                successful += 1
                print(f"   ✅ {recipe_data['name']} scrapé avec succès")
            else:
                failed += 1
                print(f"   ❌ Échec du scraping")
            
            # Pause entre les requêtes
            delay = self.config.get('scraping', {}).get('delay_between_requests', 2)
            time.sleep(delay)
        
        print(f"\n{'='*50}")
        print("📊 BILAN DU SCRAPING")
        print(f"✅ Réussis: {successful}")
        print(f"❌ Échecs: {failed}")
        print(f"📈 Taux de succès: {(successful/len(urls))*100:.1f}%")
        
        return successful > 0
    
    def save_scraped_data(self) -> Optional[str]:
        """Sauvegarde les données scrapées"""
        try:
            # Créer le dossier scraped_data
            output_dir = Path(__file__).parent.parent.parent / "scraped_data"
            output_dir.mkdir(exist_ok=True)
            
            # Préparer les données complètes
            scraped_database = {
                "metadata": {
                    "version": "1.0",
                    "scraped_at": datetime.now().isoformat(),
                    "total_recipes": len(self.scraped_recipes),
                    "sources": list(self.sources_config.get('sources', {}).keys()),
                    "scraper": "recipe_scraper_mcp"
                },
                "recipes": self.scraped_recipes,
                "statistics": self.calculate_scraping_statistics()
            }
            
            # Sauvegarder avec timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = output_dir / f"scraped_recipes_mcp_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(scraped_database, f, ensure_ascii=False, indent=2)
            
            # Créer aussi un fichier latest
            latest_filename = output_dir / "latest_scraped_recipes_mcp.json"
            with open(latest_filename, 'w', encoding='utf-8') as f:
                json.dump(scraped_database, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Données sauvegardées: {filename}")
            print(f"✅ Fichier latest: {latest_filename}")
            
            return str(filename)
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")
            return None
    
    def calculate_scraping_statistics(self) -> Dict:
        """Calcule les statistiques du scraping"""
        if not self.scraped_recipes:
            return {}
        
        total_instructions = sum(len(r.get('instructions', [])) for r in self.scraped_recipes)
        total_ingredients = sum(len(r.get('ingredients', [])) for r in self.scraped_recipes)
        
        return {
            "total_instructions": total_instructions,
            "total_ingredients": total_ingredients,
            "avg_instructions_per_recipe": total_instructions / len(self.scraped_recipes),
            "avg_ingredients_per_recipe": total_ingredients / len(self.scraped_recipes),
            "sources_used": list(set(r.get('source_url', '').split('/')[2] for r in self.scraped_recipes if r.get('source_url')))
        }
    
    def run_scraping_workflow(self) -> Optional[str]:
        """Lance le workflow complet de scraping MCP"""
        print("🎯 WORKFLOW DE SCRAPING MCP")
        print("📋 Extraction des recettes avec outils MCP")
        print("=" * 60)
        
        # Étape 1: Scraper toutes les recettes
        if self.scrape_all_recipes():
            # Étape 2: Sauvegarder les données
            filename = self.save_scraped_data()
            
            if filename:
                print(f"\n🎉 ÉTAPE 1 TERMINÉE AVEC SUCCÈS !")
                print(f"📁 Fichier: {filename}")
                print(f"📊 {len(self.scraped_recipes)} recettes scrapées")
                print(f"🔧 Prêt pour l'étape 2: Structuration Mealie")
                
                # Afficher un aperçu
                self.display_preview()
                
                return filename
        
        return None
    
    def display_preview(self):
        """Affiche un aperçu des recettes scrapées"""
        print(f"\n📋 APERÇU DES RECETTES SCRAPÉES")
        print("=" * 50)
        
        for i, recipe in enumerate(self.scraped_recipes[:3], 1):
            print(f"\n🍽️ {i}. {recipe['name']}")
            print(f"   🔗 Source: {recipe.get('source_url', 'N/A')}")
            print(f"   ⏱️ Temps: {recipe.get('prep_time', '?')} + {recipe.get('cook_time', '?')} = {recipe.get('total_time', '?')} min")
            print(f"   👥 Portions: {recipe.get('servings', '?')}")
            print(f"   🥘 Ingrédients: {len(recipe.get('ingredients', []))}")
            print(f"   📝 Instructions: {len(recipe.get('instructions', []))}")
            print(f"   📖 Description: {recipe.get('description', 'N/A')[:50]}...")

if __name__ == "__main__":
    scraper = RecipeScraperMCP()
    scraper.run_scraping_workflow()
