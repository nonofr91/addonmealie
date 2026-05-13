"""Menu orchestrator - coordinates nutrition and budget for menu planning."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from typing import Optional

from .clients.budget_client import BudgetClient
from .clients.mealie_client import MealieClient
from .clients.nutrition_client import NutritionClient
from .config import MenuOrchestratorConfig
from .models.menu import Menu, MenuEntry, MealType, MenuGenerationRequest
from .scoring.combined_scorer import CombinedScorer
from .storage import get_storage

logger = logging.getLogger(__name__)


class MenuOrchestrator:
    """
    Orchestrates menu generation using nutrition and budget criteria.
    
    Workflow:
    1. Generate menu (recipes for each meal)
    2. Define quantities per meal (two-step workflow)
    3. Push to Mealie mealplan
    """

    def __init__(self, config: Optional[MenuOrchestratorConfig] = None) -> None:
        self.config = config or MenuOrchestratorConfig()
        
        # Initialize clients
        self.mealie_client = MealieClient(
            base_url=self.config.mealie_base_url,
            api_key=self.config.mealie_api_key,
        )
        self.nutrition_client = NutritionClient(
            base_url=self.config.nutrition_advisor_url,
            api_key=self.config.nutrition_advisor_key,
        )
        self.budget_client = BudgetClient(
            base_url=self.config.budget_advisor_url,
            api_key=self.config.budget_advisor_key,
        )
        
        # Initialize scorer
        self.scorer = CombinedScorer(
            config=self.config,
            nutrition_client=self.nutrition_client,
            budget_client=self.budget_client,
        )

    def generate_menu(self, request: MenuGenerationRequest) -> Menu:
        """
        Generate a menu for the specified date range.
        
        Args:
            request: Menu generation request with dates and constraints
            
        Returns:
            Generated menu with entries
        """
        logger.info(
            "Generating menu from %s to %s (budget: %s)",
            request.start_date,
            request.end_date,
            request.budget_limit,
        )
        
        # Get all recipes from Mealie
        recipes = self.mealie_client.get_all_recipes()
        recipe_slugs = [r.get("slug") for r in recipes if r.get("slug")]
        
        logger.info("Found %d recipes to consider", len(recipe_slugs))
        
        # Get menu history for variety (from Mealie mealplans)
        menu_history = self._get_menu_history(request.start_date)
        
        # Generate menu entries
        entries: list[MenuEntry] = []
        current_date = request.start_date
        
        while current_date <= request.end_date:
            # Generate entries for each meal type
            if request.include_breakfast:
                entry = self._generate_entry(
                    date=current_date,
                    meal_type=MealType.BREAKFAST,
                    recipe_slugs=recipe_slugs,
                    menu_history=menu_history,
                    current_date=current_date,
                )
                if entry:
                    entries.append(entry)
            
            if request.include_lunch:
                entry = self._generate_entry(
                    date=current_date,
                    meal_type=MealType.LUNCH,
                    recipe_slugs=recipe_slugs,
                    menu_history=menu_history,
                    current_date=current_date,
                )
                if entry:
                    entries.append(entry)
            
            if request.include_dinner:
                entry = self._generate_entry(
                    date=current_date,
                    meal_type=MealType.DINNER,
                    recipe_slugs=recipe_slugs,
                    menu_history=menu_history,
                    current_date=current_date,
                )
                if entry:
                    entries.append(entry)
            
            current_date = self._next_day(current_date)
        
        # Calculate scores and totals
        scores = self._calculate_menu_scores(entries)
        total_cost = self._calculate_total_cost(entries)
        
        menu = Menu(
            id=str(uuid.uuid4()),
            start_date=request.start_date,
            end_date=request.end_date,
            entries=entries,
            total_cost=total_cost,
            scores=scores,
            created_at=datetime.utcnow().isoformat(),
        )
        
        # Save to storage
        storage = get_storage()
        storage.save(menu)
        
        logger.info("Generated menu with %d entries", len(entries))
        return menu

    def _generate_entry(
        self,
        date: date,
        meal_type: MealType,
        recipe_slugs: list[str],
        menu_history: list[str],
        current_date: date,
    ) -> Optional[MenuEntry]:
        """Generate a single menu entry by selecting the best recipe."""
        # Rank recipes by combined score
        ranked_recipes = self.scorer.rank_recipes(
            recipe_slugs=recipe_slugs,
            menu_history=menu_history,
            current_date=current_date,
            limit=10,
        )
        
        if not ranked_recipes:
            logger.warning("No recipes available for %s on %s", meal_type, date)
            return None
        
        # Select top recipe
        best_slug, best_score = ranked_recipes[0]
        
        # Get recipe details
        recipe = self.mealie_client.get_recipe(best_slug)
        if not recipe:
            logger.warning("Could not get recipe details for %s", best_slug)
            return None
        
        # Use default quantity (will be updated in second step)
        default_quantity = self.config.default_weekly_quantities.get(meal_type.value, 1)
        
        return MenuEntry(
            date=date,
            meal_type=meal_type,
            recipe_id=recipe.get("id"),
            recipe_slug=best_slug,
            recipe_name=recipe.get("name", best_slug),
            quantity=default_quantity,
        )

    def _get_menu_history(self, start_date: date) -> list[str]:
        """Get recent menu history for variety tracking."""
        # Get mealplans from the last 4 weeks
        end_date = start_date
        start_history = self._subtract_days(start_date, 28)
        
        mealplans = self.mealie_client.get_mealplans(
            start_date=start_history.isoformat(),
            end_date=end_date.isoformat(),
        )
        
        # Extract recipe slugs from mealplans
        history: list[str] = []
        for plan in mealplans:
            recipe_slug = plan.get("recipe", {}).get("slug")
            if recipe_slug:
                history.append(recipe_slug)
        
        return history

    def _calculate_menu_scores(self, entries: list[MenuEntry]) -> dict[str, float]:
        """Calculate overall scores for the menu."""
        if not entries:
            return {"nutrition": 0.0, "budget": 0.0, "variety": 0.0, "season": 0.0}
        
        # Get scores for each entry and average
        all_scores = []
        for entry in entries:
            if entry.recipe_slug:
                scores = self.scorer.score_recipe(entry.recipe_slug)
                all_scores.append(scores)
        
        if not all_scores:
            return {"nutrition": 0.0, "budget": 0.0, "variety": 0.0, "season": 0.0}
        
        # Average scores
        avg_scores = {
            "nutrition": sum(s["nutrition"] for s in all_scores) / len(all_scores),
            "budget": sum(s["budget"] for s in all_scores) / len(all_scores),
            "variety": sum(s["variety"] for s in all_scores) / len(all_scores),
            "season": sum(s["season"] for s in all_scores) / len(all_scores),
        }
        
        return avg_scores

    def _calculate_total_cost(self, entries: list[MenuEntry]) -> Optional[float]:
        """Calculate total cost for all menu entries."""
        if not entries:
            return None
        
        total_cost = 0.0
        for entry in entries:
            if entry.recipe_slug:
                cost_data = self.budget_client.get_recipe_cost(entry.recipe_slug)
                if cost_data:
                    cost = cost_data.get("total_cost", 0)
                    total_cost += cost * entry.quantity
        
        return total_cost

    def _next_day(self, d: date) -> date:
        """Get the next day."""
        from datetime import timedelta
        return d + timedelta(days=1)

    def _subtract_days(self, d: date, days: int) -> date:
        """Subtract days from a date."""
        from datetime import timedelta
        return d - timedelta(days=days)

    def update_quantities(self, menu_id: str, quantities: dict[str, int]) -> Menu:
        """
        Update quantities for menu entries.
        
        Args:
            menu_id: Menu ID
            quantities: Map of entry index to quantity
            
        Returns:
            Updated menu
        """
        storage = get_storage()
        menu = storage.get(menu_id)
        
        if not menu:
            raise ValueError(f"Menu {menu_id} not found")
        
        # Update quantities for entries
        for entry_idx, quantity in quantities.items():
            try:
                idx = int(entry_idx)
                if 0 <= idx < len(menu.entries):
                    menu.entries[idx].quantity = quantity
                    logger.debug("Updated quantity for entry %d to %d", idx, quantity)
            except (ValueError, IndexError) as exc:
                logger.warning("Invalid entry index %s: %s", entry_idx, exc)
        
        # Recalculate total cost
        menu.total_cost = self._calculate_total_cost(menu.entries)
        
        # Save updated menu
        storage.save(menu)
        
        logger.info("Updated quantities for menu %s", menu_id)
        return menu

    def push_to_mealie(self, menu: Menu) -> bool:
        """
        Push menu to Mealie mealplan.
        
        Args:
            menu: Menu to push
            
        Returns:
            True if successful
        """
        logger.info("Pushing menu to Mealie: %d entries", len(menu.entries))
        
        success_count = 0
        for entry in menu.entries:
            mealplan_entry = {
                "date": entry.date.isoformat(),
                "entry_type": entry.meal_type.value,
                "recipe_id": entry.recipe_id,
            }
            
            if self.mealie_client.create_mealplan(mealplan_entry):
                success_count += 1
            else:
                logger.warning("Failed to create mealplan entry for %s", entry.recipe_name)
        
        logger.info("Pushed %d/%d entries to Mealie", success_count, len(menu.entries))
        return success_count == len(menu.entries)

    def close(self) -> None:
        """Close all clients."""
        self.mealie_client.close()
        self.nutrition_client.close()
        self.budget_client.close()

    def __enter__(self) -> "MenuOrchestrator":
        return self

    def __exit__(self, *args) -> None:
        self.close()


def main() -> None:
    """CLI entry point for menu generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate menus for Mealie")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--budget", type=float, help="Budget limit")
    parser.add_argument("--push", action="store_true", help="Push to Mealie")
    
    args = parser.parse_args()
    
    config = MenuOrchestratorConfig()
    request = MenuGenerationRequest(
        start_date=date.fromisoformat(args.start_date),
        end_date=date.fromisoformat(args.end_date),
        budget_limit=args.budget,
    )
    
    with MenuOrchestrator(config) as orchestrator:
        menu = orchestrator.generate_menu(request)
        
        print(f"Generated menu: {len(menu.entries)} entries")
        print(f"Total cost: {menu.total_cost}")
        print(f"Scores: {menu.scores}")
        
        if args.push:
            orchestrator.push_to_mealie(menu)
            print("Menu pushed to Mealie")
