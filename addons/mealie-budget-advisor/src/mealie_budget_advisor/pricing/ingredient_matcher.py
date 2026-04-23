"""Matching d'ingrédients vers produits avec prix."""

import logging
import re
from typing import Optional

from rapidfuzz import fuzz, process

from .manual_pricer import ManualPricer
from .open_prices_client import OpenPricesClient

logger = logging.getLogger(__name__)


class IngredientMatcher:
    """Match les ingrédients de recettes avec des produits ayant des prix."""

    # Mapping des unités courantes vers unités standard
    UNIT_ALIASES = {
        # Grammes
        "g": "g", "gram": "g", "grams": "g", "gramme": "g", "grammes": "g",
        # Kilogrammes
        "kg": "kg", "kilogram": "kg", "kilograms": "kg", "kilo": "kg", "kilos": "kg",
        # Millilitres
        "ml": "ml", "milliliter": "ml", "milliliters": "ml", "millilitre": "ml", "millilitres": "ml",
        # Litres
        "l": "l", "liter": "l", "liters": "l", "litre": "l", "litres": "l",
        # Cuillères
        "tsp": "tsp", "teaspoon": "tsp", "teaspoons": "tsp", "cuillère à café": "tsp",
        "tbsp": "tbsp", "tablespoon": "tbsp", "tablespoons": "tbsp", "cuillère à soupe": "tbsp",
        # Tasses
        "cup": "cup", "cups": "cup", "tasse": "cup", "tasses": "cup",
        # Pièces
        "unit": "unit", "piece": "unit", "pieces": "unit", "pc": "unit", "pcs": "unit",
        "pièce": "unit", "pièces": "unit",
    }

    # Conversion vers unité de base (pour calcul de coût)
    UNIT_TO_BASE = {
        "g": ("kg", 0.001),
        "kg": ("kg", 1.0),
        "ml": ("l", 0.001),
        "l": ("l", 1.0),
        "tsp": ("ml", 5.0),  # ~5ml
        "tbsp": ("ml", 15.0),  # ~15ml
        "cup": ("ml", 240.0),  # ~240ml
        "unit": ("unit", 1.0),
    }

    def __init__(
        self,
        manual_pricer: Optional[ManualPricer] = None,
        open_prices: Optional[OpenPricesClient] = None,
    ) -> None:
        self.manual = manual_pricer or ManualPricer()
        self.open_prices = open_prices or OpenPricesClient()
        self._open_prices_enabled = True

    def parse_ingredient_note(self, note: str) -> tuple[float, str, str]:
        """Parse une note d'ingrédient Mealie.

        Args:
            note: Texte de l'ingrédient (ex: "2 cuillères à soupe d'huile d'olive")

        Returns:
            Tuple (quantité, unité, nom_ingrédient)
        """
        # Patterns communs
        patterns = [
            # "2 cuillères à soupe d'huile"
            r"^(?P<qty>\d+(?:\.\d+)?)\s+(?P<unit>cuillères?\s+à\s+(?:soupe|café)|c\.\s*(?:à|a)\.\s*s\.?|c\.\s*(?:à|a)\.\s*c\.?)\s+d['e]?(?P<name>.+)$",
            # "200g de farine" ou "200 g farine"
            r"^(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>g|kg|ml|l|cl|mg|tasses?|cups?)\s+(?:de\s+)?(?P<name>.+)$",
            # "2 pommes"
            r"^(?P<qty>\d+(?:\.\d+)?)\s+(?P<name>\w+(?:\s+\w+){0,3})$",
            # Juste le nom
            r"^(?P<name>.+)$",
        ]

        for pattern in patterns:
            match = re.match(pattern, note.strip(), re.IGNORECASE)
            if match:
                groups = match.groupdict()
                qty = float(groups.get("qty", 1) or 1)
                unit_raw = groups.get("unit", "unit") or "unit"
                name = groups.get("name", note).strip()

                # Normaliser l'unité
                unit = self._normalize_unit(unit_raw)

                return qty, unit, name

        # Fallback: tout est le nom
        return 1.0, "unit", note.strip()

    def _normalize_unit(self, unit: str) -> str:
        """Normalise une unité vers le format standard."""
        unit_lower = unit.lower().strip()

        # Gestion spéciale des cuillères
        if "soupe" in unit_lower or ("c" in unit_lower and "s" in unit_lower):
            return "tbsp"
        if "café" in unit_lower or ("c" in unit_lower and "c" in unit_lower):
            return "tsp"

        return self.UNIT_ALIASES.get(unit_lower, "unit")

    def normalize_quantity(
        self, quantity: float, unit: str
    ) -> tuple[float, str]:
        """Convertit une quantité vers l'unité de base.

        Returns:
            Tuple (quantité_base, unité_base)
        """
        normalized_unit = self._normalize_unit(unit)

        if normalized_unit in self.UNIT_TO_BASE:
            base_unit, multiplier = self.UNIT_TO_BASE[normalized_unit]
            return quantity * multiplier, base_unit

        return quantity, normalized_unit

    def find_price(
        self,
        ingredient_name: str,
        quantity: float = 1.0,
        unit: str = "unit",
        use_open_prices: bool = True,
    ) -> tuple[float, str, float]:
        """Trouve le prix pour un ingrédient.

        Args:
            ingredient_name: Nom de l'ingrédient
            quantity: Quantité
            unit: Unité
            use_open_prices: Utiliser Open Prices si pas trouvé en manuel

        Returns:
            Tuple (prix_total, source, confiance)
        """
        normalized_name = ingredient_name.lower().strip()

        # 1. Chercher dans les prix manuels
        manual_price = self.manual.get_price(normalized_name)
        if manual_price:
            qty_base, unit_base = self.normalize_quantity(quantity, unit)
            price_multiplier = self._get_price_multiplier(manual_price.unit, unit_base)
            total_price = qty_base * manual_price.price_per_unit * price_multiplier
            return round(total_price, 2), "manual", 1.0

        # 2. Chercher via Open Prices (si activé)
        if use_open_prices and self._open_prices_enabled:
            prices = self.open_prices.search_prices(ingredient_name, limit=5)

            if prices:
                # Prendre le prix médian pour stabilité
                sorted_prices = sorted([p.price_per_base_unit for p in prices])
                median_price = sorted_prices[len(sorted_prices) // 2]

                qty_base, unit_base = self.normalize_quantity(quantity, unit)
                # Estimation grossière: on suppose que le prix Open Prices est pour ~1kg/1l
                total_price = qty_base * median_price

                confidence = min(0.8, 0.5 + (len(prices) / 20))  # Plus de données = plus confiant
                return round(total_price, 2), "open_prices", confidence

        # 3. Fallback: estimation basée sur la catégorie
        estimated_price = self._estimate_price(ingredient_name, quantity, unit)
        return estimated_price, "estimated", 0.3

    def _get_price_multiplier(self, price_unit: str, target_unit: str) -> float:
        """Calcule le multiplicateur pour convertir entre unités de prix."""
        # Si même unité, pas de conversion
        if price_unit.lower() == target_unit.lower():
            return 1.0

        # kg <-> g
        if price_unit == "kg" and target_unit == "g":
            return 0.001
        if price_unit == "g" and target_unit == "kg":
            return 1000.0

        # l <-> ml
        if price_unit == "l" and target_unit == "ml":
            return 0.001
        if price_unit == "ml" and target_unit == "l":
            return 1000.0

        # Unités inconnues: 1:1 (risqué mais nécessaire)
        return 1.0

    def _estimate_price(
        self,
        ingredient_name: str,
        quantity: float,
        unit: str,
    ) -> float:
        """Estimation de prix basée sur des règles simples."""
        name_lower = ingredient_name.lower()

        # Base de règles très simplifiée
        price_indicators = {
            # Viandes/poissons (cher)
            "bœuf": 15.0, "boeuf": 15.0, "veau": 18.0, "agneau": 16.0,
            "poulet": 8.0, "dinde": 7.0, "canard": 12.0,
            "saumon": 14.0, "thon": 10.0, "cabillaud": 12.0,

            # Légumes frais (moyen)
            "tomate": 2.5, "oignon": 1.5, "ail": 3.0, "poivron": 3.0,
            "courgette": 2.0, "aubergine": 2.5, "carotte": 1.5,
            "pomme de terre": 1.2, "patate": 1.2, "salade": 1.5,

            # Féculents (bon marché)
            "riz": 2.0, "pâtes": 1.5, "pate": 1.5, "farfalle": 1.8,
            "penne": 1.8, "spaghetti": 1.5, "nouilles": 2.0,
            "farine": 1.0, "pain": 2.0,

            # Produits laitiers
            "lait": 1.0, "crème": 4.0, "creme": 4.0, "beurre": 8.0,
            "fromage": 10.0, "emmental": 8.0, "gruyère": 12.0,
            "mozzarella": 6.0, "parmesan": 15.0,

            # Huiles/condiments
            "huile": 5.0, "vinaigre": 2.0, "moutarde": 3.0, "ketchup": 2.5,

            # Herbes/épices (petites quantités, prix élevé au kg)
            "basilic": 15.0, "persil": 8.0, "thym": 12.0, "laurier": 10.0,
            "cumin": 20.0, "paprika": 18.0,
        }

        # Chercher une correspondance
        base_price_per_kg = 5.0  # Default moyen
        for keyword, price in price_indicators.items():
            if keyword in name_lower:
                base_price_per_kg = price
                break

        # Convertir vers unité de base
        qty_base, unit_base = self.normalize_quantity(quantity, unit)

        # Calculer prix
        if unit_base == "kg":
            return round(qty_base * base_price_per_kg, 2)
        elif unit_base == "l":
            return round(qty_base * base_price_per_kg * 0.8, 2)  # Légèrement moins cher que viande
        else:
            return round(qty_base * base_price_per_kg * 0.1, 2)  # unités: estimation

    def match_ingredient_to_product(
        self,
        ingredient_name: str,
        candidates: list[str],
        threshold: float = 70.0,
    ) -> Optional[tuple[str, float]]:
        """Match un ingrédient à une liste de produits via fuzzy matching.

        Args:
            ingredient_name: Nom de l'ingrédient
            candidates: Liste des noms de produits
            threshold: Score minimum (0-100)

        Returns:
            Tuple (meilleur_match, score) ou None
        """
        if not candidates:
            return None

        result = process.extractOne(
            ingredient_name.lower(),
            [c.lower() for c in candidates],
            scorer=fuzz.token_sort_ratio,
        )

        if result and result[1] >= threshold:
            return result[0], result[1]

        return None
