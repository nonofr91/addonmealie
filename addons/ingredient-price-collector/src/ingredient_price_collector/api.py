import json
import logging
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .collectors.drive import DriveCollector
from .collectors.insee_ipc import InseeIpcCollector
from .collectors.open_prices import OpenPricesCollector
from .config import get_config
from .importers import import_observations_from_csv, import_observations_from_dicts
from .models import ImportResult, PriceObservationCreate, PriceRecommendation
from .normalizer import normalize_ingredient_name, normalize_observation
from .storage import PriceStorage

logger = logging.getLogger(__name__)
config = get_config()
storage = PriceStorage(config.database_path)

app = FastAPI(
    title="Ingredient Price Collector API",
    description="API interne de collecte, normalisation et recherche de prix ingrédients.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "ingredient-price-collector"}


@app.get("/status")
async def get_status() -> dict:
    return {
        "success": True,
        "version": "0.1.0",
        "observations_count": storage.count_observations(),
        "config": config.to_dict(),
    }


@app.post("/prices/import", response_model=ImportResult)
async def import_prices(observations: list[PriceObservationCreate]) -> ImportResult:
    normalized = [normalize_observation(observation) for observation in observations]
    storage.add_observations(normalized)
    return ImportResult(imported=len(normalized), rejected=0, observations=normalized, errors=[])


@app.post("/prices/import/json", response_model=ImportResult)
async def import_prices_json(rows: list[dict]) -> ImportResult:
    result = import_observations_from_dicts(rows)
    storage.add_observations(result.observations)
    return result


@app.post("/prices/import/csv", response_model=ImportResult)
async def import_prices_csv(file: UploadFile = File(...)) -> ImportResult:
    content = await file.read()
    try:
        result = import_observations_from_csv(content)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from exc
    storage.add_observations(result.observations)
    return result


@app.get("/prices/search", response_model=PriceRecommendation)
async def search_price(
    ingredient: Annotated[str, Query(min_length=1)],
    unit: Annotated[str | None, Query(pattern="^(kg|l|piece|unit)$")] = None,
    store: str | None = None,
) -> PriceRecommendation:
    normalized = normalize_ingredient_name(ingredient)
    observations = storage.search(normalized, unit=unit, store=store)
    if not observations:
        return PriceRecommendation(
            ingredient_name=ingredient,
            normalized_ingredient=normalized,
            reason="Aucune observation exploitable trouvée pour cet ingrédient",
            warnings=["price_unknown"],
        )

    best = observations[0]
    recommended_price, recommended_unit = _select_price(best, unit)
    warnings = list(best.quality_flags)
    if recommended_price is None:
        warnings.append("requested_unit_unavailable")

    return PriceRecommendation(
        ingredient_name=ingredient,
        normalized_ingredient=normalized,
        recommended_price=recommended_price,
        recommended_unit=recommended_unit,
        source=best.source.value,
        confidence=best.confidence,
        reason=_build_reason(best),
        observed_at=best.observed_at,
        alternatives=observations[1:5],
        warnings=warnings,
    )


@app.get("/prices/anomalies")
async def list_anomalies(limit: Annotated[int, Query(ge=1, le=500)] = 100) -> dict:
    return {"success": True, "observations": storage.anomalies(limit=limit)}


@app.post("/prices/collect/open_prices", response_model=ImportResult)
async def collect_open_prices(
    ingredient: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    currency: Annotated[str, Query(min_length=3, max_length=3)] = "EUR",
) -> ImportResult:
    collector = OpenPricesCollector()
    raw_observations = collector.search(ingredient, limit=limit, currency=currency)

    if not raw_observations:
        return ImportResult(imported=0, rejected=0, observations=[], errors=["No results from Open Prices"])

    normalized = [normalize_observation(observation) for observation in raw_observations]
    storage.add_observations(normalized)
    return ImportResult(imported=len(normalized), rejected=0, observations=normalized, errors=[])


@app.post("/prices/collect/insee_ipc", response_model=ImportResult)
async def collect_insee_ipc(
    ingredient: Annotated[str, Query(min_length=1)],
    base_price: Annotated[float, Query(gt=0)],
    base_unit: Annotated[str, Query(min_length=1)],
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> ImportResult:
    normalized_ingredient = normalize_ingredient_name(ingredient)
    mapping_path = Path(__file__).parent.parent.parent / "data" / "coicop_mapping.json"

    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return ImportResult(imported=0, rejected=0, observations=[], errors=[f"Mapping file error: {exc}"])

    category_code = mapping.get(normalized_ingredient)
    if not category_code:
        return ImportResult(imported=0, rejected=0, observations=[], errors=["No COICOP category found for ingredient"])

    collector = InseeIpcCollector()
    observation = collector.create_observation_from_index(
        ingredient_name=ingredient,
        category_code=category_code,
        base_price=base_price,
        base_unit=base_unit,
        year=year,
    )

    if not observation:
        return ImportResult(imported=0, rejected=0, observations=[], errors=["INSEE index not found for category"])

    normalized = normalize_observation(observation)
    storage.add_observations([normalized])
    return ImportResult(imported=1, rejected=0, observations=[normalized], errors=[])


@app.post("/prices/collect/drive", response_model=ImportResult)
async def collect_drive(
    ingredient: Annotated[str, Query(min_length=1)],
    store: str | None = None,
) -> ImportResult:
    if not config.enable_drive_scraping:
        return ImportResult(imported=0, rejected=0, observations=[], errors=["Drive scraping is disabled (ENABLE_DRIVE_SCRAPING=false)"])

    collector = DriveCollector(storage)
    raw_observations = collector.collect(ingredient, store=store)

    if not raw_observations:
        return ImportResult(imported=0, rejected=0, observations=[], errors=["No results from drive collector"])

    normalized = [normalize_observation(observation) for observation in raw_observations]
    storage.add_observations(normalized)
    return ImportResult(imported=len(normalized), rejected=0, observations=normalized, errors=[])


def _select_price(observation, requested_unit: str | None) -> tuple[float | None, str | None]:
    if requested_unit == "kg":
        return observation.price_per_kg, "kg"
    if requested_unit == "l":
        return observation.price_per_l, "l"
    if requested_unit in {"piece", "unit"}:
        return observation.price_per_piece, "piece"
    if observation.price_per_kg is not None:
        return observation.price_per_kg, "kg"
    if observation.price_per_l is not None:
        return observation.price_per_l, "l"
    if observation.price_per_piece is not None:
        return observation.price_per_piece, "piece"
    return None, None


def _build_reason(observation) -> str:
    parts = [f"Prix {observation.source.value}"]
    if observation.store_name:
        parts.append(f"observé chez {observation.store_name}")
    if observation.observed_at:
        parts.append(f"le {observation.observed_at.isoformat()}")
    return " ".join(parts)


def main() -> None:
    uvicorn.run(
        "ingredient_price_collector.api:app",
        host=config.api_host,
        port=config.api_port,
        log_level=config.log_level.lower(),
    )
