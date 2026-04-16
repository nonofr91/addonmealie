"""FastAPI REST API for Mealie Import Addon."""
from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, HttpUrl

from .config import AddonConfig, AddonConfigurationError
from .orchestrator import AddonExecutionError, MealieImportOrchestrator

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Mealie Import Addon",
    description="Import de recettes et audit qualité pour Mealie.",
    version="0.2.0",
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

_orchestrator: MealieImportOrchestrator | None = None


def _get_orchestrator() -> MealieImportOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        try:
            _orchestrator = MealieImportOrchestrator()
        except AddonConfigurationError as exc:
            raise HTTPException(status_code=503, detail=f"Addon misconfigured: {exc}") from exc
    return _orchestrator


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ImportRequest(BaseModel):
    url: str


class AuditResponse(BaseModel):
    total: int
    issues: list[dict[str, Any]]
    fixed: list[str] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status", tags=["system"])
def get_status(_: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    try:
        return orch.get_health()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/import", tags=["recipes"])
def import_recipe(req: ImportRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    """Import une recette depuis une URL (Marmiton, 750g, etc.)."""
    orch = _get_orchestrator()
    try:
        result = orch.import_from_url(req.url)
    except (AddonExecutionError, AddonConfigurationError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not result.get("success"):
        raise HTTPException(status_code=422, detail=result.get("error", "Import échoué"))
    return result


@app.get("/audit", tags=["audit"])
def audit_scan(_: None = Security(_check_key)) -> dict[str, Any]:
    """Retourne le rapport d'audit sans corriger."""
    orch = _get_orchestrator()
    try:
        return orch.audit(fix=False)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/audit/fix", tags=["audit"])
def audit_fix(_: None = Security(_check_key)) -> dict[str, Any]:
    """Corrige les problèmes détectés (images manquantes, tags test)."""
    orch = _get_orchestrator()
    try:
        return orch.audit(fix=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Entrypoint for script / uvicorn
# ---------------------------------------------------------------------------


def start() -> None:
    import uvicorn

    uvicorn.run(
        "mealie_import_orchestrator.api:app",
        host=os.environ.get("ADDON_API_HOST", "0.0.0.0"),
        port=int(os.environ.get("ADDON_API_PORT", "8000")),
        reload=False,
    )
