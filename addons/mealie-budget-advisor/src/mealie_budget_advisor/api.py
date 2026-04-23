"""FastAPI REST API for the mealie-budget-advisor addon."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field

from .config import BudgetConfigError
from .models.budget import BudgetSettings
from .models.pricing import ManualPrice
from .orchestrator import BudgetOrchestrator, BudgetOrchestratorError
from .scheduler import BudgetScheduler

logger = logging.getLogger(__name__)

_scheduler: BudgetScheduler | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Démarre / arrête le planificateur avec le cycle de vie FastAPI."""
    global _scheduler
    try:
        orch = _get_orchestrator()
    except HTTPException as exc:  # addon misconfigured -> pas de cron
        logger.warning("Planificateur non démarré: %s", exc.detail)
    else:
        _scheduler = BudgetScheduler(orch, orch.config)
        _scheduler.start()
    yield
    if _scheduler is not None:
        _scheduler.stop()


app = FastAPI(
    title="Mealie Budget Advisor",
    description="Estimation de coût des recettes et planification respectant un budget mensuel.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_API_KEY_HEADER = APIKeyHeader(name="X-Addon-Key", auto_error=False)


def _check_key(key: str | None = Security(_API_KEY_HEADER)) -> None:
    required = os.environ.get("ADDON_SECRET_KEY")
    if required and key != required:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")


_orchestrator: BudgetOrchestrator | None = None


def _get_orchestrator() -> BudgetOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        try:
            _orchestrator = BudgetOrchestrator()
        except BudgetConfigError as exc:
            raise HTTPException(status_code=503, detail=f"Addon misconfigured: {exc}") from exc
    return _orchestrator


# --------------------------------------------------------------------- schemas


class BudgetUpsertRequest(BaseModel):
    settings: BudgetSettings


class ManualPriceRequest(BaseModel):
    price: ManualPrice


class BatchCostRequest(BaseModel):
    slugs: list[str] = Field(..., min_length=1)


class BudgetPlanRequest(BaseModel):
    month: Optional[str] = None
    meals_target: Optional[int] = Field(None, ge=1, le=200)
    candidate_slugs: Optional[list[str]] = None


class RefreshCostsRequest(BaseModel):
    month: Optional[str] = None


# -------------------------------------------------------------------- endpoints


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/status", tags=["system"])
def get_status(_: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    try:
        return orch.get_status()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Status failed: {exc}") from exc


# ------------------------------------------------------------------- budget


@app.get("/budget", tags=["budget"])
def get_budget(month: Optional[str] = None, _: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    settings = orch.get_budget(month)
    return {
        "success": True,
        "settings": settings.model_dump(),
        "budget_per_meal": round(settings.budget_per_meal, 2),
        "budget_per_day": round(settings.budget_per_day, 2),
        "effective_budget": round(settings.effective_budget, 2),
    }


@app.post("/budget", tags=["budget"])
def set_budget(req: BudgetUpsertRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    saved = orch.set_budget(req.settings)
    return {"success": True, "settings": saved.model_dump()}


# ------------------------------------------------------------------- prices


@app.get("/prices/manual", tags=["prices"])
def list_manual_prices(_: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    return {"success": True, "items": [p.model_dump(mode="json") for p in orch.manual_pricer.list()]}


@app.post("/prices/manual", tags=["prices"])
def upsert_manual_price(req: ManualPriceRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    saved = orch.manual_pricer.upsert(req.price)
    return {"success": True, "price": saved.model_dump(mode="json")}


@app.delete("/prices/manual/{name}", tags=["prices"])
def delete_manual_price(name: str, _: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    deleted = orch.manual_pricer.delete(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Prix manuel introuvable: {name}")
    return {"success": True, "deleted": name}


@app.get("/prices/search", tags=["prices"])
def search_open_prices(q: str, size: int = 10, _: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    if not orch.config.enable_open_prices or orch.matcher.open_prices is None:
        raise HTTPException(status_code=503, detail="Open Prices disabled")
    prices = orch.matcher.open_prices.search_by_name(q, size=size)
    return {
        "success": True,
        "query": q,
        "items": [p.model_dump(mode="json") for p in prices],
        "median": orch.matcher.open_prices.median_price(prices),
    }


# ------------------------------------------------------------------- recipes


@app.get("/recipes/{slug}/cost", tags=["recipes"])
def recipe_cost(slug: str, _: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    try:
        cost = orch.cost_recipe(slug)
    except BudgetOrchestratorError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Cost computation failed: {exc}") from exc
    return {"success": True, "cost": cost.model_dump(mode="json")}


@app.post("/recipes/batch-cost", tags=["recipes"])
def recipes_batch_cost(req: BatchCostRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    try:
        costs = orch.batch_cost(req.slugs)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Batch cost failed: {exc}") from exc
    return {"success": True, "items": [c.model_dump(mode="json") for c in costs]}


@app.post("/recipes/{slug}/sync-cost", tags=["recipes"])
def sync_recipe_cost(
    slug: str,
    month: Optional[str] = None,
    _: None = Security(_check_key),
) -> dict[str, Any]:
    """Recalcule le coût d'une recette et publie ``cout_*`` dans ses extras Mealie."""
    orch = _get_orchestrator()
    try:
        return {"success": True, **orch.sync_recipe_cost(slug, month=month)}
    except BudgetOrchestratorError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Sync cost failed: {exc}") from exc


@app.post("/recipes/refresh-costs", tags=["recipes"])
def refresh_all_recipe_costs(
    req: RefreshCostsRequest,
    _: None = Security(_check_key),
) -> dict[str, Any]:
    """Recalcule et publie le coût de TOUTES les recettes dans Mealie."""
    orch = _get_orchestrator()
    try:
        report = orch.refresh_all_costs(month=req.month)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Refresh costs failed: {exc}") from exc
    return {"success": True, "report": report}


# ------------------------------------------------------------------- planning


@app.post("/plan/budget-aware", tags=["planning"])
def plan_budget_aware(req: BudgetPlanRequest, _: None = Security(_check_key)) -> dict[str, Any]:
    orch = _get_orchestrator()
    try:
        report = orch.plan_budget_aware(
            month=req.month,
            meals_target=req.meals_target,
            candidate_slugs=req.candidate_slugs,
        )
    except BudgetOrchestratorError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Planning failed: {exc}") from exc
    return {"success": True, "report": report.model_dump(mode="json")}
