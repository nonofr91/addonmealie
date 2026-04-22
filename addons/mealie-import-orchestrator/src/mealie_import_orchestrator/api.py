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
from .nutrition_orchestrator import NutritionOrchestrator, NutritionOrchestratorError

from .ingredient_cleaner import IngredientCleaner

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
_nutrition_orchestrator: NutritionOrchestrator | None = None


def _get_orchestrator() -> MealieImportOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        try:
            _orchestrator = MealieImportOrchestrator()
        except AddonConfigurationError as exc:
            raise HTTPException(status_code=503, detail=f"Addon misconfigured: {exc}") from exc
    return _orchestrator


def _get_nutrition_orchestrator() -> NutritionOrchestrator:
    global _nutrition_orchestrator
    if _nutrition_orchestrator is None:
        try:
            _nutrition_orchestrator = NutritionOrchestrator()
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Nutrition addon misconfigured: {exc}") from exc
    return _nutrition_orchestrator


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ImportRequest(BaseModel):
    url: str


class AuditResponse(BaseModel):
    total: int
    issues: list[dict[str, Any]]
    fixed: list[str] = []


class EnrichRequest(BaseModel):
    force: bool = False


class IngredientFixRequest(BaseModel):
    food_ids: list[str] | None = None
    update_recipe_units: bool = True  # Met à jour les unités dans les ingrédients de recettes


class RecipeUnitsFixRequest(BaseModel):
    # Clés d'identification stable : "<food_id>|<original_text>".
    # Si None, corrige tous les issues détectés.
    issue_keys: list[str] | None = None


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
        raise HTTPException(status_code=500, detail="Internal server error getting status") from exc


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
        raise HTTPException(status_code=500, detail="Internal server error during audit scan") from exc


@app.post("/audit/fix", tags=["audit"])
def audit_fix(_: None = Security(_check_key)) -> dict[str, Any]:
    """Corrige les problèmes détectés (images manquantes, tags test)."""
    orch = _get_orchestrator()
    try:
        return orch.audit(fix=True)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error during audit fix") from exc


# ---------------------------------------------------------------------------
# Ingredients cleanup endpoints
# ---------------------------------------------------------------------------


@app.get("/ingredients/scan", tags=["ingredients"])
def ingredients_scan(_: None = Security(_check_key)) -> dict[str, Any]:
    """Analyse les foods Mealie et détecte les noms mal formés (sans modifier)."""
    try:
        cleaner = IngredientCleaner()
        report = cleaner.scan()
        return report.to_dict()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur scan ingrédients: {exc}") from exc


@app.post("/ingredients/fix", tags=["ingredients"])
def ingredients_fix(req: IngredientFixRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    """
    Corrige les foods mal formés et met à jour les unités dans les recettes.
    Si food_ids est fourni, ne corrige que ces IDs. Sinon corrige tout.
    update_recipe_units=True : ajoute l'unité extraite aux ingrédients des recettes.
    Sécurité : Mealie met à jour automatiquement les recettes référençant ces foods.
    """
    try:
        cleaner = IngredientCleaner()
        report = cleaner.fix(
            issue_ids=req.food_ids,
            update_recipe_units=req.update_recipe_units
        )
        return report.to_dict()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur correction ingrédients: {exc}") from exc


@app.get("/ingredients/scan-recipe-units", tags=["ingredients"])
def ingredients_scan_recipe_units(_: None = Security(_check_key)) -> dict[str, Any]:
    """
    Analyse les ingrédients de recettes et détecte ceux dont l'unité est manquante
    mais extractible depuis le texte original (ex: '500 g de julienne de légumes').
    Complémentaire à /ingredients/scan qui porte sur les noms de foods.
    """
    try:
        cleaner = IngredientCleaner()
        report = cleaner.scan_recipe_units()
        return report.to_dict()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur scan unités recettes: {exc}") from exc


@app.post("/ingredients/fix-recipe-units", tags=["ingredients"])
def ingredients_fix_recipe_units(
    req: RecipeUnitsFixRequest, _: None = Security(_check_key)
) -> dict[str, Any]:
    """
    Applique les corrections d'unités manquantes dans les ingrédients de recettes.
    Si reference_ids est fourni, ne corrige que ces ingrédients. Sinon corrige tout.
    """
    try:
        cleaner = IngredientCleaner()
        report = cleaner.fix_recipe_units(issue_keys=req.issue_keys)
        return report.to_dict()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur correction unités recettes: {exc}") from exc


# ---------------------------------------------------------------------------
# Nutrition endpoints
# ---------------------------------------------------------------------------


@app.get("/nutrition/scan", tags=["nutrition"])
def nutrition_scan(_: None = Security(_check_key)) -> dict[str, Any]:
    """Scan Mealie recipes to find those without nutrition data."""
    orch = _get_nutrition_orchestrator()
    try:
        return orch.scan_recipes()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error during nutrition scan") from exc


@app.post("/nutrition/enrich", tags=["nutrition"])
def nutrition_enrich(req: EnrichRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    """Enrich all recipes without nutrition (or all if force=True)."""
    orch = _get_nutrition_orchestrator()
    try:
        return orch.enrich_all(force=req.force)
    except NutritionOrchestratorError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error during nutrition enrichment") from exc


@app.post("/nutrition/recipe/{slug}", tags=["nutrition"])
def nutrition_enrich_recipe(slug: str, _: None = Security(_check_key)) -> dict[str, Any]:
    """Enrich a single recipe by slug."""
    orch = _get_nutrition_orchestrator()
    try:
        return orch.enrich_recipe(slug)
    except NutritionOrchestratorError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error during nutrition enrichment") from exc


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
