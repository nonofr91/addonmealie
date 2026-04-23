"""FastAPI REST API pour le Budget Advisor."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import BudgetConfigError, get_config
from .mealie_sync import MealieClient
from .models.budget import BudgetPeriod, BudgetSettings
from .planning.budget_manager import BudgetManager
from .pricing.cost_calculator import CostCalculator
from .pricing.manual_pricer import ManualPricer

config = get_config()
mealie_client = MealieClient(config.mealie_base_url, config.mealie_api_key)
cost_calculator = CostCalculator(
    config.mealie_base_url,
    config.mealie_api_key,
)
manual_pricer = ManualPricer()
budget_manager = BudgetManager(config_dir=config.config_dir)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler pour startup/shutdown."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Mealie Budget Advisor",
    description="Estimation des coûts et assistance au choix des recettes selon le budget",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "mealie-budget-advisor"}


@app.get("/status")
async def get_status():
    """Statut des connexions et configuration."""
    mealie_status = mealie_client.health_check()

    # Compter les recettes
    recipes = mealie_client.get_all_recipes(limit=1)
    total_recipes = len(recipes)

    # Compter les prix manuels
    price_stats = manual_pricer.get_coverage_stats()

    return {
        "success": True,
        "version": "0.1.0",
        "mealie_connected": mealie_status.get("connected", False),
        "mealie_version": mealie_status.get("version", "unknown"),
        "total_recipes": total_recipes,
        "manual_prices_count": price_stats.get("total_ingredients", 0),
        "open_prices_enabled": config.enable_open_prices,
        "config": config.to_dict(),
    }


@app.get("/budget")
async def get_current_budget():
    """Récupère le budget du mois en cours."""
    budget = budget_manager.get_current_budget()

    if budget:
        return {
            "success": True,
            "period": budget.period.period_label,
            "budget": budget.model_dump(),
        }

    return {
        "success": True,
        "period": BudgetPeriod.current().period_label,
        "budget": None,
        "message": "Aucun budget défini pour cette période",
    }


@app.post("/budget")
async def set_budget(settings: BudgetSettings):
    """Définit le budget pour une période."""
    budget = budget_manager.set_budget(settings)

    return {
        "success": True,
        "period": budget.period.period_label,
        "effective_budget": budget.effective_budget,
        "budget_per_meal": budget.budget_per_meal,
        "budget": budget.model_dump(),
    }


@app.get("/budget/period/{period_label}")
async def get_budget_by_period(period_label: str):
    """Récupère le budget pour une période spécifique."""
    try:
        period = BudgetPeriod.from_string(period_label)
        budget = budget_manager.get_budget(period)

        if budget:
            return {
                "success": True,
                "period": period_label,
                "budget": budget.model_dump(),
            }

        raise HTTPException(status_code=404, detail=f"Budget non trouvé pour {period_label}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Format de période invalide: {e}")


@app.delete("/budget/period/{period_label}")
async def delete_budget_by_period(period_label: str):
    """Supprime le budget pour une période."""
    try:
        period = BudgetPeriod.from_string(period_label)
        deleted = budget_manager.delete_budget(period)

        if deleted:
            return {"success": True, "period": period_label, "message": "Budget supprimé"}

        raise HTTPException(status_code=404, detail=f"Budget non trouvé pour {period_label}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Format de période invalide: {e}")


@app.get("/budget/list")
async def list_budgets():
    """Liste tous les budgets sauvegardés."""
    budgets = budget_manager.list_budgets()

    return {
        "success": True,
        "count": len(budgets),
        "budgets": [b.model_dump() for b in budgets],
    }


@app.get("/prices/search")
async def search_prices(
    q: str = Query(..., description="Terme de recherche"),
    limit: int = Query(10, ge=1, le=50),
):
    """Recherche des prix via Open Prices."""
    if not config.enable_open_prices:
        raise HTTPException(status_code=503, detail="Open Prices désactivé")

    from .pricing.open_prices_client import OpenPricesClient

    client = OpenPricesClient(config.open_prices_base_url)
    prices = client.search_prices(q, limit=limit)

    return {
        "success": True,
        "query": q,
        "count": len(prices),
        "prices": [p.model_dump() for p in prices],
    }


@app.get("/prices/manual")
async def list_manual_prices(search: str = ""):
    """Liste les prix manuels."""
    prices = manual_pricer.list_prices(search if search else None)

    return {
        "success": True,
        "count": len(prices),
        "prices": [p.model_dump() for p in prices],
    }


@app.post("/prices/manual")
async def add_manual_price(
    ingredient_name: str,
    price_per_unit: float,
    unit: str,
    store: str = "",
    location: str = "",
    notes: str = "",
):
    """Ajoute ou met à jour un prix manuel."""
    if not config.enable_manual_prices:
        raise HTTPException(status_code=503, detail="Prix manuels désactivés")

    price = manual_pricer.set_price(
        ingredient_name=ingredient_name,
        price_per_unit=price_per_unit,
        unit=unit,
        store=store or None,
        location=location or None,
        notes=notes or None,
    )

    return {
        "success": True,
        "price": price.model_dump(),
    }


@app.get("/recipes/{slug}/cost")
async def get_recipe_cost(
    slug: str,
    use_open_prices: bool = True,
):
    """Calcule le coût d'une recette."""
    cost = cost_calculator.calculate_cost(slug, use_open_prices=use_open_prices)

    if not cost:
        raise HTTPException(status_code=404, detail=f"Recette {slug} non trouvée")

    return {
        "success": True,
        "cost": cost.model_dump(),
    }


@app.post("/recipes/batch-cost")
async def batch_recipe_costs(
    slugs: list[str],
    use_open_prices: bool = True,
):
    """Calcule les coûts pour plusieurs recettes."""
    costs = cost_calculator.calculate_batch_costs(slugs, use_open_prices)

    return {
        "success": True,
        "count": len(costs),
        "costs": [c.model_dump() for c in costs],
    }


@app.get("/recipes/compare-costs")
async def compare_recipe_costs(
    slugs: list[str] = Query(..., description="Liste des slugs à comparer"),
    per_serving: bool = True,
):
    """Compare le coût de plusieurs recettes."""
    sorted_costs = cost_calculator.compare_recipes_by_cost(slugs, per_serving)

    return {
        "success": True,
        "comparison": [
            {"slug": slug, "cost": cost, "per_serving": per_serving}
            for slug, cost in sorted_costs
        ],
    }
