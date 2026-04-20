"""Open Food Facts API client — recherche nutritionnelle par ingrédient."""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

from ..models.nutrition import NutritionFacts, NutritionSource
from .off_rate_limiter import wait_for_off_rate_limit

logger = logging.getLogger(__name__)

OFF_BASE_URL = os.environ.get("OFF_BASE_URL", "https://world.openfoodfacts.org/api/v2")
OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
REQUEST_TIMEOUT = 10.0


class OpenFoodFactsClient:
    """Client HTTP pour l'API Open Food Facts (sans clé, gratuit)."""

    def __init__(self, base_url: str = OFF_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "mealie-nutrition-advisor/0.1 (github.com/nonofr91/addonmealie)"},
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "OpenFoodFactsClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def search(self, ingredient_name: str, language: str = "fr") -> tuple[Optional[NutritionFacts], Optional[float]]:
        """
        Recherche un ingrédient dans OFF et retourne les données nutritionnelles /100g
        et le poids moyen de vente en grammes.
        Retourne (None, None) si aucun résultat ou si l'appel échoue.
        """
        try:
            # Rate limiting partagé pour OFF
            wait_for_off_rate_limit()
            
            params = {
                "search_terms": ingredient_name,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 5,
                "fields": "product_name,nutriments,categories_tags,quantity",
                "lc": language,
            }
            response = self._client.get(OFF_SEARCH_URL, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("OFF HTTP error pour '%s': %s", ingredient_name, exc)
            return None, None
        except Exception as exc:
            logger.warning("OFF erreur inattendue pour '%s': %s", ingredient_name, exc)
            return None, None

        products = data.get("products", [])
        if not products:
            logger.debug("OFF: aucun produit pour '%s'", ingredient_name)
            return None, None

        # Calculer le poids moyen sur tous les produits pertinents
        weights = []
        for product in products:
            nutriments = product.get("nutriments", {})
            if not nutriments:
                continue
            facts = self._parse_nutriments(nutriments)
            if not facts.is_empty():
                # Extraire le poids depuis le champ quantity
                weight = self._extract_weight(product.get("quantity", ""))
                if weight:
                    weights.append(weight)

        # Retourner le premier produit valide pour nutrition et le poids moyen
        for product in products:
            nutriments = product.get("nutriments", {})
            if not nutriments:
                continue
            facts = self._parse_nutriments(nutriments)
            if not facts.is_empty():
                typical_weight = sum(weights) / len(weights) if weights else None
                logger.debug("OFF: résultat trouvé pour '%s' → %.0f kcal/100g (poids moyen: %s g)", ingredient_name, facts.calories_kcal, typical_weight or "N/A")
                return facts, typical_weight

        logger.debug("OFF: produits trouvés mais sans données nutritionnelles pour '%s'", ingredient_name)
        return None, None

    @staticmethod
    def _extract_weight(quantity_str: str) -> Optional[float]:
        """Extrait le poids en grammes depuis une chaîne de quantité OFF (ex: '500 g', '1.5 kg')."""
        if not quantity_str:
            return None
        try:
            quantity_str = quantity_str.lower().strip()
            # Chercher "X g" ou "X kg"
            import re
            match = re.match(r'([\d.,]+)\s*(kg|g)', quantity_str)
            if match:
                val = float(match.group(1).replace(',', '.'))
                unit = match.group(2)
                if unit == 'kg':
                    return val * 1000
                return val
        except Exception:
            pass
        return None

    @staticmethod
    def _parse_nutriments(n: dict) -> NutritionFacts:
        """Extrait les valeurs nutritionnelles depuis un objet nutriments OFF."""

        def _get(key: str) -> float:
            for suffix in ("_100g", "_serving", ""):
                val = n.get(f"{key}{suffix}")
                if val is not None:
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        pass
            return 0.0

        return NutritionFacts(
            calories_kcal=_get("energy-kcal") or (_get("energy") / 4.184 if _get("energy") else 0.0),
            protein_g=_get("proteins"),
            fat_g=_get("fat"),
            saturated_fat_g=_get("saturated-fat"),
            carbohydrate_g=_get("carbohydrates"),
            sugar_g=_get("sugars"),
            fiber_g=_get("fiber"),
            sodium_mg=_get("sodium") * 1000 if _get("sodium") else _get("salt") * 400,
            source=NutritionSource.open_food_facts,
            confidence=0.85,
        )
