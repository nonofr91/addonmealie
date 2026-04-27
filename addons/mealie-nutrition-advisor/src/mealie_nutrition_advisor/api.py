"""FastAPI REST API for mealie-nutrition-advisor addon."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from .api_routes import menu_drafting_router
from .config import NutritionConfig, NutritionConfigError
from .models.profile import HouseholdProfile, MemberProfile, WeeklyPresencePattern
from .orchestrator import NutritionOrchestrator, NutritionOrchestratorError
from .profiles.manager import ProfileManager

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan — setup fake recipe at startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create placeholder recipe + Addon cookbook (best-effort)."""
    try:
        from .setup import MealieSetup

        base_url = os.environ.get("MEALIE_BASE_URL", "")
        api_key = os.environ.get("MEALIE_API_KEY", "")
        if base_url and api_key:
            setup = MealieSetup(base_url, api_key)
            result = setup.setup()
            _logger.info("Addon setup: %s", result.get("status"))
    except Exception:  # noqa: BLE001
        _logger.exception("Addon setup failed (non-critical)")
    yield


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Mealie Nutrition Advisor",
    description="Calculateur nutritionnel et enrichissement de recettes pour Mealie.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include menu drafting router
app.include_router(menu_drafting_router)

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
_profile_manager: ProfileManager | None = None
_config: NutritionConfig | None = None


def _get_config() -> NutritionConfig:
    global _config
    if _config is None:
        _config = NutritionConfig()
    return _config


def _get_orchestrator() -> NutritionOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        try:
            _orchestrator = NutritionOrchestrator()
        except NutritionConfigError as exc:
            raise HTTPException(status_code=503, detail=f"Addon misconfigured: {exc}") from exc
    return _orchestrator


def _get_profile_manager() -> ProfileManager:
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class EnrichRequest(BaseModel):
    force: bool = False


class RecipeEnrichRequest(BaseModel):
    slug: str


class ProfileCreateRequest(BaseModel):
    member: MemberProfile


class ProfileUpdateRequest(BaseModel):
    member: MemberProfile


class PresenceUpdateRequest(BaseModel):
    presence: WeeklyPresencePattern


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
        raise HTTPException(status_code=500, detail="Internal server error getting status") from exc


@app.get("/nutrition/scan", tags=["nutrition"])
def scan_recipes(_: None = Security(_check_key)) -> dict[str, Any]:
    """Scan Mealie recipes to find those without nutrition data."""
    config = _get_config()
    if not config.enable_nutrition_analysis:
        raise HTTPException(status_code=503, detail="Nutrition analysis feature is disabled")
    orch = _get_orchestrator()
    try:
        return orch.scan_recipes()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error during nutrition scan") from exc


@app.post("/nutrition/enrich", tags=["nutrition"])
def enrich_recipes(req: EnrichRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    """Enrich all recipes without nutrition (or all if force=True)."""
    config = _get_config()
    if not config.enable_nutrition_analysis:
        raise HTTPException(status_code=503, detail="Nutrition analysis feature is disabled")
    orch = _get_orchestrator()
    try:
        return orch.enrich_all(force=req.force)
    except NutritionOrchestratorError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error during nutrition enrichment") from exc


@app.post("/nutrition/recipe/{slug}", tags=["nutrition"])
def enrich_recipe(slug: str, _: None = Security(_check_key)) -> dict[str, Any]:
    """Enrich a single recipe by slug."""
    config = _get_config()
    if not config.enable_nutrition_analysis:
        raise HTTPException(status_code=503, detail="Nutrition analysis feature is disabled")
    orch = _get_orchestrator()
    try:
        return orch.enrich_recipe(slug)
    except NutritionOrchestratorError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error during nutrition enrichment") from exc


@app.get("/profiles", tags=["profiles"])
def get_profiles(_: None = Security(_check_key)) -> dict[str, Any]:
    """List all household profiles."""
    config = _get_config()
    if not config.enable_profile_ui:
        raise HTTPException(status_code=503, detail="Profile UI feature is disabled")
    pm = _get_profile_manager()
    try:
        household = pm.household
        return {
            "success": True,
            "household_name": household.household_name,
            "members": [m.model_dump() for m in household.members],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error getting profiles") from exc


@app.get("/profiles/{name}", tags=["profiles"])
def get_profile(name: str, _: None = Security(_check_key)) -> dict[str, Any]:
    """Get a specific member profile by name."""
    config = _get_config()
    if not config.enable_profile_ui:
        raise HTTPException(status_code=503, detail="Profile UI feature is disabled")
    pm = _get_profile_manager()
    try:
        member = pm.get_member(name)
        if not member:
            raise HTTPException(status_code=404, detail=f"Member '{name}' not found")
        return {"success": True, "member": member.model_dump()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error getting profile") from exc


@app.post("/profiles", tags=["profiles"])
def create_profile(req: ProfileCreateRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    """Create a new member profile."""
    config = _get_config()
    if not config.enable_profile_ui:
        raise HTTPException(status_code=503, detail="Profile UI feature is disabled")
    pm = _get_profile_manager()
    try:
        pm.add_member(req.member)
        return {"success": True, "member": req.member.model_dump()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error creating profile") from exc


@app.put("/profiles/{name}", tags=["profiles"])
def update_profile(name: str, req: ProfileUpdateRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    """Update an existing member profile."""
    config = _get_config()
    if not config.enable_profile_ui:
        raise HTTPException(status_code=503, detail="Profile UI feature is disabled")
    pm = _get_profile_manager()
    try:
        existing = pm.get_member(name)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Member '{name}' not found")
        pm.add_member(req.member)
        return {"success": True, "member": req.member.model_dump()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error updating profile") from exc


@app.delete("/profiles/{name}", tags=["profiles"])
def delete_profile(name: str, _: None = Security(_check_key)) -> dict[str, Any]:
    """Delete a member profile."""
    config = _get_config()
    if not config.enable_profile_ui:
        raise HTTPException(status_code=503, detail="Profile UI feature is disabled")
    pm = _get_profile_manager()
    try:
        deleted = pm.remove_member(name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Member '{name}' not found")
        return {"success": True, "deleted": name}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error deleting profile") from exc


@app.post("/profiles/{name}/presence", tags=["profiles"])
def update_presence(name: str, req: PresenceUpdateRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    """Update the weekly presence pattern for a member."""
    config = _get_config()
    if not config.enable_profile_ui:
        raise HTTPException(status_code=503, detail="Profile UI feature is disabled")
    pm = _get_profile_manager()
    try:
        pm.set_weekly_presence(name, req.presence)
        return {"success": True, "presence": req.presence.model_dump()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Internal server error updating presence") from exc


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
