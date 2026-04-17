"""Weekly menu planner — selects recipes compatible with household profiles."""

from __future__ import annotations

import json
import logging
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from ..mealie_sync import MealieClient
from ..models.menu import DayMenu, MealSlot, MealType, WeekMenu
from ..models.profile import HouseholdProfile
from ..profiles.manager import ProfileManager
from .allergy_filter import AllergyFilter
from .scorer import RecipeScorer, _parse_mealie_nutrition

logger = logging.getLogger(__name__)

MEAL_STRUCTURE: list[MealType] = [MealType.breakfast, MealType.lunch, MealType.dinner]

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "menu_plans"


class MenuPlanner:
    """Génère un planning hebdomadaire de repas adapté aux profils du foyer."""

    def __init__(
        self,
        mealie_client: Optional[MealieClient] = None,
        profile_manager: Optional[ProfileManager] = None,
        scorer: Optional[RecipeScorer] = None,
        allergy_filter: Optional[AllergyFilter] = None,
    ) -> None:
        self.client = mealie_client or MealieClient()
        self.profile_manager = profile_manager or ProfileManager()
        self.scorer = scorer or RecipeScorer()
        self.allergy_filter = allergy_filter or AllergyFilter()

    def plan_week(self, week_label: str, push: bool = False) -> WeekMenu:
        """
        Génère un menu pour la semaine donnée.

        Args:
            week_label: Format ISO ex: "2026-W16"
            push: Si True, pousse le planning dans Mealie.

        Returns:
            WeekMenu complet.
        """
        household = self.profile_manager.household
        start_date = _week_start(week_label)

        recipes = self.client.get_all_recipes()
        safe_recipes, rejected = self.allergy_filter.filter_recipes(recipes, household)
        if rejected:
            logger.info("Recettes exclues par allergies/restrictions: %d", len(rejected))

        if not safe_recipes:
            logger.warning("Aucune recette compatible — menu vide")

        recipe_details = self._fetch_details(safe_recipes)
        week = WeekMenu(
            week_label=week_label,
            member_names=[m.name for m in household.members],
        )

        used_slugs: set[str] = set()

        for day_offset in range(7):
            day_date = start_date + timedelta(days=day_offset)
            day_menu = DayMenu(date=day_date)

            for meal_type in MEAL_STRUCTURE:
                recipe = self._pick_recipe(
                    recipe_details, household, meal_type, used_slugs
                )
                if recipe is None:
                    continue

                slug = recipe.get("slug", "")
                name = recipe.get("name", slug)
                used_slugs.add(slug)

                nutrition = _parse_mealie_nutrition(recipe)
                servings_raw = recipe.get("recipeServings") or 1
                try:
                    servings = max(int(float(servings_raw)), 1)
                except (ValueError, TypeError):
                    servings = 1
                per_serving = nutrition.scale(1.0 / servings)

                household_score = self.scorer.score_for_household(recipe, household.members, meal_type)

                slot = MealSlot(
                    meal_type=meal_type,
                    recipe_slug=slug,
                    recipe_name=name,
                    servings=len(household.members),
                    nutrition_per_serving=per_serving,
                    score=household_score,
                )
                day_menu.slots.append(slot)

            week.days.append(day_menu)

        if push:
            self._push_to_mealie(week)

        self._save_report(week, household)
        return week

    def _fetch_details(self, recipes: list[dict]) -> list[dict]:
        """Récupère les détails (nutrition, ingrédients) des recettes."""
        detailed: list[dict] = []
        for r in recipes:
            detail = self.client.get_recipe(r["slug"])
            if detail:
                detailed.append(detail)
        return detailed

    def _pick_recipe(
        self,
        recipes: list[dict],
        household: HouseholdProfile,
        meal_type: MealType,
        used_slugs: set[str],
    ) -> Optional[dict]:
        """Choisit la meilleure recette disponible pour un repas donné."""
        candidates = [r for r in recipes if r.get("slug") not in used_slugs]
        if not candidates:
            candidates = [r for r in recipes]

        scored = [
            (r, self.scorer.score_for_household(r, household.members, meal_type))
            for r in candidates
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        top = scored[:max(3, len(scored) // 4)]
        if not top:
            return None
        return random.choice(top)[0]

    def _push_to_mealie(self, week: WeekMenu) -> None:
        """Pousse le planning dans Mealie via l'API."""
        entries = week.to_mealie_mealplan_entries()
        ok = self.client.create_mealplan_bulk(entries)
        if ok:
            logger.info("Planning poussé dans Mealie: %d entrées", len(entries))
            print(f"✅ Planning semaine {week.week_label} créé dans Mealie ({len(entries)} repas)")
        else:
            logger.warning("Échec de la création du planning dans Mealie")

    def _save_report(self, week: WeekMenu, household: HouseholdProfile) -> None:
        """Sauvegarde le rapport JSON du menu."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORTS_DIR / f"menu_{week.week_label}.json"
        payload = {
            "week_label": week.week_label,
            "members": [m.name for m in household.members],
            "avg_daily_calories": week.average_daily_calories(),
            "days": [
                {
                    "date": d.date.isoformat(),
                    "total_calories": round(d.total_calories(), 1),
                    "meals": [
                        {
                            "type": s.meal_type.value,
                            "recipe": s.recipe_name,
                            "slug": s.recipe_slug,
                            "score": s.score,
                            "calories_per_serving": round(s.nutrition_per_serving.calories_kcal, 1),
                        }
                        for s in d.slots
                    ],
                }
                for d in week.days
            ],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Rapport menu sauvegardé: %s", path)

    def print_week(self, week: WeekMenu) -> None:
        """Affiche le menu de la semaine dans la console."""
        print(f"\n📅  Menu semaine {week.week_label}")
        print(f"    Membres: {', '.join(week.member_names)}")
        print(f"    Moyenne: {week.average_daily_calories()} kcal/jour\n")
        meal_icons = {MealType.breakfast: "🌅", MealType.lunch: "🍽️ ", MealType.dinner: "🌙", MealType.snack: "🍎"}
        for day in week.days:
            print(f"  {day.date.strftime('%A %d/%m')} ({round(day.total_calories())} kcal)")
            for slot in day.slots:
                icon = meal_icons.get(slot.meal_type, "•")
                print(f"    {icon} {slot.recipe_name}  [{round(slot.nutrition_per_serving.calories_kcal)} kcal, score:{slot.score:.2f}]")
        print()


def _week_start(week_label: str) -> date:
    """Parse 'YYYY-Www' → date du lundi."""
    try:
        year, week = week_label.split("-W")
        return date.fromisocalendar(int(year), int(week), 1)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Format semaine invalide '{week_label}' — utiliser YYYY-Www ex: 2026-W16") from exc
