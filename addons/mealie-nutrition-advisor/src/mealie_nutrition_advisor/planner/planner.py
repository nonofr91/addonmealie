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
from ..models.profile import DayOfWeek, HouseholdProfile
from ..profiles.manager import ProfileManager
from .allergy_filter import AllergyFilter
from .scorer import RecipeScorer, _parse_mealie_nutrition

logger = logging.getLogger(__name__)

MEAL_STRUCTURE: list[MealType] = [MealType.breakfast, MealType.lunch, MealType.dinner]

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "menu_plans"


def _date_to_day_of_week(d: date) -> DayOfWeek:
    """Convertit une date en DayOfWeek."""
    day_map = {
        0: DayOfWeek.monday,
        1: DayOfWeek.tuesday,
        2: DayOfWeek.wednesday,
        3: DayOfWeek.thursday,
        4: DayOfWeek.friday,
        5: DayOfWeek.saturday,
        6: DayOfWeek.sunday,
    }
    return day_map[d.weekday()]


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
            day_of_week = _date_to_day_of_week(day_date)
            day_menu = DayMenu(date=day_date)

            for meal_type in MEAL_STRUCTURE:
                present_members = [
                    m for m in household.members
                    if m.weekly_presence.is_present(day_of_week, meal_type.value)
                ]

                if not present_members:
                    logger.debug("Aucun membre présent pour %s %s", day_of_week.value, meal_type.value)
                    continue

                recipe = self._pick_recipe(
                    recipe_details, household, meal_type, used_slugs, present_members
                )
                if recipe is None:
                    continue

                slug = recipe.get("slug", "")
                name = recipe.get("name", slug)
                recipe_id = recipe.get("id")
                used_slugs.add(slug)

                # Vérifier et collecter les conflits pour alerte
                has_conflict, conflict_msg, individual_scores = self._check_multi_profile_conflict(
                    recipe, present_members, meal_type
                )
                if has_conflict:
                    week.conflicts.append({
                        "date": day_date.isoformat(),
                        "meal_type": meal_type.value,
                        "recipe": name,
                        "message": conflict_msg,
                        "individual_scores": individual_scores,
                    })

                nutrition = _parse_mealie_nutrition(recipe)
                servings_raw = recipe.get("recipeServings") or 1
                try:
                    servings = max(int(float(servings_raw)), 1)
                except (ValueError, TypeError):
                    servings = 1
                per_serving = nutrition.scale(1.0 / servings)

                household_score = self.scorer.score_for_household(recipe, present_members, meal_type)

                slot = MealSlot(
                    meal_type=meal_type,
                    recipe_slug=slug,
                    recipe_id=recipe_id,
                    recipe_name=name,
                    servings=len(present_members),
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
        present_members: list[MemberProfile],
    ) -> Optional[dict]:
        """Choisit la meilleure recette disponible pour un repas donné."""
        candidates = [r for r in recipes if r.get("slug") not in used_slugs]
        if not candidates:
            candidates = [r for r in recipes]

        scored = []
        for r in candidates:
            # Vérifier les conflits multi-profils
            has_conflict, conflict_msg, individual_scores = self._check_multi_profile_conflict(
                r, present_members, meal_type
            )
            household_score = self.scorer.score_for_household(r, present_members, meal_type)

            if has_conflict:
                # Logger le conflit mais ne pas rejeter automatiquement si score > 0.5
                if household_score < 0.5:
                    logger.warning(f"Conflit rejeté: {conflict_msg} pour {r.get('name')}")
                    continue
                else:
                    logger.info(f"Conflit détecté mais score acceptable: {conflict_msg} pour {r.get('name')}")

            scored.append((r, household_score, individual_scores))

        scored.sort(key=lambda x: x[1], reverse=True)

        top = scored[:max(3, len(scored) // 4)]
        if not top:
            return None

        selected = random.choice(top)
        recipe = selected[0]
        scores = selected[2]

        # Logger les scores individuels pour debug
        logger.debug(f"Recette sélectionnée: {recipe.get('name')} - Scores: {scores}")

        return recipe

    def _check_multi_profile_conflict(
        self,
        recipe: dict,
        members: list[MemberProfile],
        meal_type: MealType,
    ) -> tuple[bool, str, dict]:
        """
        Vérifie s'il y a un conflit entre les profils des membres.

        Retourne:
        - (has_conflict, message, individual_scores)
        - has_conflict: True si écart > 0.3 ou un score < 0.3
        - message: Description du conflit
        - individual_scores: Dict {member_name: score}
        """
        individual_scores = {}
        for member in members:
            report = self.scorer.score(recipe, member, meal_type)
            individual_scores[member.name] = report.score

        scores = list(individual_scores.values())
        min_score = min(scores)
        max_score = max(scores)
        score_gap = max_score - min_score

        # Si un score < 0.3, rejet
        if min_score < 0.3:
            low_members = [name for name, score in individual_scores.items() if score < 0.3]
            return True, f"Recette incompatible pour {', '.join(low_members)} (score < 0.3)", individual_scores

        # Si écart > 0.3, alerte pour arbitrage
        if score_gap > 0.3:
            return True, f"Conflit de préférences (écart {score_gap:.2f}), arbitrage manuel recommandé", individual_scores

        return False, "", individual_scores

    def _push_to_mealie(self, week: WeekMenu) -> None:
        """Pousse le planning dans Mealie."""
        entries = week.to_mealie_mealplan_entries()
        success_count = 0
        for entry in entries:
            ok = self.client.create_mealplan(entry)
            if ok:
                success_count += 1
        if success_count == len(entries):
            logger.info("Planning poussé dans Mealie: %d entrées", success_count)
            print(f"✅ Planning semaine {week.week_label} créé dans Mealie ({len(entries)} repas)")
        else:
            logger.warning("Push partiel dans Mealie: %d/%d entrées", success_count, len(entries))

    def _save_report(self, week: WeekMenu, household: HouseholdProfile) -> None:
        """Sauvegarde le rapport JSON du menu."""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        path = REPORTS_DIR / f"menu_{week.week_label}.json"
        payload = {
            "week_label": week.week_label,
            "members": [m.name for m in household.members],
            "avg_daily_calories": week.average_daily_calories(),
            "conflicts": week.conflicts,
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
            print(f"  {day.day_date.strftime('%A %d/%m')} ({round(day.total_calories())} kcal)")
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
