import json
import re
import unicodedata
from pathlib import Path

from .models import PriceObservation, PriceObservationCreate


_MASS_FACTORS_TO_KG = {
    "kg": 1.0,
    "kilogram": 1.0,
    "kilograms": 1.0,
    "g": 0.001,
    "gram": 0.001,
    "grams": 0.001,
}

_VOLUME_FACTORS_TO_L = {
    "l": 1.0,
    "liter": 1.0,
    "liters": 1.0,
    "litre": 1.0,
    "litres": 1.0,
    "ml": 0.001,
    "cl": 0.01,
}

_PIECE_UNITS = {"piece", "pieces", "unit", "units", "unite", "unites", "pc", "pcs"}

_PRICE_BOUNDS: dict[str, dict[str, float]] = {}


def _load_price_bounds() -> None:
    global _PRICE_BOUNDS
    if _PRICE_BOUNDS:
        return

    bounds_path = Path(__file__).parent.parent.parent / "data" / "price_bounds.json"
    try:
        with open(bounds_path, "r", encoding="utf-8") as f:
            _PRICE_BOUNDS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _PRICE_BOUNDS = {}


def normalize_ingredient_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    compacted = re.sub(r"[^a-z0-9]+", " ", without_accents).strip()
    if compacted.endswith("s") and len(compacted) > 3:
        compacted = compacted[:-1]
    return compacted


def normalize_observation(observation: PriceObservationCreate) -> PriceObservation:
    _load_price_bounds()
    unit = observation.package_unit
    quantity = observation.package_quantity
    price = observation.price_amount
    price_per_kg = None
    price_per_l = None
    price_per_piece = None
    quality_flags: list[str] = []

    if unit in _MASS_FACTORS_TO_KG:
        kg_quantity = quantity * _MASS_FACTORS_TO_KG[unit]
        price_per_kg = round(price / kg_quantity, 4)
    elif unit in _VOLUME_FACTORS_TO_L:
        l_quantity = quantity * _VOLUME_FACTORS_TO_L[unit]
        price_per_l = round(price / l_quantity, 4)
    elif unit in _PIECE_UNITS:
        price_per_piece = round(price / quantity, 4)
    else:
        quality_flags.append("unsupported_unit")

    if observation.source.value == "ai_estimate" and (
        observation.confidence is None or observation.confidence > 0.5
    ):
        quality_flags.append("ai_estimate_confidence_capped")

    confidence = observation.confidence
    if confidence is None:
        confidence = _default_confidence(observation.source.value, quality_flags)
    if observation.source.value == "ai_estimate":
        confidence = min(confidence, 0.5)

    if price_per_kg is not None and (price_per_kg <= 0 or price_per_kg > 100):
        quality_flags.append("price_per_kg_outlier")
    if price_per_l is not None and (price_per_l <= 0 or price_per_l > 100):
        quality_flags.append("price_per_l_outlier")
    if price_per_piece is not None and (price_per_piece <= 0 or price_per_piece > 50):
        quality_flags.append("price_per_piece_outlier")

    normalized_ingredient = normalize_ingredient_name(observation.ingredient_name)
    category_code = _get_category_code(normalized_ingredient)
    confidence = _adjust_confidence_by_bounds(
        confidence,
        price_per_kg,
        price_per_l,
        category_code,
        quality_flags,
    )

    payload = observation.model_dump()
    payload["confidence"] = confidence
    return PriceObservation(
        **payload,
        normalized_ingredient=normalized_ingredient,
        price_per_kg=price_per_kg,
        price_per_l=price_per_l,
        price_per_piece=price_per_piece,
        quality_flags=quality_flags,
    )


def _default_confidence(source: str, quality_flags: list[str]) -> float:
    if "unsupported_unit" in quality_flags:
        return 0.2
    if source == "manual_import":
        return 0.95
    if source == "open_prices":
        return 0.7
    if source in {"insee_ipc", "rnm_franceagrimer"}:
        return 0.6
    if source == "ai_estimate":
        return 0.5
    return 0.4


_COICOP_MAPPING: dict[str, str] = {}


def _load_coicop_mapping() -> None:
    global _COICOP_MAPPING
    if _COICOP_MAPPING:
        return

    mapping_path = Path(__file__).parent.parent.parent / "data" / "coicop_mapping.json"
    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            _COICOP_MAPPING = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _COICOP_MAPPING = {}


def _get_category_code(normalized_ingredient: str) -> str | None:
    _load_coicop_mapping()
    return _COICOP_MAPPING.get(normalized_ingredient)


def _adjust_confidence_by_bounds(
    confidence: float,
    price_per_kg: float | None,
    price_per_l: float | None,
    category_code: str | None,
    quality_flags: list[str],
) -> float:
    if not category_code or category_code not in _PRICE_BOUNDS:
        return confidence

    bounds = _PRICE_BOUNDS[category_code]
    price = price_per_kg or price_per_l
    if price is None:
        return confidence

    min_price = bounds.get("min_price_per_kg") or bounds.get("min_price_per_l", 0)
    max_price = bounds.get("max_price_per_kg") or bounds.get("max_price_per_l", 1000)

    if price < min_price:
        quality_flags.append("price_below_category_bounds")
        return max(confidence - 0.2, 0.1)
    if price > max_price:
        quality_flags.append("price_above_category_bounds")
        return max(confidence - 0.2, 0.1)

    return confidence
