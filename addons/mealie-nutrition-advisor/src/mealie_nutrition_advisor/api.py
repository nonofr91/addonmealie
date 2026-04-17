"""FastAPI REST API for mealie-nutrition-advisor addon."""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from .config import NutritionConfig, NutritionConfigError
from .orchestrator import NutritionOrchestrator, NutritionOrchestratorError

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Mealie Nutrition Advisor",
    description="Calculateur nutritionnel et enrichissement de recettes pour Mealie.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Auth (optional) — token via X-Addon-Key header
# ---------------------------------------------------------------------------

_API_KEY_HEADER = APIKeyHeader(name="X-Addon-Key", auto_error=False)


def _check_key(key: str | None = Security(_API_KEY_HEADER)) -> None:
    required = os.environ.get("ADDON_SECRET_KEY")
    if required and key != required:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")


# ---------------------------------------------------------------------------
# Lazy singletons
# ---------------------------------------------------------------------------

_orchestrator: NutritionOrchestrator | None = None


def _get_orchestrator() -> NutritionOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        try:
            _orchestrator = NutritionOrchestrator()
        except NutritionConfigError as exc:
            raise HTTPException(status_code=503, detail=f"Addon misconfigured: {exc}") from exc
    return _orchestrator


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class EnrichRequest(BaseModel):
    force: bool = False


class RecipeEnrichRequest(BaseModel):
    slug: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status", tags=["system"])
def get_status(_: None = Security(_check_key)) -> dict[str, Any]:
    """Get status of nutrition addon."""
    orch = _get_orchestrator()
    try:
        return orch.get_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/nutrition/scan", tags=["nutrition"])
def scan_recipes(_: None = Security(_check_key)) -> dict[str, Any]:
    """Scan Mealie recipes to find those without nutrition data."""
    orch = _get_orchestrator()
    try:
        return orch.scan_recipes()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/nutrition/enrich", tags=["nutrition"])
def enrich_recipes(req: EnrichRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    """Enrich all recipes without nutrition (or all if force=True)."""
    orch = _get_orchestrator()
    try:
        return orch.enrich_all(force=req.force)
    except NutritionOrchestratorError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/nutrition/recipe/{slug}", tags=["nutrition"])
def enrich_recipe(slug: str, _: None = Security(_check_key)) -> dict[str, Any]:
    """Enrich a single recipe by slug."""
    orch = _get_orchestrator()
    try:
        return orch.enrich_recipe(slug)
    except NutritionOrchestratorError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Entrypoint for script / uvicorn
# ---------------------------------------------------------------------------


def start() -> None:
    import uvicorn

    config = NutritionConfig()
    uvicorn.run(
        "mealie_nutrition_advisor.api:app",
        host=config.api_host,
        port=config.api_port,
        reload=False,
    )
