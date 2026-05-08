import csv
import io
from datetime import date
from typing import Any

from pydantic import ValidationError

from .models import ImportResult, PriceObservationCreate
from .normalizer import normalize_observation


def import_observations_from_dicts(rows: list[dict[str, Any]]) -> ImportResult:
    observations = []
    errors = []

    for index, row in enumerate(rows, start=1):
        try:
            candidate = PriceObservationCreate(**_normalize_row(row))
            observations.append(normalize_observation(candidate))
        except (ValidationError, ValueError, TypeError) as exc:
            errors.append(f"row {index}: {exc}")

    return ImportResult(imported=len(observations), rejected=len(errors), observations=observations, errors=errors)


def import_observations_from_csv(content: bytes) -> ImportResult:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return import_observations_from_dicts(list(reader))


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    aliases = {
        "ingredient": "ingredient_name",
        "product": "product_name",
        "price": "price_amount",
        "quantity": "package_quantity",
        "unit": "package_unit",
        "store": "store_name",
        "date": "observed_at",
    }
    for source, target in aliases.items():
        if source in normalized and target not in normalized:
            normalized[target] = normalized[source]

    if not normalized.get("observed_at"):
        normalized["observed_at"] = date.today().isoformat()
    if not normalized.get("currency"):
        normalized["currency"] = "EUR"
    if not normalized.get("source"):
        normalized["source"] = "manual_import"

    return normalized
