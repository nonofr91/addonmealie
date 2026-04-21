"""USDA FoodData Central API client — recherche nutritionnelle par ingrédient."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

import httpx

from ..models.nutrition import NutritionFacts, NutritionSource

logger = logging.getLogger(__name__)

USDA_BASE_URL = os.environ.get("USDA_BASE_URL", "https://api.nal.usda.gov/fdc/v1")
USDA_API_KEY = os.environ.get("USDA_API_KEY", "DEMO_KEY")
REQUEST_TIMEOUT = 10.0
RATE_LIMIT_DELAY = 0.4  # ~1000 req/h = 0.36s minimum, on prend 0.4s pour marge


class USDAFoodDataCentralClient:
    """Client HTTP pour l'API USDA FoodData Central."""

    def __init__(self, base_url: str = USDA_BASE_URL, api_key: str = USDA_API_KEY) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "mealie-nutrition-advisor/0.1 (github.com/nonofr91/addonmealie)"},
        )
        self._last_request_time = 0.0

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "USDAFoodDataCentralClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _wait_for_rate_limit(self) -> None:
        """Attend le rate limiting entre les requêtes USDA."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - time_since_last)
        self._last_request_time = time.time()

    def search(self, ingredient_name: str, language: str = "fr") -> tuple[Optional[NutritionFacts], Optional[float]]:
        """
        Recherche un ingrédient dans USDA et retourne les données nutritionnelles /100g
        et le poids moyen de vente en grammes.
        Retourne (None, None) si aucun résultat ou si l'appel échoue.
        
        Note: USDA utilise principalement des termes en anglais.
        """
        try:
            self._wait_for_rate_limit()
            
            # Traduire l'ingrédient en anglais si nécessaire
            search_term = self._translate_to_english(ingredient_name)
            
            params = {
                "api_key": self.api_key,
                "query": search_term,
                "pageSize": 5,
                "dataType": ["Foundation", "SR Legacy", "Branded"],  # Prioriser les aliments de base
            }
            
            response = self._client.get(f"{self.base_url}/foods/search", params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("USDA HTTP error pour '%s': %s", ingredient_name, exc)
            return None, None
        except Exception as exc:
            logger.warning("USDA erreur inattendue pour '%s': %s", ingredient_name, exc)
            return None, None

        foods = data.get("foods", [])
        if not foods:
            logger.debug("USDA: aucun aliment pour '%s' (recherche: '%s')", ingredient_name, search_term)
            return None, None

        # Chercher le premier aliment avec des données nutritionnelles
        for food in foods:
            fdc_id = food.get("fdcId")
            if not fdc_id:
                continue
            
            # Récupérer les détails nutritionnels
            facts = self._fetch_food_details(fdc_id)
            if facts and not facts.is_empty():
                logger.debug("USDA: résultat trouvé pour '%s' → %.0f kcal/100g (recherche: '%s')", 
                           ingredient_name, facts.calories_kcal, search_term)
                return facts, None  # USDA ne fournit pas de poids moyen de vente

        logger.debug("USDA: aliments trouvés mais sans données nutritionnelles pour '%s'", ingredient_name)
        return None, None

    def _fetch_food_details(self, fdc_id: int) -> Optional[NutritionFacts]:
        """Récupère les détails nutritionnels d'un aliment par son FDC ID."""
        try:
            self._wait_for_rate_limit()
            
            params = {"api_key": self.api_key}
            response = self._client.get(f"{self.base_url}/food/{fdc_id}", params=params)
            response.raise_for_status()
            data = response.json()
            
            return self._parse_nutrients(data)
        except httpx.HTTPError as exc:
            logger.warning("USDA HTTP error pour FDC ID %d: %s", fdc_id, exc)
            return None
        except Exception as exc:
            logger.warning("USDA erreur inattendue pour FDC ID %d: %s", fdc_id, exc)
            return None

    def _translate_to_english(self, ingredient: str) -> str:
        """Traduit un ingrédient français en anglais (mapping basique)."""
        # Dictionnaire de traduction basique pour les ingrédients courants
        translations = {
            "poulet": "chicken",
            "cuisses de poulet": "chicken thighs",
            "blanc de poulet": "chicken breast",
            "courgette": "zucchini",
            "courgettes": "zucchini",
            "pomme de terre": "potato",
            "pommes de terre": "potato",
            "carotte": "carrot",
            "carottes": "carrot",
            "tomate": "tomato",
            "tomates": "tomato",
            "oignon": "onion",
            "oignons": "onion",
            "ail": "garlic",
            "huile d'olive": "olive oil",
            "beurre": "butter",
            "lait": "milk",
            "oeuf": "egg",
            "oeufs": "egg",
            "farine": "flour",
            "sucre": "sugar",
            "sel": "salt",
            "poivre": "pepper",
            "riz": "rice",
            "pâtes": "pasta",
            "pain": "bread",
            "fromage": "cheese",
            "laitue": "lettuce",
            "épinard": "spinach",
            "brocoli": "broccoli",
            "champignon": "mushroom",
            "pommes": "apple",
            "orange": "orange",
            "banane": "banana",
            "citron": "lemon",
            "cumin": "cumin",
            "curry": "curry",
            "cannelle": "cinnamon",
            "vanille": "vanilla",
            "eau": "water",
        }
        
        # Recherche exacte d'abord
        lower_ingredient = ingredient.lower().strip()
        if lower_ingredient in translations:
            return translations[lower_ingredient]
        
        # Recherche partielle
        for fr, en in translations.items():
            if fr in lower_ingredient:
                return en
        
        # Si pas de traduction, utiliser le terme original (USDA peut avoir des termes français)
        return ingredient

    def _parse_nutrients(self, food_data: dict) -> NutritionFacts:
        """Extrait les valeurs nutritionnelles depuis les données USDA."""
        nutrients = food_data.get("foodNutrients", [])
        
        # Mapping des nutriments USDA vers nos champs
        nutrient_map = {
            "Energy": "calories_kcal",
            "Protein": "protein_g",
            "Total lipid (fat)": "fat_g",
            "Total Sugars": "sugar_g",
            "Carbohydrate, by difference": "carbohydrate_g",
            "Fiber, total dietary": "fiber_g",
            "Sodium, Na": "sodium_mg",
            "Saturated Fat": "saturated_fat_g",
        }
        
        # Valeurs par défaut
        values = {
            "calories_kcal": 0.0,
            "protein_g": 0.0,
            "fat_g": 0.0,
            "saturated_fat_g": 0.0,
            "carbohydrate_g": 0.0,
            "sugar_g": 0.0,
            "fiber_g": 0.0,
            "sodium_mg": 0.0,
        }
        
        for nutrient in nutrients:
            name = nutrient.get("name", "")
            amount = nutrient.get("amount", 0)
            unit = nutrient.get("unitName", "")
            
            # Mapper le nutriment
            if name in nutrient_map:
                field = nutrient_map[name]
                
                # Convertir selon l'unité
                if field == "calories_kcal":
                    if unit == "kcal":
                        values[field] = float(amount)
                    elif unit == "kJ":
                        values[field] = float(amount) / 4.184  # Conversion kJ → kcal
                elif field == "sodium_mg":
                    if unit == "mg":
                        values[field] = float(amount)
                    elif unit == "g":
                        values[field] = float(amount) * 1000
                else:
                    # Pour les autres nutriments en g
                    if unit == "g":
                        values[field] = float(amount)
        
        return NutritionFacts(
            calories_kcal=values["calories_kcal"],
            protein_g=values["protein_g"],
            fat_g=values["fat_g"],
            saturated_fat_g=values["saturated_fat_g"],
            carbohydrate_g=values["carbohydrate_g"],
            sugar_g=values["sugar_g"],
            fiber_g=values["fiber_g"],
            sodium_mg=values["sodium_mg"],
            source=NutritionSource.usda_food_data_central,
            confidence=0.90,  # USDA est une source gouvernementale très fiable
        )
