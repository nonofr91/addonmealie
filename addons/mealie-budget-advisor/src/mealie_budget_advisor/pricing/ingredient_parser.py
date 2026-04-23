"""Parse Mealie ingredient text → normalized (name, quantity, unit).

Lightweight parser tailored for budget estimation: we only need the
quantity in a base unit (g / ml / unit) so the cost calculator can
multiply by a per-kg or per-liter price.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Mapping from user-facing unit (fr/en) → (base_unit, grams_or_ml_per_unit)
UNIT_TABLE: dict[str, tuple[str, float]] = {
    "g": ("g", 1),
    "gr": ("g", 1),
    "gramme": ("g", 1),
    "grammes": ("g", 1),
    "kg": ("g", 1000),
    "kilogramme": ("g", 1000),
    "kilogrammes": ("g", 1000),
    "ml": ("ml", 1),
    "cl": ("ml", 10),
    "dl": ("ml", 100),
    "l": ("ml", 1000),
    "litre": ("ml", 1000),
    "litres": ("ml", 1000),
    "cuillère à soupe": ("ml", 15),
    "cuillères à soupe": ("ml", 15),
    "c. à s.": ("ml", 15),
    "cs": ("ml", 15),
    "tbsp": ("ml", 15),
    "cuillère à café": ("ml", 5),
    "cuillères à café": ("ml", 5),
    "c. à c.": ("ml", 5),
    "cc": ("ml", 5),
    "tsp": ("ml", 5),
    "tasse": ("ml", 240),
    "tasses": ("ml", 240),
    "cup": ("ml", 240),
    "cups": ("ml", 240),
    "verre": ("ml", 200),
    "verres": ("ml", 200),
    "pincée": ("g", 1),
    "pincées": ("g", 1),
}

# Default per-item weights (grams) for common ingredients sold at the unit.
DEFAULT_UNIT_WEIGHT_G: dict[str, float] = {
    "oignon": 120,
    "oeuf": 50,
    "œuf": 50,
    "gousse d'ail": 5,
    "ail": 5,
    "tomate": 120,
    "pomme de terre": 150,
    "patate": 150,
    "carotte": 80,
    "courgette": 200,
    "aubergine": 250,
    "poivron": 150,
    "citron": 80,
    "orange": 150,
    "pomme": 150,
    "banane": 120,
    "poulet": 1200,
    "lapin": 1500,
}

_STOP_WORDS = {
    "haché",
    "hachée",
    "coupé",
    "coupée",
    "émincé",
    "émincée",
    "râpé",
    "râpée",
    "frais",
    "fraîche",
    "fraîches",
    "cru",
    "crue",
    "cuit",
    "cuite",
    "au goût",
    "selon",
    "facultatif",
    "optionnel",
    "environ",
}

_UNITS_SORTED = sorted(UNIT_TABLE.keys(), key=len, reverse=True)
_QTY_PATTERN = re.compile(
    r"^(?P<qty>\d+[\.,]?\d*)\s*"
    r"(?:(?P<unit>" + "|".join(re.escape(u) for u in _UNITS_SORTED) + r")\b)?\s*"
    r"(?:de |d'|du |des |of )?\s*"
    r"(?P<food>.+)$",
    re.IGNORECASE,
)


@dataclass
class ParsedIngredient:
    """Result of parsing a free-form ingredient line."""

    raw_text: str
    food_name: str
    quantity: float
    unit: str  # "g", "ml", or "unit"


def _clean_food_name(text: str) -> str:
    words = [w for w in re.split(r"\s+", text.strip(",;")) if w]
    cleaned = [w for w in words if w.lower() not in _STOP_WORDS]
    return " ".join(cleaned).strip().lower()


def parse_ingredient(text: str) -> ParsedIngredient:
    """Parse ingredient text into canonical (name, qty, unit).

    Priority:
      1. Explicit quantity + unit (e.g. "200g de poulet").
      2. Integer count with a known unit-weight food ("2 oignons").
      3. DEFAULT_UNIT_WEIGHT_G lookup on the food name.
      4. Fallback: qty=1, unit="unit".
    """
    text = (text or "").strip()
    if not text:
        return ParsedIngredient(raw_text=text, food_name="", quantity=0.0, unit="unit")

    match = _QTY_PATTERN.match(text)
    if match:
        qty = float(match.group("qty").replace(",", "."))
        unit_raw = (match.group("unit") or "").lower().strip()
        food = _clean_food_name(match.group("food"))

        if unit_raw:
            base_unit, factor = UNIT_TABLE[unit_raw]
            return ParsedIngredient(
                raw_text=text,
                food_name=food,
                quantity=round(qty * factor, 2),
                unit=base_unit,
            )

        # No unit: try food-specific default weight
        unit_weight = _lookup_unit_weight(food)
        if unit_weight is not None:
            return ParsedIngredient(
                raw_text=text,
                food_name=food,
                quantity=round(qty * unit_weight, 2),
                unit="g",
            )

        return ParsedIngredient(raw_text=text, food_name=food, quantity=qty, unit="unit")

    food = _clean_food_name(text)
    unit_weight = _lookup_unit_weight(food)
    if unit_weight is not None:
        return ParsedIngredient(raw_text=text, food_name=food, quantity=unit_weight, unit="g")
    return ParsedIngredient(raw_text=text, food_name=food, quantity=1.0, unit="unit")


def _lookup_unit_weight(food: str) -> Optional[float]:
    if not food:
        return None
    for key, weight in DEFAULT_UNIT_WEIGHT_G.items():
        if key in food:
            return weight
    return None
