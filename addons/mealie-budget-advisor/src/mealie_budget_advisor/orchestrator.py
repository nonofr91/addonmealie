"""High-level orchestrator: wires config, pricing, planning together."""

from __future__ import annotations

import logging
import os
from typing import Optional

from .budget_manager import BudgetManager
from .config import BudgetConfig
from .mealie_sync import MealieClient
from .models.budget import BudgetSettings
from .models.cost import CostBreakdown, RecipeCost
from .planning.budget_planner import BudgetPlanner
from .planning.budget_scorer import BudgetScorer
from .pricing.cost_calculator import CostCalculator
from .pricing.ingredient_matcher import IngredientMatcher
from .pricing.manual_pricer import ManualPricer
from .pricing.open_prices_client import OpenPricesClient
from .recipe_extras import (
    build_addon_extras,
    merge_extras,
    read_override,
)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("mealie-budget")


class BudgetOrchestratorError(Exception):
    """Orchestrator execution error."""


class BudgetOrchestrator:
    """Façade used by the API, UI and CLI layers."""

    def __init__(self, config: Optional[BudgetConfig] = None) -> None:
        self.config = config or BudgetConfig.load()
        self.budget_manager = BudgetManager(self.config.config_dir / "budget_settings.json")
        self.manual_pricer = ManualPricer(self.config.data_dir / "ingredient_prices.json")

        open_prices: Optional[OpenPricesClient] = None
        if self.config.enable_open_prices:
            open_prices = OpenPricesClient(self.config.open_prices_base_url)

        self.matcher = IngredientMatcher(
            manual_pricer=self.manual_pricer,
            open_prices=open_prices,
            enable_open_prices=self.config.enable_open_prices,
        )
        self.calculator = CostCalculator(self.matcher)
        self.planner = BudgetPlanner(BudgetScorer())

    # ------------------------------------------------------------------ status

    def get_status(self) -> dict:
        manual_count = len(self.manual_pricer.list())
        months = sorted(self.budget_manager.list().keys())
        return {
            "success": True,
            "mealie_base_url": self.config.mealie_base_url,
            "open_prices_enabled": self.config.enable_open_prices,
            "manual_prices_enabled": self.config.enable_manual_prices,
            "budget_planning_enabled": self.config.enable_budget_planning,
            "manual_price_count": manual_count,
            "configured_months": months,
            "nutrition_api_configured": bool(self.config.nutrition_api_url),
        }

    # ------------------------------------------------------------------ budget

    def get_budget(self, month: Optional[str] = None) -> BudgetSettings:
        month = month or BudgetSettings.current_month()
        return self.budget_manager.get_or_default(month)

    def set_budget(self, settings: BudgetSettings) -> BudgetSettings:
        return self.budget_manager.set(settings)

    # ------------------------------------------------------------------ costs

    def cost_recipe(self, slug: str) -> RecipeCost:
        with MealieClient(self.config.mealie_base_url, self.config.mealie_api_key) as client:
            recipe = client.get_recipe(slug)
            if not recipe:
                raise BudgetOrchestratorError(f"Recette introuvable: {slug}")
            cost = self.calculator.cost_of_recipe(
                recipe_slug=slug,
                recipe_name=recipe.get("name", slug),
                ingredient_texts=client.extract_ingredient_texts(recipe),
                servings=client.servings(recipe),
            )
            return self._apply_override(recipe, cost)

    def _apply_override(self, recipe: dict, cost: RecipeCost) -> RecipeCost:
        """Applique un éventuel override manuel lu dans ``recipe.extras``.

        La priorité est : ``cout_manuel_par_portion`` > ``cout_manuel_total``
        > coût calculé. Un override met ``price_source`` du breakdown
        inchangé mais remplace ``total_cost`` et ``cost_per_serving``.
        """
        override = read_override(recipe.get("extras"))
        if not override.is_active:
            return cost

        servings = max(cost.servings, 1)
        if override.per_serving is not None:
            new_per_serving = round(override.per_serving, 2)
            new_total = round(override.per_serving * servings, 2)
        elif override.total is not None:
            new_total = round(override.total, 2)
            new_per_serving = round(new_total / servings, 2)
        else:
            return cost

        return cost.model_copy(
            update={
                "total_cost": new_total,
                "cost_per_serving": new_per_serving,
            }
        )

    def batch_cost(self, slugs: list[str]) -> list[RecipeCost]:
        results: list[RecipeCost] = []
        with MealieClient(self.config.mealie_base_url, self.config.mealie_api_key) as client:
            for slug in slugs:
                recipe = client.get_recipe(slug)
                if not recipe:
                    logger.warning("Skipping unknown recipe: %s", slug)
                    continue
                cost = self.calculator.cost_of_recipe(
                    recipe_slug=slug,
                    recipe_name=recipe.get("name", slug),
                    ingredient_texts=client.extract_ingredient_texts(recipe),
                    servings=client.servings(recipe),
                )
                results.append(self._apply_override(recipe, cost))
        return results

    # ----------------------------------------------------------- sync Mealie

    def sync_recipe_cost(self, slug: str, month: Optional[str] = None) -> dict:
        """Recalcule le coût d'une recette et l'écrit dans ses ``extras`` Mealie.

        Ne touche JAMAIS aux clés ``cout_manuel_*`` (overrides utilisateur).
        """
        month = month or BudgetSettings.current_month()
        with MealieClient(self.config.mealie_base_url, self.config.mealie_api_key) as client:
            recipe = client.get_recipe(slug)
            if not recipe:
                raise BudgetOrchestratorError(f"Recette introuvable: {slug}")
            cost = self.calculator.cost_of_recipe(
                recipe_slug=slug,
                recipe_name=recipe.get("name", slug),
                ingredient_texts=client.extract_ingredient_texts(recipe),
                servings=client.servings(recipe),
            )
            addon_extras = build_addon_extras(cost, month=month)
            merged = merge_extras(recipe.get("extras"), addon_extras)
            ok = client.patch_extras(slug, merged)
        return {
            "slug": slug,
            "written": ok,
            "month": month,
            "cost_per_serving": cost.cost_per_serving,
            "total_cost": cost.total_cost,
            "confidence": cost.confidence,
            "override_preserved": any(
                k.startswith("cout_manuel_") and k in (recipe.get("extras") or {})
                for k in (recipe.get("extras") or {})
            ),
        }

    def refresh_all_costs(self, month: Optional[str] = None) -> dict:
        """Recalcule et publie le coût de toutes les recettes Mealie.

        Parcourt la liste, ignore les recettes sans ingrédients, et reporte
        combien ont été mises à jour / ignorées / en échec.
        """
        month = month or BudgetSettings.current_month()
        updated = 0
        skipped = 0
        failed: list[str] = []
        override_preserved = 0

        with MealieClient(self.config.mealie_base_url, self.config.mealie_api_key) as client:
            recipes = client.get_all_recipes()
            for summary in recipes:
                slug = summary.get("slug")
                if not slug:
                    skipped += 1
                    continue
                detail = client.get_recipe(slug)
                if not detail:
                    skipped += 1
                    continue
                ingredient_texts = client.extract_ingredient_texts(detail)
                if not ingredient_texts:
                    skipped += 1
                    continue

                try:
                    cost = self.calculator.cost_of_recipe(
                        recipe_slug=slug,
                        recipe_name=detail.get("name", slug),
                        ingredient_texts=ingredient_texts,
                        servings=client.servings(detail),
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Coût échoué pour %s: %s", slug, exc)
                    failed.append(slug)
                    continue

                existing = detail.get("extras") or {}
                if any(k.startswith("cout_manuel_") and existing.get(k) for k in existing):
                    override_preserved += 1

                merged = merge_extras(existing, build_addon_extras(cost, month=month))
                if client.patch_extras(slug, merged):
                    updated += 1
                else:
                    failed.append(slug)

        logger.info(
            "refresh_all_costs %s: %d mis à jour, %d ignorés, %d échecs",
            month, updated, skipped, len(failed),
        )
        return {
            "month": month,
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
            "override_preserved": override_preserved,
            "total": updated + skipped + len(failed),
        }

    # ------------------------------------------------------------------ plan

    def plan_budget_aware(
        self,
        month: Optional[str] = None,
        meals_target: Optional[int] = None,
        candidate_slugs: Optional[list[str]] = None,
    ) -> CostBreakdown:
        if not self.config.enable_budget_planning:
            raise BudgetOrchestratorError("Budget planning feature disabled")

        settings = self.get_budget(month)
        meals = meals_target or (settings.meals_per_day * settings.days_per_month)

        with MealieClient(self.config.mealie_base_url, self.config.mealie_api_key) as client:
            if candidate_slugs:
                recipes = [r for r in (client.get_recipe(s) for s in candidate_slugs) if r]
            else:
                recipes = client.get_all_recipes()

            costs: list[RecipeCost] = []
            for recipe in recipes:
                slug = recipe.get("slug", "")
                if not slug:
                    continue
                try:
                    detail = recipe if "recipeIngredient" in recipe else client.get_recipe(slug)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to load recipe %s: %s", slug, exc)
                    continue
                if not detail:
                    continue
                cost = self.calculator.cost_of_recipe(
                    recipe_slug=slug,
                    recipe_name=detail.get("name", slug),
                    ingredient_texts=client.extract_ingredient_texts(detail),
                    servings=client.servings(detail),
                )
                costs.append(self._apply_override(detail, cost))

        return self.planner.plan(costs, settings, meals_target=meals)
