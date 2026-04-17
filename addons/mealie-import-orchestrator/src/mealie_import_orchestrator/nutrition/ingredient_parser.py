"""Parse ingredient text → (food_name, quantity_g).

Handles text like:
  "200g de poulet haché"
  "2 cuillères à soupe d'huile d'olive"
  "1 oignon moyen"
  "sel et poivre"
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Optional

from .quantity_estimator import QuantityEstimator

logger = logging.getLogger(__name__)

UNIT_TO_GRAMS: dict[str, float] = {
    "g": 1,
    "gr": 1,
    "gramme": 1,
    "grammes": 1,
    "kg": 1000,
    "kilogramme": 1000,
    "kilogrammes": 1000,
    "ml": 1,
    "cl": 10,
    "dl": 100,
    "l": 1000,
    "litre": 1000,
    "litres": 1000,
    "cuillère à soupe": 15,
    "cuillères à soupe": 15,
    "c. à s.": 15,
    "cs": 15,
    "tbsp": 15,
    "cuillère à café": 5,
    "cuillères à café": 5,
    "c. à c.": 5,
    "cc": 5,
    "tsp": 5,
    "tasse": 240,
    "tasses": 240,
    "cup": 240,
    "cups": 240,
    "verre": 200,
    "verres": 200,
    "bol": 350,
    "tranche": 30,
    "tranches": 30,
    "slice": 30,
    "poignée": 30,
    "poignées": 30,
    "botte": 100,
    "bottes": 100,
    "filet": 150,
    "filets": 150,
    "pincée": 1,
    "pincées": 1,
    "noix": 10,
}

DEFAULT_WEIGHTS_G: dict[str, float] = {
    # Viandes entières (poids moyens de vente)
    "gigot": 1500,
    "gigot d'agneau": 1500,
    "poulet": 1200,
    "poulet entier": 1200,
    "lapin": 1500,
    "canard": 1500,
    "dinde": 5000,
    "rôti de porc": 1000,
    # Poissons entiers
    "saumon": 400,
    "saumon entier": 400,
    "truite": 300,
    "dorade": 400,
    "bar": 400,
    # Fruits/légumes moyens
    "oignon": 80,
    "ail": 5,
    "gousse d'ail": 5,
    "tomate": 100,
    # Épices/condiments (quantités réalistes)
    "sel": 2,
    "poivre": 1,
    "muscade": 1,
    "cannelle": 1,
    "piment": 1,
    "paprika": 1,
    "curry": 2,
    "thym": 1,
    "romarin": 1,
    "origan": 1,
    "basilic": 1,
    "persil": 1,
    "estragon": 1,
    "ciboulette": 1,
    "vanille": 1,
    "safran": 0.1,
    "courgette": 200,
    "aubergine": 250,
    "poivron": 150,
    "carotte": 70,
    "pomme de terre": 150,
    "patate": 150,
    "citron": 80,
    "orange": 150,
    "pomme": 150,
    "banane": 120,
    # Autres
    "œuf": 50,
    "oeuf": 50,
    # Ajouts basés sur l'analyse d'ingrédients sans poids
    "graisse d'oie": 30,
    "graisse de canard": 30,
    "os à moelle": 100,
    "os": 100,
    "estragon": 5,
    "herbes": 5,
}

DEFAULT_QUANTITY_G = 50.0
USE_AI_ESTIMATION = os.environ.get("USE_AI_ESTIMATION", "false").lower() == "true"

QUANTITY_PATTERN = re.compile(
    r"^(?P<qty>\d+[\.,]?\d*)\s*"
    r"(?P<unit>" + "|".join(sorted(UNIT_TO_GRAMS.keys(), key=len, reverse=True)) + r")?\s*"
    r"(?:de |d'|du |des |of )?\s*"
    r"(?P<food>.+)$",
    re.IGNORECASE,
)

STOP_WORDS = {
    "haché", "hachée", "coupé", "coupée", "émincé", "émincée", "râpé", "râpée",
    "frais", "fraîche", "cru", "crue", "cuit", "cuite",
    "environ", "au goût", "selon", "facultatif", "optionnel",
}


@dataclass
class ParsedIngredient:
    raw_text: str
    food_name: str
    quantity_g: float


def parse_ingredient(text: str, servings: int = 4, use_ai: bool = USE_AI_ESTIMATION) -> ParsedIngredient:
    """Parse un texte d'ingrédient en (food_name, quantity_g).

    Pipeline de priorité :
    1. Quantité explicite (ex: "200g de poulet")
    2. DEFAULT_WEIGHTS_G (ex: "1 gigot" → 1500g)
    3. IA estimation (si use_ai=True et pas épice/condiment)
    4. DEFAULT_QUANTITY_G fallback

    Args:
        text: Texte de l'ingrédient
        servings: Nombre de portions pour le contexte
        use_ai: Utiliser l'estimation IA (défaut: USE_AI_ESTIMATION env var)
    """
    text = text.strip()
    if not text:
        logger.debug("Empty ingredient text, using default quantity")
        return ParsedIngredient(raw_text=text, food_name=text, quantity_g=DEFAULT_QUANTITY_G)

    # 1. Quantité explicite
    m = QUANTITY_PATTERN.match(text)
    if m:
        qty = float(m.group("qty").replace(",", "."))
        unit = (m.group("unit") or "").lower().strip()
        food = _clean_food_name(m.group("food"))
        grams = qty * UNIT_TO_GRAMS.get(unit, DEFAULT_QUANTITY_G / qty if unit == "" else DEFAULT_QUANTITY_G)
        logger.debug("Parsed explicit quantity: '%s' -> food='%s', qty=%.1fg (unit=%s, raw_qty=%s)", text, food, grams, unit, qty)
        return ParsedIngredient(raw_text=text, food_name=food, quantity_g=round(grams, 1))

    food_clean = _clean_food_name(text)
    logger.debug("No explicit quantity pattern match for '%s', cleaned food='%s'", text, food_clean)
    
    # Détecter si c'est une épice/condiment - désactiver IA pour ces cas-là
    spice_keywords = ["sel", "poivre", "muscade", "cannelle", "piment", "paprika", "curry", "thym", "romarin", "origan", "basilic", "persil", "estragon", "ciboulette", "vanille", "safran"]
    is_spice = any(keyword in food_clean.lower() for keyword in spice_keywords)
    
    if is_spice:
        use_ai = False  # Désactiver IA pour les épices/condiments
        logger.debug("Detected spice/condiment '%s', AI estimation disabled", food_clean)

    # 2. DEFAULT_WEIGHTS_G
    for key, weight in DEFAULT_WEIGHTS_G.items():
        if key.lower() in food_clean.lower():
            logger.debug("Matched DEFAULT_WEIGHTS_G: '%s' -> %sg (key='%s')", food_clean, weight, key)
            return ParsedIngredient(raw_text=text, food_name=food_clean, quantity_g=weight)

    logger.debug("No DEFAULT_WEIGHTS_G match for '%s'", food_clean)

    # 3. IA estimation (optionnel)
    if use_ai:
        logger.debug("Attempting AI estimation for '%s' (use_ai=True)", food_clean)
        estimator = QuantityEstimator()
        estimated = estimator.estimate(text, servings)
        if estimated:
            logger.debug("AI estimation successful: '%s' -> %sg", food_clean, estimated)
            return ParsedIngredient(raw_text=text, food_name=food_clean, quantity_g=estimated)
        else:
            logger.debug("AI estimation failed or returned None for '%s'", food_clean)
    else:
        logger.debug("AI estimation disabled for '%s' (use_ai=%s, is_spice=%s)", food_clean, use_ai, is_spice)

    # 4. Fallback DEFAULT_QUANTITY_G
    logger.debug("Using fallback DEFAULT_QUANTITY_G=%sg for '%s'", DEFAULT_QUANTITY_G, food_clean)
    return ParsedIngredient(raw_text=text, food_name=food_clean, quantity_g=DEFAULT_QUANTITY_G)


def _clean_food_name(food: str) -> str:
    """Nettoie le nom de l'aliment (ponctuation, parenthèses, stop words)."""
    food = re.sub(r"\(.*?\)", "", food)
    food = re.sub(r"[,;]+.*$", "", food)
    tokens = food.split()
    tokens = [t for t in tokens if t.lower() not in STOP_WORDS]
    return " ".join(tokens).strip() or food.strip()
