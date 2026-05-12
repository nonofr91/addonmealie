"""Matching d'ingrédients vers produits avec prix."""

import logging
import re
from typing import Optional

from rapidfuzz import fuzz, process

from .ingredient_weights import get_ingredient_weight
from .manual_pricer import ManualPricer
from .open_prices_client import OpenPricesClient
from .price_collector_client import PriceCollectorClient

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
        # Centilitres
        "cl": "cl", "centilitre": "cl", "centilitres": "cl",
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
        "cl": ("l", 0.01),
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
        price_collector: Optional[PriceCollectorClient] = None,
    ) -> None:
        self.manual = manual_pricer or ManualPricer()
        self.open_prices = open_prices or OpenPricesClient()
        self.price_collector = price_collector
        self._open_prices_enabled = True

    def parse_ingredient_note(self, note: str) -> tuple[float, str, str]:
        """Parse une note d'ingrédient Mealie.

        Args:
            note: Texte de l'ingrédient (ex: "2 cuillères à soupe d'huile d'olive")

        Returns:
            Tuple (quantité, unité, nom_ingrédient)
        """
        note = note.strip()

        # Helper: convertir virgule française en point décimal
        def parse_qty(qty_str: str) -> float:
            qty_str = qty_str.replace(",", ".")
            try:
                return float(qty_str)
            except ValueError:
                return 1.0

        # Patterns communs (ordre important: du plus spécifique au moins)
        patterns = [
            # Fractions: "1/2 tasse de lait", "3/4 cup sugar"
            r"^(?P<qty>\d+/\d+)\s+(?P<unit>tasse?|cup|cuill[èe]res?\s+à\s+(?:soupe|café)|tsp|tbsp|g|kg|ml|l|cl)\s+(?:de\s+)?(?P<name>.+)$",
            # "200g de farine", "200 g farine", "200g farine" - METTRE AVANT les cuillères pour éviter le conflit cl/tsp
            r"^(?P<qty>\d+(?:[,.]\d+)?)\s*(?P<unit>g|kg|ml|l|cl|mg|tasses?|cups?|oz|lb)\s+(?:de\s+)?(?P<name>.+)$",
            # "2 cuillères à soupe d'huile" ou "2 c. à s. huile" (avec adjectifs optionnels: rases, bombées)
            r"^(?P<qty>\d+(?:[,.]\d+)?)\s+(?P<unit>cuill[èe]res?\s+à\s+(?:soupe|café)|c\.\s*(?:à|a)\.\s*s\.?|c\.\s*(?:à|a)\.\s*c\.?|tbsp|tsp)(?:\s+(?:rases?|bombées?))?\s+d['e]?(?P<name>.+)$",
            # "2 pommes", "3 oeufs" - EXCLURE les mots qui ressemblent à des unités
            r"^(?P<qty>\d+(?:[,.]\d+)?)\s+(?P<name>[a-zA-ZàâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ\w\s\-']+)$",
            # "huile d'olive" (pas de quantité explicite)
            r"^(?P<name>[a-zA-ZàâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ\w\s\-']+)$",
        ]

        for pattern in patterns:
            match = re.match(pattern, note, re.IGNORECASE)
            if match:
                groups = match.groupdict()
                qty_str = groups.get("qty", "1") or "1"
                unit_raw = groups.get("unit", "unit") or "unit"
                name = groups.get("name", note).strip()

                # Parser la quantité (gère fractions)
                if "/" in qty_str:
                    num, den = qty_str.split("/")
                    qty = float(num) / float(den)
                else:
                    qty = parse_qty(qty_str)

                # Normaliser l'unité
                unit = self._normalize_unit(unit_raw)

                # Nettoyer le nom (enlever "de " au début)
                name = re.sub(r"^(de|d')\s+", "", name, flags=re.IGNORECASE)
                name = name.strip()

                return qty, unit, name

        # Fallback: tout est le nom
        return 1.0, "unit", note

    def _normalize_unit(self, unit: str) -> str:
        """Normalise une unité vers le format standard."""
        unit_lower = unit.lower().strip()

        # Priorité aux unités métriques explicites
        if unit_lower in ["g", "kg", "ml", "l", "cl", "mg"]:
            return unit_lower

        # Gestion spéciale des cuillères - café avant soupe pour éviter les faux positifs
        if "café" in unit_lower:
            return "tsp"
        if "soupe" in unit_lower or ("c" in unit_lower and "s" in unit_lower):
            return "tbsp"

        return self.UNIT_ALIASES.get(unit_lower, "unit")

    def _normalize_ingredient_name(self, name: str) -> str:
        """Normalise un nom d'ingrédient pour le matching.

        Supprime les préfixes courants comme "d'", "de", "1 barquettes d'", etc.
        """
        name = name.strip().lower()
        
        # Supprimer les préfixes numériques + quantités + articles
        patterns_to_remove = [
            r"^\d+\s+(?:barquettes?|boîtes?|paquets?|bouteilles?|verres?|tasses?|cuill[èe]res?|gouttes?|pincées?)\s+d['e]?\s*",
            r"^\d+/\d+\s+(?:barquettes?|boîtes?|paquets?|bouteilles?)\s+d['e]?\s*",
            r"^(?:de|d')\s+",
            r"^\d+\s*(?:barquettes?|boîtes?|paquets?|bouteilles?)\s+",
        ]
        
        for pattern in patterns_to_remove:
            name = re.sub(pattern, "", name, flags=re.IGNORECASE)
        
        # Nettoyer les espaces multiples
        name = re.sub(r"\s+", " ", name).strip()
        
        return name

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
        
        # Conversion spéciale: moules en litres → kg (1l de moules ≈ 0.8 kg)
        if "moule" in normalized_name and unit == "l":
            original_qty = quantity
            quantity = quantity * 0.8
            unit = "kg"
            logger.debug(f"Conversion moules: {original_qty} l → {quantity} kg")
        
        # Ingrédients gratuits (eau, sel de table, etc.)
        free_ingredients = ["eau", "water", "sel de table", "table salt", "sel", "poivre"]
        if any(free in normalized_name for free in free_ingredients):
            return 0.0, "free", 1.0

        # 1. Chercher dans les prix manuels
        manual_price = self.manual.get_price(normalized_name)
        if manual_price:
            qty_base, unit_base = self.normalize_quantity(quantity, unit)
            
            # Si l'ingrédient est en unit mais le prix est en kg/l, utiliser le poids moyen
            if unit_base == "unit" and manual_price.unit in ["kg", "l"]:
                weight_per_unit = get_ingredient_weight(ingredient_name)
                qty_base = qty_base * weight_per_unit
                unit_base = manual_price.unit
                logger.debug(f"Conversion {ingredient_name}: {quantity} unit × {weight_per_unit}kg/unit = {qty_base}{unit_base}")
            
            price_multiplier = self._get_price_multiplier(manual_price.unit, unit_base)
            total_price = qty_base * manual_price.price_per_unit * price_multiplier
            return round(total_price, 2), "manual", 1.0

        # 2. Chercher via Price Collector (addon interne — données fiables)
        if self.price_collector:
            # Essayer avec le nom normalisé (sans préfixes)
            normalized_name = self._normalize_ingredient_name(ingredient_name)
            result = self.price_collector.search_price(normalized_name)
            if result:
                price_per_unit, pc_unit = result
                qty_base, unit_base = self.normalize_quantity(quantity, unit)
                if unit_base == "unit":
                    weight_per_unit = get_ingredient_weight(ingredient_name)
                    qty_base = qty_base * weight_per_unit
                    unit_base = "kg"
                price_multiplier = self._get_price_multiplier(pc_unit, unit_base)
                total_price = qty_base * price_per_unit * price_multiplier
                return round(total_price, 2), "price_collector", 0.9

        # 3. Chercher via Open Prices (si activé)
        if use_open_prices and self._open_prices_enabled:
            prices = self.open_prices.search_prices(ingredient_name, limit=5)

            if prices:
                # Prendre le prix médian pour stabilité
                sorted_prices = sorted([p.price_per_base_unit for p in prices])
                median_price = sorted_prices[len(sorted_prices) // 2]

                qty_base, unit_base = self.normalize_quantity(quantity, unit)
                
                # Conversion intelligente: le prix Open Prices est en €/kg ou €/l
                # Si l'ingrédient est en unités, on utilise le poids moyen spécifique
                if unit_base == "unit":
                    # Utiliser la base de données de poids moyens par type d'ingrédient
                    weight_per_unit = get_ingredient_weight(ingredient_name)
                    estimated_kg = qty_base * weight_per_unit
                    total_price = estimated_kg * median_price
                    logger.debug(f"Conversion {ingredient_name}: {qty_base} unit × {weight_per_unit}kg/unit = {estimated_kg}kg × {median_price}€/kg = {total_price}€")
                elif unit_base == "kg" or unit_base == "l":
                    # Prix déjà dans la bonne unité
                    total_price = qty_base * median_price
                elif unit_base == "ml":
                    estimated_kg = self._estimate_ml_as_kg(ingredient_name, qty_base)
                    total_price = estimated_kg * median_price
                else:
                    # Fallback: conversion directe (risqué mais nécessaire)
                    total_price = qty_base * median_price

                confidence = min(0.8, 0.5 + (len(prices) / 20))  # Plus de données = plus confiant
                return round(total_price, 2), "open_prices", confidence

        # 3. Fallback: estimation basée sur la catégorie
        estimated_price = self._estimate_price(ingredient_name, quantity, unit)
        return estimated_price, "estimated", 0.3

    def _estimate_ml_as_kg(self, ingredient_name: str, quantity_ml: float) -> float:
        normalized_name = ingredient_name.lower().strip()
        density = 1.0
        if any(keyword in normalized_name for keyword in ["huile", "vinaigre"]):
            density = 0.91
        elif any(
            keyword in normalized_name
            for keyword in [
                "thym",
                "laurier",
                "genièvre",
                "genievre",
                "girofle",
                "cumin",
                "paprika",
                "épice",
                "epice",
            ]
        ):
            density = 0.25
        return (quantity_ml * density) / 1000

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

        # Normaliser le nom de l'ingrédient
        normalized_ing = self._normalize_ingredient_name(ingredient_name)

        # Normaliser les candidats
        normalized_candidates = [self._normalize_product_name(c) for c in candidates]

        # Essayer plusieurs scorers pour trouver le meilleur match
        scorers = [
            fuzz.token_sort_ratio,  # Meilleur pour "huile d'olive" vs "olive oil"
            fuzz.partial_ratio,     # Meilleur pour sous-chaînes
            fuzz.WRatio,            # Weighted ratio (préfère les correspondances complètes)
        ]

        best_match = None
        best_score = 0

        for scorer in scorers:
            result = process.extractOne(
                normalized_ing,
                normalized_candidates,
                scorer=scorer,
            )

            if result and result[1] > best_score:
                best_match = result[0]
                best_score = result[1]

                # Arrêter si on a un excellent match
                if best_score >= 95:
                    break

        if best_match and best_score >= threshold:
            # Retourner le nom original (non normalisé)
            original_idx = normalized_candidates.index(best_match)
            return candidates[original_idx], best_score

        return None

    def _normalize_ingredient_name(self, name: str) -> str:
        """Normalise un nom d'ingrédient pour le matching."""
        name = name.lower().strip()

        # Enlever les articles
        name = re.sub(r"^(le|la|les|un|une|des|de|d')\s+", "", name, flags=re.IGNORECASE)

        # Remplacer les caractères spéciaux
        name = name.replace("é", "e").replace("è", "e").replace("ê", "e")
        name = name.replace("à", "a").replace("â", "a")
        name = name.replace("ô", "o").replace("ö", "o")
        name = name.replace("î", "i").replace("ï", "i")
        name = name.replace("ù", "u").replace("û", "u")
        name = name.replace("ç", "c")

        # Enlever les parenthèses et leur contenu
        name = re.sub(r"\([^)]*\)", "", name)

        # Enlever les mots de qualité (bio, frais, etc.)
        quality_words = ["bio", "frais", "surgelé", "congelé", "nature", "entier"]
        for word in quality_words:
            name = re.sub(rf"\b{word}\b", "", name, flags=re.IGNORECASE)

        # Nettoyer les espaces multiples
        name = re.sub(r"\s+", " ", name).strip()

        return name

    def _normalize_product_name(self, name: str) -> str:
        """Normalise un nom de produit Open Prices."""
        name = name.lower().strip()

        # Même normalisation que pour les ingrédients
        name = re.sub(r"^(le|la|les|un|une|des|de|d')\s+", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\([^)]*\)", "", name)
        name = re.sub(r"\s+", " ", name).strip()

        return name
