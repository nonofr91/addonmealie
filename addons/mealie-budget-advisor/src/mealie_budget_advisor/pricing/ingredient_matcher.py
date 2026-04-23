"""Match parsed ingredient names to priced products.

Strategy:
  1. Look up the manual pricer (exact + substring match on normalized name).
  2. Fallback to Open Prices search by product name.

Prices are always normalized to the parsed ingredient's base unit:
  * g     → price per gram
  * ml    → price per milliliter
  * unit  → price per piece

Manual prices are expected to be expressed per kg / per liter / per piece.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from ..models.pricing import ManualPrice, PriceSource
from .manual_pricer import ManualPricer
from .open_prices_client import OpenPricesClient

logger = logging.getLogger(__name__)


@dataclass
class MatchedPrice:
    """Resolved unit price for a given ingredient name."""

    ingredient_name: str
    price_per_unit_base: float  # per g / ml / unit depending on `base_unit`
    base_unit: str
    source: PriceSource
    currency: str = "EUR"


# Coarse fallback estimates when no source has data, in € per kg or per unit.
# Kept intentionally small and neutral so relative ordering stays meaningful.
_FALLBACK_ESTIMATES: dict[str, tuple[float, str]] = {
    "poulet": (8.0, "kg"),
    "bœuf": (15.0, "kg"),
    "boeuf": (15.0, "kg"),
    "porc": (10.0, "kg"),
    "agneau": (18.0, "kg"),
    "saumon": (20.0, "kg"),
    "cabillaud": (18.0, "kg"),
    "thon": (15.0, "kg"),
    "œuf": (0.3, "unit"),
    "oeuf": (0.3, "unit"),
    "riz": (2.5, "kg"),
    "pâtes": (2.0, "kg"),
    "pates": (2.0, "kg"),
    "lentilles": (3.5, "kg"),
    "pois chiches": (3.0, "kg"),
    "haricots": (3.0, "kg"),
    "oignon": (2.0, "kg"),
    "ail": (10.0, "kg"),
    "tomate": (3.0, "kg"),
    "carotte": (1.5, "kg"),
    "pomme de terre": (1.2, "kg"),
    "courgette": (2.5, "kg"),
    "aubergine": (3.0, "kg"),
    "poivron": (3.5, "kg"),
    "salade": (2.5, "kg"),
    "citron": (3.0, "kg"),
    "pomme": (2.5, "kg"),
    "banane": (2.0, "kg"),
    "lait": (1.2, "l"),
    "beurre": (10.0, "kg"),
    "huile": (5.0, "l"),
    "farine": (1.5, "kg"),
    "sucre": (1.5, "kg"),
    "pain": (4.0, "kg"),
    "fromage": (15.0, "kg"),
    "yaourt": (3.0, "kg"),
}


def _bulk_unit_to_base(unit: str) -> tuple[str, float]:
    """Convert a bulk pricing unit (kg, l, unit) to a base unit + divider.

    Returns (base_unit, divisor) where price_per_base = bulk_price / divisor.
    """
    unit = unit.strip().lower()
    if unit in {"kg", "kilogramme", "kilogrammes"}:
        return "g", 1000.0
    if unit == "g":
        return "g", 1.0
    if unit in {"l", "litre", "litres"}:
        return "ml", 1000.0
    if unit == "ml":
        return "ml", 1.0
    return "unit", 1.0


def _manual_to_match(price: ManualPrice) -> MatchedPrice:
    base_unit, divisor = _bulk_unit_to_base(price.unit)
    return MatchedPrice(
        ingredient_name=price.ingredient_name,
        price_per_unit_base=price.price_per_unit / divisor if divisor else 0.0,
        base_unit=base_unit,
        source=PriceSource.manual,
        currency=price.currency,
    )


class IngredientMatcher:
    """Resolve a unit price for a normalized ingredient name."""

    def __init__(
        self,
        manual_pricer: ManualPricer,
        open_prices: Optional[OpenPricesClient] = None,
        enable_open_prices: bool = True,
    ) -> None:
        self.manual_pricer = manual_pricer
        self.open_prices = open_prices
        self.enable_open_prices = enable_open_prices and open_prices is not None

    def match(self, food_name: str, parsed_base_unit: str) -> Optional[MatchedPrice]:
        """Resolve a price for `food_name`, normalized to `parsed_base_unit`."""
        if not food_name:
            return None

        # 1. Manual pricer — exact then substring.
        manual = self.manual_pricer.get(food_name)
        if manual is None:
            for candidate in self.manual_pricer.list():
                if candidate.ingredient_name in food_name or food_name in candidate.ingredient_name:
                    manual = candidate
                    break

        if manual is not None:
            match = _manual_to_match(manual)
            if _compatible(match.base_unit, parsed_base_unit):
                return match

        # 2. Open Prices API fallback.
        if self.enable_open_prices and self.open_prices is not None:
            prices = self.open_prices.search_by_name(food_name, size=8)
            median = self.open_prices.median_price(prices)
            if median is not None and prices:
                # Open Prices returns a product-level price; treat it as "per unit" unless
                # we can parse a richer signal. That's intentionally coarse — the addon is
                # for assistance, not accounting. Callers should prefer manual prices for
                # ingredients sold in bulk.
                return MatchedPrice(
                    ingredient_name=food_name,
                    price_per_unit_base=median,
                    base_unit="unit",
                    source=PriceSource.open_prices,
                    currency=prices[0].currency,
                )

        # 3. Static fallback estimate.
        fallback = _fallback_estimate(food_name)
        if fallback is not None:
            bulk_price, bulk_unit = fallback
            base_unit, divisor = _bulk_unit_to_base(bulk_unit)
            if _compatible(base_unit, parsed_base_unit):
                return MatchedPrice(
                    ingredient_name=food_name,
                    price_per_unit_base=bulk_price / divisor if divisor else 0.0,
                    base_unit=base_unit,
                    source=PriceSource.estimated,
                )
        return None


def _compatible(resolved_unit: str, parsed_unit: str) -> bool:
    """Relax compatibility: g↔ml treated as equivalent (density≈1 assumption)."""
    if resolved_unit == parsed_unit:
        return True
    liquids = {"g", "ml"}
    if resolved_unit in liquids and parsed_unit in liquids:
        return True
    if resolved_unit == "unit" or parsed_unit == "unit":
        # "unit" acts as a last-resort bridge; use with a low confidence signal.
        return True
    return False


def _fallback_estimate(food: str) -> Optional[tuple[float, str]]:
    food = food.lower()
    for key, value in _FALLBACK_ESTIMATES.items():
        if key in food:
            return value
    return None
