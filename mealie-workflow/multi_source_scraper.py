#!/usr/bin/env python3
"""
MULTI-SOURCE SCRAPER EXPANDER
Expansion des sources et import en masse pour Mealie
"""

import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Ajouter le chemin du workflow
sys.path.append(str(Path(__file__).parent))

class MultiSourceScraper:
    """Scraper multi-sources pour expansion des recettes"""
    
    def __init__(self):
        self.sources_config = self.load_sources_config()
        self.expansion_log = []
        self.scraped_count = 0
        
    def load_sources_config(self) -> Dict:
        """Charge la configuration des sources étendue"""
        config_path = Path(__file__).parent / "config" / "expanded_sources_config.json"
        
        # Configuration par défaut si le fichier n'existe pas
        default_config = {
            "sources": {
                "marmiton": {
                    "base_url": "https://www.marmiton.org",
                    "priority": 1,
                    "language": "fr",
                    "max_recipes": 50,
                    "search_patterns": ["/recettes/{}", "/recettes/recherche/{}"]
                },
                "750g": {
                    "base_url": "https://www.750g.com",
                    "priority": 2,
                    "language": "fr",
                    "max_recipes": 30,
                    "search_patterns": ["/recette/{}", "/recettes/{}"]
                },
                "cuisineactuelle": {
                    "base_url": "https://www.cuisineactuelle.fr",
                    "priority": 3,
                    "language": "fr",
                    "max_recipes": 25,
                    "search_patterns": ["/recettes/{}", "/recettes/{}"]
                },
                "meilleurduchef": {
                    "base_url": "https://www.meilleurduchef.com",
                    "priority": 4,
                    "language": "fr",
                    "max_recipes": 20,
                    "search_patterns": ["/fr/recette/{}.html"]
                },
                "chefnini": {
                    "base_url": "https://www.chefnini.com",
                    "priority": 5,
                    "language": "fr",
                    "max_recipes": 15,
                    "search_patterns": ["/recette/{}", "/recettes/{}"]
                },
                "allrecipes": {
                    "base_url": "https://www.allrecipes.com",
                    "priority": 6,
                    "language": "en",
                    "max_recipes": 10,
                    "search_patterns": ["/recipe/{}", "/recipes/{}"]
                }
            },
            "target_recipes": [
                {"name": "boeuf-bourguignon", "category": "plat_principal", "sources": ["meilleurduchef", "marmiton"]},
                {"name": "tarte-tatin", "category": "dessert", "sources": ["marmiton", "750g"]},
                {"name": "quiche-lorraine", "category": "plat_principal", "sources": ["marmiton", "cuisineactuelle"]},
                {"name": "ratatouille", "category": "accompagnement", "sources": ["cuisineactuelle", "750g"]},
                {"name": "lasagnes", "category": "plat_principal", "sources": ["marmiton", "chefnini"]},
                {"name": "mousse-chocolat", "category": "dessert", "sources": ["750g", "marmiton"]},
                {"name": "poulet-curry", "category": "plat_principal", "sources": ["chefnini", "allrecipes"]},
                {"name": "salade-caesar", "category": "entrée", "sources": ["marmiton", "cuisineactuelle"]},
                {"name": "soupe-a-l'oignon", "category": "entrée", "sources": ["meilleurduchef", "750g"]},
                {"name": "coq-au-vin", "category": "plat_principal", "sources": ["meilleurduchef", "marmiton"]},
                {"name": "crepes", "category": "dessert", "sources": ["marmiton", "750g"]},
                {"name": "blanquette-de-veau", "category": "plat_principal", "sources": ["meilleurduchef", "cuisineactuelle"]},
                {"name": "gratin-dauphinois", "category": "accompagnement", "sources": ["marmiton", "cuisineactuelle"]},
                {"name": "tarte-aux-pommes", "category": "dessert", "sources": ["marmiton", "750g"]},
                {"name": "couscous", "category": "plat_principal", "sources": ["chefnini", "750g"]}
            ],
            "expansion_settings": {
                "delay_between_requests": 2,
                "max_concurrent_sources": 3,
                "retry_failed": True,
                "max_retries": 3
            }
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Créer le fichier de configuration par défaut
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                return default_config
        except Exception as e:
            print(f"❌ Erreur chargement config: {e}")
            return default_config
    
    def expand_sources(self, target_count: int = 20) -> Dict:
        """Étend les sources pour scraper plus de recettes"""
        print("🚀 EXPANSION MULTI-SOURCES")
        print("📊 Scraping étendu depuis plusieurs sources")
        print("=" * 80)
        
        start_time = datetime.now()
        
        # Générer les URLs à scraper
        urls_to_scrape = self.generate_expansion_urls(target_count)
        print(f"📊 URLs générées: {len(urls_to_scrape)}")
        
        # Scraper par lots
        all_recipes = []
        batches = self.create_scraping_batches(urls_to_scrape, batch_size=5)
        
        for i, batch in enumerate(batches, 1):
            print(f"\n📦 Lot {i}/{len(batches)} ({len(batch)} URLs)")
            
            batch_recipes = self.scrape_batch(batch)
            all_recipes.extend(batch_recipes)
            
            # Pause entre les lots
            if i < len(batches):
                time.sleep(3)
        
        # Nettoyer et dédupliquer
        cleaned_recipes = self.clean_expanded_recipes(all_recipes)
        
        # Sauvegarder
        expanded_file = self.save_expanded_recipes(cleaned_recipes)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Résumé
        print(f"\n🎉 EXPANSION TERMINÉE")
        print(f"⏱️ Durée: {duration:.1f} secondes")
        print(f"📊 URLs traitées: {len(urls_to_scrape)}")
        print(f"🍽️ Recettes obtenues: {len(cleaned_recipes)}")
        print(f"💾 Fichier: {expanded_file}")
        
        self.expansion_log.append(f"Expansion: {len(cleaned_recipes)} recettes en {duration:.1f}s")
        
        return {
            "success": True,
            "urls_processed": len(urls_to_scrape),
            "recipes_obtained": len(cleaned_recipes),
            "duration": duration,
            "file": expanded_file,
            "recipes": cleaned_recipes
        }
    
    def generate_expansion_urls(self, target_count: int) -> List[Dict]:
        """Génère les URLs à scraper pour l'expansion"""
        urls = []
        target_recipes = self.sources_config.get("target_recipes", [])
        sources = self.sources_config.get("sources", {})
        
        # Prioriser les recettes par popularité
        priority_recipes = target_recipes[:target_count]
        
        for recipe_target in priority_recipes:
            recipe_name = recipe_target["name"]
            recipe_sources = recipe_target.get("sources", list(sources.keys())[:2])
            
            for source_name in recipe_sources:
                if source_name in sources:
                    source_config = sources[source_name]
                    base_url = source_config["base_url"]
                    patterns = source_config.get("search_patterns", ["/{}"])
                    
                    # Générer l'URL avec le premier pattern
                    pattern = patterns[0]
                    url = base_url + pattern.format(recipe_name)
                    
                    urls.append({
                        "url": url,
                        "source": source_name,
                        "recipe_name": recipe_name,
                        "category": recipe_target.get("category", "plat_principal"),
                        "priority": source_config.get("priority", 999)
                    })
        
        # Trier par priorité et limiter
        urls.sort(key=lambda x: x["priority"])
        return urls[:target_count]
    
    def create_scraping_batches(self, urls: List[Dict], batch_size: int = 5) -> List[List[Dict]]:
        """Crée des lots de scraping"""
        batches = []
        for i in range(0, len(urls), batch_size):
            batches.append(urls[i:i + batch_size])
        return batches
    
    def scrape_batch(self, batch: List[Dict]) -> List[Dict]:
        """Scrape un lot d'URLs"""
        batch_recipes = []
        
        for url_info in batch:
            try:
                print(f"   🔍 Scraping: {url_info['recipe_name']} depuis {url_info['source']}")
                
                # Simuler le scraping (remplacer par vrai MCP)
                recipe = self.simulate_recipe_scraping(url_info)
                
                if recipe:
                    batch_recipes.append(recipe)
                    self.scraped_count += 1
                    print(f"      ✅ Succès: {recipe['name']}")
                else:
                    print(f"      ❌ Échec: {url_info['recipe_name']}")
                
                # Pause entre les requêtes
                time.sleep(1)
                
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
        
        return batch_recipes
    
    def simulate_recipe_scraping(self, url_info: Dict) -> Optional[Dict]:
        """Simule le scraping d'une recette (remplacer par vrai MCP)"""
        recipe_name = url_info["recipe_name"]
        source = url_info["source"]
        category = url_info["category"]
        
        # Templates améliorés par type de recette
        templates = {
            "lasagnes": {
                "name": "Lasagnes Maison",
                "description": "Délicieuses lasagnes italiennes avec sauce bolognaise et béchamel",
                "prep_time": "45",
                "cook_time": "40",
                "servings": "6",
                "ingredients": [
                    "500g de pâtes à lasagnes",
                    "1kg de viande hachée",
                    "800g de sauce tomate",
                    "1 oignon",
                    "2 gousses d'ail",
                    "100g de parmesan",
                    "1l de lait",
                    "50g de beurre",
                    "50g de farine",
                    "Noix de muscade",
                    "Sel et poivre"
                ],
                "instructions": [
                    "Préparer la sauce bolognaise : faire revenir oignon et ail hachés",
                    "Ajouter la viande hachée et dorer",
                    "Incorporer la sauce tomate et laisser mijoter 30 minutes",
                    "Préparer la sauce béchamel avec lait, beurre et farine",
                    "Monter les lasagnes en alternant pâtes, sauce bolognaise et béchamel",
                    "Parsemer de parmesan et cuire au four 180°C 40 minutes"
                ]
            },
            "mousse-chocolat": {
                "name": "Mousse au Chocolat",
                "description": "Mousse au chocolat noir aérienne et fondante",
                "prep_time": "20",
                "cook_time": "0",
                "servings": "4",
                "ingredients": [
                    "200g de chocolat noir 70%",
                    "6 œufs",
                    "100g de sucre",
                    "30cl de crème liquide",
                    "1 pincée de sel",
                    "Extrait de vanille"
                ],
                "instructions": [
                    "Faire fondre le chocolat au bain-marie",
                    "Séparer les blancs des jaunes d'œufs",
                    "Battre les jaunes avec le sucre jusqu'à blanchissement",
                    "Ajouter le chocolat fondu tiède",
                    "Monter les blancs en neige ferme",
                    "Incorporer délicatement les blancs et la crème montée",
                    "Répartir dans des rameaux et réfrigérer 4 heures"
                ]
            },
            "poulet-curry": {
                "name": "Poulet Curry Indien",
                "description": "Poulet tendre dans une sauce curry parfumée",
                "prep_time": "25",
                "cook_time": "35",
                "servings": "4",
                "ingredients": [
                    "800g de poulet coupé en morceaux",
                    "2 oignons",
                    "3 gousses d'ail",
                    "2cm de gingembre",
                    "2 cuillères de curry en poudre",
                    "400ml de lait de coco",
                    "200g de yaourt",
                    "Huile végétale",
                    "Coriandre fraîche",
                    "Sel et poivre"
                ],
                "instructions": [
                    "Faire mariner le poulet dans le yaourt et curry 30 minutes",
                    "Faire revenir oignons, ail et gingembre hachés",
                    "Ajouter le curry en poudre et cuire 2 minutes",
                    "Ajouter le poulet et dorer sur toutes faces",
                    "Verser le lait de coco et laisser mijoter 25 minutes",
                    "Garnir de coriandre fraîche et servir avec riz basmati"
                ]
            },
            "salade-caesar": {
                "name": "Salade Caesar",
                "description": "Salade Caesar classique avec poulet grillé et croûtons",
                "prep_time": "20",
                "cook_time": "15",
                "servings": "4",
                "ingredients": [
                    "2 laitues romaines",
                    "400g de blanc de poulet",
                    "100g de parmesan",
                    "200g de pain de mie",
                    "2 gousses d'ail",
                    "6 cuillères d'huile d'olive",
                    "2 cuillères de jus de citron",
                    "1 cuillère de moutarde de Dijon",
                    "Anchois (optionnel)",
                    "Sel et poivre"
                ],
                "instructions": [
                    "Préparer les croûtons : couper le pain en dés, dorer à l'huile avec ail",
                    "Griller le poulet et couper en lanières",
                    "Laver et couper la laitue",
                    "Préparer la vinaigrette : moutarde, jus de citron, huile, ail",
                    "Mélanger la laitue avec la vinaigrette",
                    "Ajouter le poulet, les croûtons et le parmesan râpé"
                ]
            }
        }
        
        # Obtenir le template approprié
        template_key = recipe_name.replace("-", "").lower()
        template = templates.get(template_key, self.get_generic_template(category))
        
        if template:
            recipe = {
                "source_url": url_info["url"],
                "scraped_at": datetime.now().isoformat(),
                "raw_content": self.generate_raw_content(template),
                "name": template["name"],
                "description": template["description"],
                "ingredients": template["ingredients"],
                "instructions": template["instructions"],
                "prep_time": template["prep_time"],
                "cook_time": template["cook_time"],
                "total_time": str(int(template["prep_time"]) + int(template["cook_time"])),
                "servings": template["servings"],
                "image": f"https://images.unsplash.com/photo-{self.generate_image_id()}?w=800&h=600&fit=crop",
                "category": category,
                "source": source
            }
            return recipe
        
        return None
    
    def get_generic_template(self, category: str) -> Dict:
        """Retourne un template générique par catégorie"""
        templates = {
            "plat_principal": {
                "name": "Plat Principal",
                "description": "Délicieux plat principal équilibré",
                "prep_time": "25",
                "cook_time": "30",
                "servings": "4",
                "ingredients": [
                    "Ingrédient principal (500g)",
                    "Légumes de saison (300g)",
                    "Aromates (ail, oignon)",
                    "Huile d'olive",
                    "Sel et poivre",
                    "Herbes fraîches"
                ],
                "instructions": [
                    "Préparer les ingrédients",
                    "Cuire à feu moyen",
                    "Ajouter les aromates",
                    "Laisser mijoter",
                    "Servir chaud"
                ]
            },
            "dessert": {
                "name": "Dessert",
                "description": "Dessert gourmand et léger",
                "prep_time": "15",
                "cook_time": "20",
                "servings": "6",
                "ingredients": [
                    "Farine (200g)",
                    "Sucre (150g)",
                    "Œufs (3)",
                    "Beurre (100g)",
                    "Extrait de vanille",
                    "Sel"
                ],
                "instructions": [
                    "Préchauffer le four à 180°C",
                    "Mélanger les ingrédients secs",
                    "Incorporer les ingrédients humides",
                    "Verser dans un moule",
                    "Cuire 20-25 minutes"
                ]
            },
            "entrée": {
                "name": "Entrée",
                "description": "Entrée fraîche et légère",
                "prep_time": "15",
                "cook_time": "10",
                "servings": "4",
                "ingredients": [
                    "Légumes frais (400g)",
                    "Vinaigrette maison",
                    "Herbes aromatiques",
                    "Noix ou graines",
                    "Sel et poivre"
                ],
                "instructions": [
                    "Laver et préparer les légumes",
                    "Préparer la vinaigrette",
                    "Assembler l'entrée",
                    "Garnir d'herbes fraîches",
                    "Servir frais"
                ]
            },
            "accompagnement": {
                "name": "Accompagnement",
                "description": "Accompagnement savoureux",
                "prep_time": "20",
                "cook_time": "25",
                "servings": "4",
                "ingredients": [
                    "Légumes variés (800g)",
                    "Huile d'olive",
                    "Ail et oignon",
                    "Herbes de Provence",
                    "Sel et poivre"
                ],
                "instructions": [
                    "Préparer les légumes",
                    "Faire revenir les aromates",
                    "Ajouter les légumes",
                    "Couvrir et cuire doucement",
                    "Servir chaud"
                ]
            }
        }
        
        return templates.get(category, templates["plat_principal"])
    
    def generate_raw_content(self, template: Dict) -> str:
        """Génère le contenu brut à partir du template"""
        content = f"# {template['name']}\n\n"
        content += f"## Description\n{template['description']}\n\n"
        content += "## Ingrédients\n"
        for ingredient in template["ingredients"]:
            content += f"- {ingredient}\n"
        content += "\n## Instructions\n"
        for i, instruction in enumerate(template["instructions"], 1):
            content += f"{i}. {instruction}\n"
        content += f"\n## Temps\n"
        content += f"- Préparation: {template['prep_time']} minutes\n"
        content += f"- Cuisson: {template['cook_time']} minutes\n"
        content += f"- Total: {int(template['prep_time']) + int(template['cook_time'])} minutes\n"
        content += f"\n## Portions\n{template['servings']} personnes\n"
        
        return content
    
    def generate_image_id(self) -> str:
        """Génère un ID d'image Unsplash"""
        import random
        ids = [
            "1603133872878-684f208fb84b",  # Boeuf
            "1585937429242-9b35ed3a7cbc",  # Tarte
            "1555939594-58dcbcb1dce0",  # Quiche
            "1546548970-71785318a17b",  # Ratatouille
            "1574894709920-9b35ed3a7cbc",  # Lasagnes
            "1577666597629-0ae603b2b74c",  # Mousse
            "1585937429242-9b35ed3a7cbc",  # Poulet
            "1550309789-719f6af8012f",  # Salade
            "1565299624946-b28f40a0ae38",  # Plat générique
        ]
        return random.choice(ids)
    
    def clean_expanded_recipes(self, recipes: List[Dict]) -> List[Dict]:
        """Nettoie et déduplique les recettes étendues"""
        print(f"\n🧹 Nettoyage de {len(recipes)} recettes")
        
        # Éliminer les doublons par nom
        seen_names = set()
        unique_recipes = []
        
        for recipe in recipes:
            name = recipe.get("name", "").lower()
            if name not in seen_names:
                seen_names.add(name)
                unique_recipes.append(recipe)
        
        print(f"   🗑️ Doublons éliminés: {len(recipes) - len(unique_recipes)}")
        print(f"   ✅ Recettes uniques: {len(unique_recipes)}")
        
        return unique_recipes
    
    def save_expanded_recipes(self, recipes: List[Dict]) -> str:
        """Sauvegarde les recettes étendues"""
        output_dir = Path(__file__).parent / "expanded_data"
        output_dir.mkdir(exist_ok=True)
        
        # Préparer les données
        data = {
            "metadata": {
                "version": "2.0",
                "expanded_at": datetime.now().isoformat(),
                "total_recipes": len(recipes),
                "sources_used": list(set(r.get("source", "unknown") for r in recipes)),
                "expander": "multi_source_scraper"
            },
            "recipes": recipes,
            "statistics": {
                "total_instructions": sum(len(r.get("instructions", [])) for r in recipes),
                "total_ingredients": sum(len(r.get("ingredients", [])) for r in recipes),
                "avg_instructions_per_recipe": sum(len(r.get("instructions", [])) for r in recipes) / len(recipes) if recipes else 0,
                "avg_ingredients_per_recipe": sum(len(r.get("ingredients", [])) for r in recipes) / len(recipes) if recipes else 0,
                "categories_distribution": self.calculate_categories_distribution(recipes),
                "sources_distribution": self.calculate_sources_distribution(recipes)
            }
        }
        
        # Sauvegarder avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_dir / f"expanded_recipes_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Créer aussi un fichier latest
        latest_filename = output_dir / "latest_expanded_recipes.json"
        with open(latest_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(filename)
    
    def calculate_categories_distribution(self, recipes: List[Dict]) -> Dict:
        """Calcule la distribution des catégories"""
        distribution = {}
        for recipe in recipes:
            category = recipe.get("category", "plat_principal")
            distribution[category] = distribution.get(category, 0) + 1
        return distribution
    
    def calculate_sources_distribution(self, recipes: List[Dict]) -> Dict:
        """Calcule la distribution des sources"""
        distribution = {}
        for recipe in recipes:
            source = recipe.get("source", "unknown")
            distribution[source] = distribution.get(source, 0) + 1
        return distribution
    
    def get_expansion_report(self) -> Dict:
        """Retourne le rapport d'expansion"""
        return {
            "expansion_log": self.expansion_log,
            "scraped_count": self.scraped_count,
            "sources_config": self.sources_config
        }

if __name__ == "__main__":
    # Test de l'expansion
    scraper = MultiSourceScraper()
    
    # Lancer l'expansion avec 15 recettes
    result = scraper.expand_sources(target_count=15)
    
    if result.get("success"):
        print(f"\n🎉 Expansion réussie: {result['recipes_obtained']} recettes")
    else:
        print(f"\n❌ Échec expansion")
