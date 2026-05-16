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
from .models.menu import CourseType, Menu, MenuEntry, MealType, MenuGenerationRequest
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

        # Build metadata dict: slug → {tags, categories, rating, time} for season, course, rating, time filtering
        recipe_metadata: dict[str, dict] = {}
        for r in recipes:
            slug = r.get("slug")
            if slug:
                recipe_metadata[slug] = {
                    "tags": [t.get("slug", t.get("name", "")).lower() for t in r.get("tags", [])],
                    "categories": [c.get("slug", c.get("name", "")).lower() for c in r.get("recipeCategory", [])],
                    "rating": r.get("rating", 0),
                    "totalTime": r.get("totalTime"),
                    "prepTime": r.get("prepTime"),
                    "cookTime": r.get("cookTime"),
                }

        logger.info("Found %d recipes to consider", len(recipe_slugs))

        # Get household profiles for nutrition filtering and scoring
        household_profiles = {}
        if request.household_id:
            profiles_data = self.nutrition_client.get_profiles()
            if profiles_data:
                household_profiles = profiles_data.get("members", {})
                logger.info("Loaded %d household member profiles", len(household_profiles))

        # Extract allergens and foods to avoid from profiles
        allergens_to_avoid = self._extract_allergens(household_profiles)
        if allergens_to_avoid:
            logger.info("Allergens to avoid: %s", allergens_to_avoid)

        # Set household profiles in scorer for pathology-aware nutrition scoring
        if household_profiles:
            self.scorer.set_household_profiles(household_profiles)

        # Get menu history for variety (from Mealie mealplans)
        menu_history = self._get_menu_history(request.start_date)

        # Meal type enablement map with default rules
        # Weekdays: dinner only; Weekends/holidays: lunch + dinner
        meal_enabled = {
            "breakfast": request.include_breakfast,
            "lunch": request.include_lunch,
            "dinner": request.include_dinner,
        }

        # Generate menu entries
        entries: list[MenuEntry] = []
        current_date = request.start_date
        session_history = list(menu_history)
        weekly_cost_so_far = 0.0

        while current_date <= request.end_date:
            # Apply default meal rules if not overridden
            day_meal_enabled = self._get_meal_enablement_for_day(
                current_date, meal_enabled, request
            )

            for meal_key, courses in request.meal_composition.items():
                if not day_meal_enabled.get(meal_key, False):
                    continue
                meal_type = MealType(meal_key)
                
                # Generate complete meal (all courses together)
                meal_entries = self._generate_meal(
                    date=current_date,
                    meal_type=meal_type,
                    courses=courses,
                    recipe_slugs=recipe_slugs,
                    recipe_metadata=recipe_metadata,
                    menu_history=session_history,
                    current_date=current_date,
                    weekly_cost_so_far=weekly_cost_so_far,
                    budget_limit=request.budget_limit,
                    household_size=request.default_household_size,
                    quantity_overrides=request.meal_quantity_overrides,
                    allergens_to_avoid=allergens_to_avoid,
                )
                
                if meal_entries:
                    entries.extend(meal_entries)
                    # Update history and cost
                    for entry in meal_entries:
                        if entry.recipe_slug:
                            session_history.append(entry.recipe_slug)
                        # Update cost
                        cost_data = self.budget_client.get_recipe_cost(entry.recipe_slug)
                        if cost_data:
                            weekly_cost_so_far += cost_data.get("total_cost", 0) * entry.quantity

            current_date = self._next_day(current_date)
        
        # Calculate scores and totals
        scores = self._calculate_menu_scores(entries, recipe_metadata)
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

    def _extract_allergens(self, household_profiles: dict) -> set[str]:
        """Extract allergens and foods to avoid from household profiles."""
        allergens: set[str] = set()
        
        for member_id, member_data in household_profiles.items():
            allergies = member_data.get("allergies", [])
            if isinstance(allergies, list):
                allergens.update(allergies)
            
            intolerances = member_data.get("intolerances", [])
            if isinstance(intolerances, list):
                allergens.update(intolerances)
            
            foods_to_avoid = member_data.get("foods_to_avoid", [])
            if isinstance(foods_to_avoid, list):
                allergens.update(foods_to_avoid)
        
        return {a.lower() for a in allergens if a}

    def _get_meal_enablement_for_day(
        self, current_date: date, meal_enabled: dict[str, bool], request: MenuGenerationRequest
    ) -> dict[str, bool]:
        """
        Apply default meal rules for the day.
        Weekdays (Mon-Fri): dinner only
        Weekends (Sat-Sun): lunch + dinner
        """
        # If user explicitly set all flags, respect them
        if request.include_breakfast or request.include_lunch or request.include_dinner:
            return meal_enabled
        
        # Default rules
        is_weekend = current_date.weekday() >= 5  # 5=Saturday, 6=Sunday
        # Note: holidays detection could be added here with a holidays library
        
        if is_weekend:
            # Weekend: lunch + dinner
            return {"breakfast": False, "lunch": True, "dinner": True}
        else:
            # Weekday: dinner only
            return {"breakfast": False, "lunch": False, "dinner": True}

    def _generate_meal(
        self,
        date: date,
        meal_type: MealType,
        courses: list[str],
        recipe_slugs: list[str],
        recipe_metadata: dict[str, dict],
        menu_history: list[str],
        current_date: date,
        weekly_cost_so_far: float,
        budget_limit: Optional[float],
        household_size: int,
        quantity_overrides: Optional[dict[str, int]],
        allergens_to_avoid: set[str],
    ) -> list[MenuEntry]:
        """
        Generate a complete meal with all courses, considering budget compensation, time penalty, and allergens.
        """
        meal_entries: list[MenuEntry] = []
        total_meal_time_minutes = 0.0
        
        # Filter recipes for each course
        course_recipes: dict[str, list[str]] = {}
        for course_str in courses:
            try:
                course_type = CourseType(course_str)
                filtered_slugs = self._filter_by_course(
                    recipe_slugs, course_type, recipe_metadata
                )
                # Further filter by allergens
                if allergens_to_avoid:
                    filtered_slugs = self._filter_by_allergens(
                        filtered_slugs, allergens_to_avoid, recipe_metadata
                    )
                course_recipes[course_str] = filtered_slugs
            except ValueError:
                logger.warning("Unknown course type '%s', skipping", course_str)
                continue
        
        # Select best combination of recipes for all courses
        # For simplicity, select best recipe per course independently (could be improved with joint optimization)
        for course_str, slugs in course_recipes.items():
            if not slugs:
                logger.warning("No recipes available for course '%s' on %s", course_str, date)
                continue
            
            try:
                course_type = CourseType(course_str)
            except ValueError:
                continue
            
            # Rank recipes for this course
            ranked_recipes = self.scorer.rank_recipes(
                recipe_slugs=slugs,
                menu_history=menu_history,
                current_date=current_date,
                limit=10,
                recipe_metadata=recipe_metadata,
            )
            
            if not ranked_recipes:
                continue
            
            # Select top recipe
            best_slug, best_score = ranked_recipes[0]
            
            # Get recipe details
            recipe = self.mealie_client.get_recipe(best_slug)
            if not recipe:
                continue
            
            # Calculate quantity
            meal_key = f"{date.isoformat()}_{meal_type.value}"
            quantity = quantity_overrides.get(meal_key, household_size) if quantity_overrides else household_size
            
            # Extract time for this recipe
            recipe_meta = recipe_metadata.get(best_slug, {})
            total_time_minutes = self._extract_total_time_minutes(recipe_meta)
            total_meal_time_minutes += total_time_minutes
            
            entry = MenuEntry(
                date=date,
                meal_type=meal_type,
                course_type=course_type,
                recipe_id=recipe.get("id"),
                recipe_slug=best_slug,
                recipe_name=recipe.get("name", best_slug),
                quantity=quantity,
            )
            meal_entries.append(entry)
        
        # Check total meal time and log warning if > 2h
        if total_meal_time_minutes > 120:
            logger.warning(
                "Meal on %s (%s) exceeds 2h total time: %.1f minutes",
                date, meal_type.value, total_meal_time_minutes
            )
        
        # Budget compensation check
        if budget_limit:
            meal_cost = sum(
                (self.budget_client.get_recipe_cost(e.recipe_slug).get("total_cost", 0) if e.recipe_slug else 0) * e.quantity
                for e in meal_entries
            )
            projected_total = weekly_cost_so_far + meal_cost
            if projected_total > budget_limit:
                logger.info(
                    "Meal cost %.2f would exceed budget (projected total: %.2f/%.2f)",
                    meal_cost, projected_total, budget_limit
                )
        
        return meal_entries

    def _extract_total_time_minutes(self, recipe_metadata: dict) -> float:
        """Extract total preparation time in minutes from recipe metadata."""
        total_time = recipe_metadata.get("totalTime", 0)
        if total_time:
            if isinstance(total_time, str) and total_time.startswith("PT"):
                hours = 0
                minutes = 0
                if "H" in total_time:
                    hours = int(total_time.split("H")[0].replace("PT", ""))
                if "M" in total_time:
                    minutes = int(total_time.split("M")[0].split("H")[-1])
                return hours * 60 + minutes
            elif isinstance(total_time, (int, float)):
                return float(total_time)
        
        # Fallback to prepTime + cookTime
        prep_time = recipe_metadata.get("prepTime", 0)
        cook_time = recipe_metadata.get("cookTime", 0)
        
        def parse_time(t):
            if isinstance(t, str) and t.startswith("PT"):
                hours = 0
                minutes = 0
                if "H" in t:
                    hours = int(t.split("H")[0].replace("PT", ""))
                if "M" in t:
                    minutes = int(t.split("M")[0].split("H")[-1])
                return hours * 60 + minutes
            elif isinstance(t, (int, float)):
                return float(t)
            return 0
        
        return parse_time(prep_time) + parse_time(cook_time)

    def _filter_by_allergens(
        self,
        recipe_slugs: list[str],
        allergens_to_avoid: set[str],
        recipe_metadata: dict[str, dict],
    ) -> list[str]:
        """
        Filter recipes that contain allergens or foods to avoid.
        """
        filtered = []
        for slug in recipe_slugs:
            metadata = recipe_metadata.get(slug, {})
            # Check recipe name and tags for allergens
            recipe_name = metadata.get("name", "").lower()
            tags = set(metadata.get("tags", []))
            
            # Simple heuristic: check if any allergen appears in name or tags
            contains_allergen = False
            for allergen in allergens_to_avoid:
                if allergen in recipe_name or allergen in tags:
                    contains_allergen = True
                    break
            
            if not contains_allergen:
                filtered.append(slug)
            else:
                logger.debug("Recipe %s filtered due to allergens", slug)
        
        if len(filtered) < len(recipe_slugs):
            logger.info("Filtered %d recipes due to allergens", len(recipe_slugs) - len(filtered))
        
        return filtered

    def _filter_by_course(
        self,
        recipe_slugs: list[str],
        course_type: CourseType,
        recipe_metadata: dict[str, dict],
    ) -> list[str]:
        """
        Filter recipe pool to those matching the given course type category or tag.
        Strict filtering: no fallback to full pool if no recipes match.
        """
        course_cats = {c.lower() for c in self.config.course_categories.get(course_type.value, [])}
        if not course_cats:
            logger.warning("No course categories configured for '%s', returning empty list", course_type.value)
            return []

        filtered = []
        for slug in recipe_slugs:
            metadata = recipe_metadata.get(slug, {})
            categories = set(metadata.get("categories", []))
            tags = set(metadata.get("tags", []))
            
            # Match if course category appears in either categories or tags
            if course_cats & (categories | tags):
                filtered.append(slug)

        if not filtered:
            logger.warning(
                "No recipes found for course '%s' with categories/tags: %s. "
                "Consider running diagnose_recipe_metadata() to see available tags/categories.",
                course_type.value,
                sorted(course_cats)
            )

        logger.debug(
            "Course filter '%s': %d/%d recipes match", course_type.value, len(filtered), len(recipe_slugs)
        )
        return filtered

    def _generate_entry(
        self,
        date: date,
        meal_type: MealType,
        recipe_slugs: list[str],
        menu_history: list[str],
        current_date: date,
        course_type: CourseType = CourseType.MAIN,
        recipe_metadata: Optional[dict[str, dict]] = None,
    ) -> Optional[MenuEntry]:
        """Generate a single menu entry by selecting the best recipe."""
        # Rank recipes by combined score
        ranked_recipes = self.scorer.rank_recipes(
            recipe_slugs=recipe_slugs,
            menu_history=menu_history,
            current_date=current_date,
            limit=10,
            recipe_metadata=recipe_metadata,
        )

        if not ranked_recipes:
            logger.warning("No recipes available for %s/%s on %s", meal_type, course_type, date)
            return None

        # Select top recipe
        best_slug, best_score = ranked_recipes[0]

        # Get recipe details from metadata cache first, fall back to API
        recipe = self.mealie_client.get_recipe(best_slug)
        if not recipe:
            logger.warning("Could not get recipe details for %s", best_slug)
            return None

        # Use default quantity (will be updated in second step)
        default_quantity = self.config.default_weekly_quantities.get(meal_type.value, 1)

        return MenuEntry(
            date=date,
            meal_type=meal_type,
            course_type=course_type,
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

    def _calculate_menu_scores(
        self, entries: list[MenuEntry], recipe_metadata: Optional[dict[str, dict]] = None
    ) -> dict[str, float]:
        """Calculate overall scores for the menu."""
        if not entries:
            return {"nutrition": 0.0, "budget": 0.0, "variety": 0.0, "season": 0.0}

        # Get scores for each entry and average
        all_scores = []
        for entry in entries:
            if entry.recipe_slug:
                tags = recipe_metadata.get(entry.recipe_slug, {}).get("tags", []) if recipe_metadata else []
                scores = self.scorer.score_recipe(entry.recipe_slug, recipe_tags=tags)
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
