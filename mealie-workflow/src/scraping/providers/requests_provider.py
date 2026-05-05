#!/usr/bin/env python3
"""
Provider de scraping via requests + BeautifulSoup
Fallback local qui ne dépend pas de Cascade
"""

import sys
from pathlib import Path
from typing import Optional, List
import requests
from bs4 import BeautifulSoup

# Ajouter le chemin du module scraping
sys.path.insert(0, str(Path(__file__).parent.parent))
from base import ScrapingProvider


class RequestsProvider(ScrapingProvider):
    """Provider de scraping via requests + BeautifulSoup"""
    
    def __init__(self):
        self.name = "Requests + BeautifulSoup (Local)"
    
    def extract_url(self, url: str) -> Optional[str]:
        """Extrait le contenu via requests + BeautifulSoup avec parsing spécifique par source"""
        try:
            print(f"   🌐 Extraction via requests: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parser le HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Détecter la source et utiliser les sélecteurs appropriés
            domain = self._extract_domain(url)
            
            if 'marmiton' in domain:
                return self._extract_marmiton_content(soup, url)
            elif '750g' in domain:
                return self._extract_750g_content(soup, url)
            else:
                # Fallback générique : extraire le texte
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                text = soup.get_text(separator='\n', strip=True)
                
                if len(text) > 100:
                    print(f"   ✅ Contenu extrait: {len(text)} caractères")
                    return text
                else:
                    print(f"   ⚠️ Contenu trop court: {len(text)} caractères")
                    return None
        except Exception as e:
            print(f"   ❌ Erreur extraction: {e}")
            return None
    
    def _extract_domain(self, url: str) -> str:
        """Extrait le domaine de l'URL"""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    def _extract_marmiton_content(self, soup, url: str) -> dict:
        """Extrait le contenu spécifique Marmiton via JSON-LD et retourne un dict structuré"""
        import json
        try:
            # Chercher les données JSON-LD de type Recipe
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    if data.get('@type') == 'Recipe':
                        # Extraire le nom
                        name = data.get('name', 'Recette')
                        
                        # Extraire les ingrédients
                        ingredients = data.get('recipeIngredient', [])
                        if isinstance(ingredients, str):
                            ingredients = [ingredients]
                        
                        # Extraire les instructions
                        instructions = []
                        recipe_instructions = data.get('recipeInstructions', [])
                        for instr in recipe_instructions:
                            if isinstance(instr, dict):
                                instructions.append(instr.get('text', instr.get('name', '')))
                            else:
                                instructions.append(str(instr))
                        
                        # Extraire l'image
                        image = data.get('image', '')
                        
                        # Extraire les temps (ISO 8601 duration → minutes)
                        prep_time = self._parse_iso_duration(data.get('prepTime'))
                        cook_time = self._parse_iso_duration(data.get('cookTime'))
                        total_time = self._parse_iso_duration(data.get('totalTime'))
                        
                        # Extraire les portions
                        servings = self._extract_servings(data.get('recipeYield'))
                        
                        print(f"   ✅ Contenu extrait via JSON-LD: {len(ingredients)} ingrédients, {len(instructions)} instructions")
                        
                        return {
                            'name': name,
                            'ingredients': ingredients,
                            'instructions': instructions,
                            'image': image,
                            'prep_time': prep_time,
                            'cook_time': cook_time,
                            'total_time': total_time,
                            'servings': servings,
                            'raw_content': json.dumps(data, ensure_ascii=False)
                        }
                except json.JSONDecodeError:
                    continue
            
            # Fallback : extraire depuis le texte HTML
            ingredients = []
            ingredient_items = soup.select('[class*="ingredient"]')
            for item in ingredient_items:
                text = item.get_text(strip=True)
                if text and len(text) > 5:
                    ingredients.append(text)
            
            print(f"   ✅ Contenu extrait via fallback: {len(ingredients)} ingrédients")
            
            return {
                'name': 'Recette',
                'ingredients': ingredients,
                'instructions': [],
                'image': '',
                'raw_content': ''
            }
        except Exception as e:
            print(f"   ❌ Erreur extraction Marmiton: {e}")
            return None
    
    def _extract_750g_content(self, soup, url: str) -> str:
        """Extrait le contenu spécifique 750g"""
        # Extraire les ingrédients
        ingredients = []
        ingredient_items = soup.select('.ingredients-list li, .ingredient, .recipe-ingredient')
        for item in ingredient_items:
            text = item.get_text(strip=True)
            if text:
                ingredients.append(text)
        
        # Extraire les instructions
        instructions = []
        instruction_items = soup.select('.steps-list li, .instruction, .recipe-step')
        for item in instruction_items:
            text = item.get_text(strip=True)
            if text and len(text) > 5:
                instructions.append(text)
        
        # Construire un texte structuré
        structured_text = f"INGRÉDIENTS:\n" + "\n".join(ingredients) + "\n\nINSTRUCTIONS:\n" + "\n".join(instructions)
        
        if len(structured_text) > 100:
            print(f"   ✅ Contenu extrait: {len(structured_text)} caractères ({len(ingredients)} ingrédients, {len(instructions)} instructions)")
            return structured_text
        else:
            print(f"   ⚠️ Contenu trop court: {len(structured_text)} caractères")
            return None
    
    @staticmethod
    def _parse_iso_duration(duration_str) -> Optional[str]:
        """Convertit une durée ISO 8601 (PT15M, PT1H30M) en minutes (str)."""
        if not duration_str:
            return None
        import re
        m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?', str(duration_str))
        if not m:
            return None
        hours = int(m.group(1) or 0)
        minutes = int(m.group(2) or 0)
        total = hours * 60 + minutes
        return str(total) if total > 0 else None

    @staticmethod
    def _extract_servings(yield_val) -> Optional[str]:
        """Extrait le nombre de portions depuis recipeYield (str, int ou list)."""
        if yield_val is None:
            return None
        import re
        if isinstance(yield_val, list):
            yield_val = yield_val[0] if yield_val else None
        if yield_val is None:
            return None
        val = str(yield_val).strip()
        nums = re.findall(r'\d+', val)
        return nums[0] if nums else None

    def search_images(self, query: str, num: int = 3) -> List[str]:
        """Recherche des images via Google Images (fallback)"""
        try:
            print(f"   🖼️ Recherche images (fallback): {query}")
            # Pour l'instant, retourne une liste vide car les MCP Jina sont nécessaires pour la recherche d'images
            # On pourrait implémenter une alternative via Google Images ou Unsplash API
            return []
        except Exception as e:
            print(f"   ❌ Erreur recherche images: {e}")
            return []
    
    def get_provider_name(self) -> str:
        return self.name
    
    def is_available(self) -> bool:
        """Vérifie si requests est disponible"""
        try:
            import requests
            return True
        except ImportError:
            return False
