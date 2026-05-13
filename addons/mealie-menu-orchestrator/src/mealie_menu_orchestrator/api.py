"""FastAPI REST API for mealie-menu-orchestrator addon."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from .config import MenuOrchestratorConfig
from .models.menu import Menu, MenuGenerationRequest, MenuQuantitiesUpdate, MenuPushRequest
from .orchestrator import MenuOrchestrator
from .storage import get_storage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("Menu Orchestrator API starting")
    yield
    logger.info("Menu Orchestrator API shutting down")


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Mealie Menu Orchestrator",
    description="Coordinates nutrition and budget for multi-criteria menu planning.",
    version="0.1.0",
    lifespan=lifespan,
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
    required = MenuOrchestratorConfig().addon_secret_key
    if required and key != required:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")


# ---------------------------------------------------------------------------
# Lazy singleton
# ---------------------------------------------------------------------------

_orchestrator: MenuOrchestrator | None = None


def _get_orchestrator() -> MenuOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        config = MenuOrchestratorConfig()
        if not config.enable_menu_generation:
            raise HTTPException(status_code=503, detail="Menu generation feature is disabled")
        _orchestrator = MenuOrchestrator(config)
    return _orchestrator


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ConfigResponse(BaseModel):
    """Configuration response."""
    config: dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/config", tags=["system"])
def get_config(_: None = Security(_check_key)) -> ConfigResponse:
    """Get current configuration."""
    config = MenuOrchestratorConfig()
    return ConfigResponse(config=config.to_dict())


@app.post("/menus/generate", tags=["menus"])
def generate_menu(
    request: MenuGenerationRequest,
    _: None = Security(_check_key),
) -> Menu:
    """Generate a menu for the specified date range."""
    try:
        orchestrator = _get_orchestrator()
        menu = orchestrator.generate_menu(request)
        return menu
    except Exception as exc:
        logger.exception("Error generating menu")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/menus", tags=["menus"])
def list_menus(_: None = Security(_check_key)) -> list[Menu]:
    """List all menus."""
    storage = get_storage()
    return storage.list_all()


@app.get("/menus/{menu_id}", tags=["menus"])
def get_menu(menu_id: str, _: None = Security(_check_key)) -> Menu:
    """Get a specific menu by ID."""
    storage = get_storage()
    menu = storage.get(menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail=f"Menu {menu_id} not found")
    return menu


@app.post("/menus/{menu_id}/quantities", tags=["menus"])
def update_menu_quantities(
    menu_id: str,
    request: MenuQuantitiesUpdate,
    _: None = Security(_check_key),
) -> Menu:
    """Update quantities for a menu."""
    try:
        orchestrator = _get_orchestrator()
        menu = orchestrator.update_quantities(menu_id, request.quantities)
        return menu
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error updating menu quantities")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/menus/{menu_id}/push-to-mealie", tags=["menus"])
def push_menu_to_mealie(
    menu_id: str,
    _: None = Security(_check_key),
) -> dict[str, Any]:
    """Push a menu to Mealie mealplan."""
    try:
        storage = get_storage()
        menu = storage.get(menu_id)
        if not menu:
            raise HTTPException(status_code=404, detail=f"Menu {menu_id} not found")
        
        orchestrator = _get_orchestrator()
        success = orchestrator.push_to_mealie(menu)
        
        return {"success": success, "menu_id": menu_id}
    except Exception as exc:
        logger.exception("Error pushing menu to Mealie")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/menus/push", tags=["menus"])
def push_menu_direct(
    request: MenuPushRequest,
    _: None = Security(_check_key),
) -> dict[str, Any]:
    """Push a menu to Mealie mealplan by menu object (requires menu in storage)."""
    try:
        storage = get_storage()
        menu = storage.get(request.menu_id)
        if not menu:
            raise HTTPException(status_code=404, detail=f"Menu {request.menu_id} not found")
        
        orchestrator = _get_orchestrator()
        success = orchestrator.push_to_mealie(menu)
        
        return {"success": success, "menu_id": request.menu_id}
    except Exception as exc:
        logger.exception("Error pushing menu to Mealie")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Entrypoint for script / uvicorn
# ---------------------------------------------------------------------------


def start() -> None:
    """Start the API server."""
    import uvicorn

    config = MenuOrchestratorConfig()
    uvicorn.run(
        "mealie_menu_orchestrator.api:app",
        host=config.api_host,
        port=config.api_port,
        reload=False,
    )


if __name__ == "__main__":
    start()
