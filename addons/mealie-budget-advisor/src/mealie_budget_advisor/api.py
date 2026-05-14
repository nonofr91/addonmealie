"""FastAPI REST API pour le Budget Advisor."""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import BudgetConfigError, get_config
from .mealie_sync import MealieClient
from .models.budget import BudgetPeriod, BudgetSettings
from .models.cost import RecipeCost
from .models.pricing import ManualPrice
from .planning.budget_aware_planner import BudgetAwarePlanner
from .planning.budget_manager import BudgetManager
from .pricing.cost_calculator import CostCalculator
from .pricing.manual_pricer import ManualPricer
from .scheduler import BudgetScheduler

logger = logging.getLogger(__name__)

config = get_config()
mealie_client = MealieClient(config.mealie_base_url, config.mealie_api_key)
cost_calculator = CostCalculator(
    config.mealie_base_url,
    config.mealie_api_key,
)
manual_pricer = ManualPricer()
budget_manager = BudgetManager(
    config_dir=config.config_dir,
    use_extras=True,  # Utiliser Mealie extras pour la persistance
    mealie_base_url=config.mealie_base_url,
    mealie_api_key=config.mealie_api_key,
)
budget_planner = BudgetAwarePlanner()
_scheduler: Optional[BudgetScheduler] = None


class RefreshCostsRequest(BaseModel):
    """Corps de requête pour ``POST /recipes/refresh-costs``."""

    month: Optional[str] = Field(
        default=None,
        description="Mois de référence (YYYY-MM). Si absent, utilise le mois courant UTC.",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler pour startup/shutdown (scheduler cron + setup fake recipe)."""
    global _scheduler

    # Setup fake recipe + Addon cookbook (non-blocking, best-effort)
    try:
        from .setup import MealieSetup

        setup = MealieSetup(config.mealie_base_url, config.mealie_api_key)
        result = setup.setup()
        logger.info("Addon setup: %s", result.get("status"))
    except Exception:  # noqa: BLE001
        logger.exception("Addon setup failed (non-critical)")

    if config.enable_monthly_cost_refresh:
        _scheduler = BudgetScheduler(
            refresh_callable=lambda: cost_calculator.refresh_all_costs(),
            cron_expression=config.monthly_cost_refresh_cron,
        )
        try:
            _scheduler.start()
        except Exception:  # noqa: BLE001
            logger.exception("Démarrage du scheduler impossible (continue sans cron)")
    else:
        logger.info(
            "Rafraîchissement mensuel des coûts désactivé (ENABLE_MONTHLY_COST_REFRESH=false)"
        )
    try:
        yield
    finally:
        if _scheduler is not None:
            _scheduler.shutdown()


app = FastAPI(
    title="Mealie Budget Advisor API",
    description="""
    API pour l'estimation des coûts et l'assistance au choix des recettes selon le budget.

    ## Fonctionnalités principales

    - **Calcul des coûts**: Estimation du coût des recettes Mealie
    - **Gestion des prix**: Prix manuels et recherche via Open Prices
    - **Budget**: Définition et suivi du budget mensuel
    - **Planning**: Suggestions d'alternatives respectant le budget

    ## Sources de prix

    1. **Prix manuels**: Configurés par l'utilisateur (priorité)
    2. **Open Prices**: API publique de prix alimentaires
    3. **Estimation**: Basée sur les ingrédients connus
    """,
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
    """Health check endpoint.

    Returns:
        JSON response with service status
    """
    return {"status": "ok", "service": "mealie-budget-advisor"}


@app.get("/status")
async def get_status():
    """Statut des connexions et configuration.

    Returns:
        JSON response with:
        - mealie_connected: Boolean
        - mealie_version: String
        - total_recipes: Integer
        - manual_prices_count: Integer
        - open_prices_enabled: Boolean
        - config: Dict with current configuration
    """
    mealie_status = mealie_client.health_check()

    # Compter les recettes (via pagination metadata, léger)
    total_recipes = mealie_client.get_recipe_count()

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


@app.get("/recipes/list")
async def list_recipes():
    """Liste les recettes Mealie (nom + slug) pour les menus déroulants de l'UI."""
    recipes = mealie_client.get_all_recipes()
    return {
        "success": True,
        "recipes": [
            {"name": r.get("name", r.get("slug", "")), "slug": r.get("slug", "")}
            for r in recipes
            if r.get("slug")
        ],
    }


@app.get("/budget")
async def get_current_budget():
    """Récupère le budget du mois en cours.

    Returns:
        JSON response with:
        - success: Boolean
        - period: String (YYYY-MM)
        - budget: BudgetSettings object or null
        - message: String if no budget defined
    """
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
    """Définit le budget pour une période.

    Args:
        settings: BudgetSettings object with period, total_budget, etc.

    Returns:
        JSON response with:
        - success: Boolean
        - period: String (YYYY-MM)
        - effective_budget: Float
        - budget_per_meal: Float
        - budget: BudgetSettings object
    """
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
    ingredient_name: str = Query(..., description="Nom de l'ingrédient"),
    price_per_unit: float = Query(..., gt=0, description="Prix par unité"),
    unit: str = Query(..., description="Unité (kg, g, l, ml, unit)"),
    store: str = Query("", description="Magasin (optionnel)"),
    location: str = Query("", description="Localisation (optionnel)"),
    notes: str = Query("", description="Notes (optionnel)"),
):
    """Ajoute ou met à jour un prix manuel."""
    if not config.enable_manual_prices:
        raise HTTPException(status_code=503, detail="Prix manuels désactivés")

    manual_price = manual_pricer.set_price(
        ingredient_name=ingredient_name,
        price_per_unit=price_per_unit,
        unit=unit,
        store=store if store else None,
        location=location if location else None,
        notes=notes if notes else None,
    )

    return {
        "success": True,
        "price": manual_price.model_dump(),
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


@app.post("/recipes/{slug}/sync-cost")
async def sync_recipe_cost(
    slug: str,
    month: Optional[str] = Query(
        None, description="Mois de référence au format YYYY-MM. Défaut : mois courant UTC."
    ),
    use_open_prices: bool = True,
):
    """Recalcule le coût d'une recette et le publie dans ``extras`` de Mealie.

    - Les clés utilisateur ``cout_manuel_*`` sont **toujours préservées**.
    - Les autres clés `extras` (autres addons) sont préservées.
    - Si un override manuel est présent, ``cout_source=manuel`` dans le retour.
    """
    result = cost_calculator.sync_recipe_cost(
        slug=slug,
        month=month,
        use_open_prices=use_open_prices,
        mealie_client=mealie_client,
    )
    if not result.get("success"):
        status = 404 if "introuvable" in str(result.get("error", "")) else 502
        raise HTTPException(status_code=status, detail=result.get("error", "Sync échoué"))
    return result


@app.post("/recipes/refresh-costs")
async def refresh_all_recipes_costs(payload: RefreshCostsRequest = Body(default=None)):
    """Recalcule et publie les coûts pour toutes les recettes Mealie.

    Les ``extras.cout_manuel_*`` existants ne sont jamais touchés.
    """
    month = payload.month if payload else None
    summary = cost_calculator.refresh_all_costs(
        month=month,
        mealie_client=mealie_client,
    )
    return {"success": True, "summary": summary}


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


@app.get("/planning/suggest-alternatives")
async def suggest_alternatives(
    current_slug: str = Query(..., description="Slug de la recette actuelle"),
    limit: int = Query(5, ge=1, le=20),
):
    """Suggère des alternatives moins chères respectant le budget.

    Args:
        current_slug: Slug de la recette à remplacer
        limit: Nombre maximum de suggestions (1-20)

    Returns:
        JSON response with:
        - success: Boolean
        - current_recipe: Dict with slug and cost_per_serving
        - budget_per_meal: Float
        - suggestions: List of dicts with slug, cost_per_serving, savings
    """
    # Récupérer le budget actuel
    budget = budget_manager.get_current_budget()
    if not budget:
        raise HTTPException(status_code=404, detail="Aucun budget défini")

    # Récupérer toutes les recettes
    recipes = mealie_client.get_all_recipes()
    all_slugs = [r.get("slug") for r in recipes if r.get("slug")]

    # Filtrer la recette actuelle
    if current_slug in all_slugs:
        all_slugs.remove(current_slug)

    # Calculer les coûts
    costs = cost_calculator.calculate_batch_costs(all_slugs[:50], use_open_prices=True)

    # Récupérer le coût de la recette actuelle
    current_cost = cost_calculator.calculate_cost(current_slug, use_open_prices=True)

    if not current_cost:
        raise HTTPException(status_code=404, detail=f"Recette {current_slug} non trouvée")

    # Suggérer des alternatives
    alternatives = budget_planner.suggest_cheaper_alternatives(
        current_cost=current_cost.cost_per_serving,
        budget_per_meal=budget.budget_per_meal,
        alternatives=costs,
        limit=limit,
    )

    return {
        "success": True,
        "current_recipe": {
            "slug": current_slug,
            "cost_per_serving": current_cost.cost_per_serving,
        },
        "budget_per_meal": budget.budget_per_meal,
        "suggestions": [
            {
                "slug": r.recipe_slug,
                "cost_per_serving": r.cost_per_serving,
                "savings": round(budget.budget_per_meal - r.cost_per_serving, 2),
            }
            for r in alternatives
        ],
    }


@app.get("/planning/cost-report")
async def generate_cost_report(
    slugs: List[str] = Query(..., description="Liste des slugs à analyser"),
):
    """Génère un rapport coût vs budget pour plusieurs recettes.

    Args:
        slugs: Liste des slugs de recettes à analyser

    Returns:
        JSON response with:
        - success: Boolean
        - budget: BudgetSettings object
        - report: Dict with metrics (total_recipes, avg_cost_per_serving, within_budget_pct, etc.)
    """
    # Récupérer le budget actuel
    budget = budget_manager.get_current_budget()
    if not budget:
        raise HTTPException(status_code=404, detail="Aucun budget défini")

    # Calculer les coûts
    costs = cost_calculator.calculate_batch_costs(slugs, use_open_prices=True)

    # Générer le rapport
    report = budget_planner.generate_cost_report(costs, budget)

    return {
        "success": True,
        "budget": budget.model_dump(),
        "report": report,
    }


@app.get("/foods")
async def list_foods(
    search: Optional[str] = Query(None, description="Filtrer par nom d'ingrédient"),
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=1000),
):
    """Liste les ingrédients (foods) Mealie avec pagination.

    Args:
        search: Filtre optionnel sur le nom
        page: Page à récupérer
        per_page: Nombre d'items par page

    Returns:
        JSON response with:
        - success: Boolean
        - foods: List of food objects
        - total: Total count
    """
    foods = mealie_client.get_foods()

    # Filtrer par recherche si fourni
    if search:
        foods = [f for f in foods if search.lower() in f.get("name", "").lower()]

    # Pagination
    total = len(foods)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_foods = foods[start:end]

    return {
        "success": True,
        "foods": paginated_foods,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@app.get("/foods/{food_id}")
async def get_food(food_id: str):
    """Récupère un food par son ID.

    Args:
        food_id: UUID du food

    Returns:
        JSON response with:
        - success: Boolean
        - food: Food object
    """
    food = mealie_client.get_food(food_id)
    if not food:
        raise HTTPException(status_code=404, detail=f"Food {food_id} non trouvé")

    return {
        "success": True,
        "food": food,
    }


@app.put("/foods/{food_id}")
async def update_food(food_id: str, food_data: dict = Body(...)):
    """Met à jour un food Mealie.

    Args:
        food_id: UUID du food
        food_data: Payload complet du food (PUT remplace l'objet entier)

    Returns:
        JSON response with:
        - success: Boolean
        - message: String
    """
    success = mealie_client.update_food(food_id, food_data)
    if not success:
        raise HTTPException(status_code=500, detail=f"Échec de la mise à jour du food {food_id}")

    return {
        "success": True,
        "message": f"Food {food_id} mis à jour",
    }
