"""Draft manager for menu planning CRUD operations."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4

from ..mealie_sync import MealieClient
from ..models.menu import MealType
from ..models.menu_draft import (
    ConflictReport,
    DayDraftSlots,
    DraftSlot,
    DraftStatus,
    MenuDraft,
    NutritionSummary,
)
from ..models.profile import HouseholdProfile
from ..planner.history_tracker import HistoryTracker
from ..planner.scorer import RecipeScorer
from ..planner.variety_scorer import VarietyScorer
from ..profiles.manager import ProfileManager

logger = logging.getLogger(__name__)

# Storage paths
DRAFTS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "drafts"


def _week_start(week_label: str) -> date:
    """Parse 'YYYY-Www' → date du lundi."""
    try:
        year, week = week_label.split("-W")
        return date.fromisocalendar(int(year), int(week), 1)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Format semaine invalide '{week_label}' — utiliser YYYY-Www ex: 2026-W16") from exc


class DraftManager:
    """Manages menu drafts: creation, persistence, validation, and push to Mealie."""
    
    def __init__(
        self,
        mealie_client: Optional[MealieClient] = None,
        profile_manager: Optional[ProfileManager] = None,
        nutrition_scorer: Optional[RecipeScorer] = None,
        variety_scorer: Optional[VarietyScorer] = None,
    ) -> None:
        self.client = mealie_client or MealieClient()
        self.profile_manager = profile_manager or ProfileManager()
        self.nutrition_scorer = nutrition_scorer or RecipeScorer()
        self.variety_scorer = variety_scorer or VarietyScorer()
        
        # Ensure drafts directory exists
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _get_draft_path(self, draft_id: str) -> Path:
        """Get file path for a draft."""
        return DRAFTS_DIR / f"{draft_id}.json"
    
    def _save_draft(self, draft: MenuDraft) -> None:
        """Save draft to disk."""
        path = self._get_draft_path(draft.draft_id)
        path.write_text(
            draft.model_dump_json(indent=2),
            encoding="utf-8"
        )
        logger.info("Draft saved: %s", path)
    
    def _load_draft(self, draft_id: str) -> Optional[MenuDraft]:
        """Load draft from disk."""
        path = self._get_draft_path(draft_id)
        if not path.exists():
            return None
        
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return MenuDraft.model_validate(data)
        except Exception as exc:
            logger.error("Failed to load draft %s: %s", draft_id, exc)
            return None
    
    def _delete_draft_file(self, draft_id: str) -> bool:
        """Delete draft file from disk."""
        path = self._get_draft_path(draft_id)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def _fetch_recipe_details(self, recipes: list[dict]) -> list[dict]:
        """Fetch detailed recipe information including nutrition."""
        detailed = []
        for r in recipes:
            detail = self.client.get_recipe(r["slug"])
            if detail:
                detailed.append(detail)
        return detailed
    
    def _determine_present_members(
        self,
        household: HouseholdProfile,
        day: date,
        meal_type: MealType,
    ) -> list:
        """Determine which members are present for a meal."""
        from ..models.profile import DayOfWeek
        
        day_map = {
            0: DayOfWeek.monday,
            1: DayOfWeek.tuesday,
            2: DayOfWeek.wednesday,
            3: DayOfWeek.thursday,
            4: DayOfWeek.friday,
            5: DayOfWeek.saturday,
            6: DayOfWeek.sunday,
        }
        day_of_week = day_map.get(day.weekday(), DayOfWeek.monday)
        
        return [
            m for m in household.members
            if m.weekly_presence.is_present(day_of_week, meal_type.value)
        ]
    
    def _pick_recipe_for_slot(
        self,
        candidates: list[dict],
        household: HouseholdProfile,
        present_members: list,
        meal_type: MealType,
        used_slugs: set[str],
        day: date,
    ) -> Optional[tuple[dict, float, dict]]:
        """Pick best recipe for a slot considering nutrition and variety."""
        
        scored = []
        for recipe in candidates:
            slug = recipe.get("slug", "")
            
            # Skip if already used this week (unless we're out of options)
            if slug in used_slugs and len(candidates) > len(used_slugs) + 3:
                continue
            
            # Calculate nutrition score for household
            nutrition_score = self.nutrition_scorer.score_for_household(
                recipe, present_members, meal_type
            )
            
            # Calculate variety score
            variety_result = self.variety_scorer.score(recipe, nutrition_score, meal_type, day)
            
            # Get composite score
            composite, breakdown = self.variety_scorer.score_with_nutrition(
                recipe, nutrition_score, meal_type, day
            )
            
            scored.append((recipe, composite, breakdown, variety_result))
        
        if not scored:
            return None
        
        # Sort by composite score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Pick top 3 and randomly select for variety
        import random
        top = scored[:min(3, len(scored))]
        selected = random.choice(top)
        
        return selected[0], selected[1], selected[2]
    
    def generate_draft(
        self,
        week_label: str,
        household: Optional[HouseholdProfile] = None,
    ) -> MenuDraft:
        """Generate a new menu draft for the given week.
        
        Args:
            week_label: Week in format YYYY-Www (e.g., 2026-W16)
            household: Optional household profile (loads default if not provided)
            
        Returns:
            New MenuDraft with generated slots.
        """
        if household is None:
            household = self.profile_manager.household
        
        start_date = _week_start(week_label)
        
        # Get all recipes
        logger.info("Fetching recipes for draft generation...")
        all_recipes = self.client.get_all_recipes()
        detailed_recipes = self._fetch_recipe_details(all_recipes)
        
        # Filter recipes with nutrition only
        recipes_with_nutrition = [
            r for r in detailed_recipes
            if r.get("nutrition") and r["nutrition"].get("calories")
        ]
        
        if not recipes_with_nutrition:
            logger.warning("No recipes with nutrition data found!")
            recipes_with_nutrition = detailed_recipes  # Fallback
        
        logger.info("Generating draft for week %s with %d recipes", week_label, len(recipes_with_nutrition))
        
        # Refresh variety metrics
        self.variety_scorer.refresh_metrics()
        
        # Create draft
        draft = MenuDraft(
            week_label=week_label,
            member_names=[m.name for m in household.members],
        )
        
        used_slugs: set[str] = set()
        meal_structure = [MealType.breakfast, MealType.lunch, MealType.dinner]
        
        for day_offset in range(7):
            day_date = start_date + timedelta(days=day_offset)
            day_name = day_date.strftime("%A")
            
            day_slots = DayDraftSlots(date=day_date, day_name=day_name)
            
            for meal_type in meal_structure:
                # Determine present members
                present_members = self._determine_present_members(
                    household, day_date, meal_type
                )
                
                if not present_members:
                    logger.debug("No members present for %s %s", day_date, meal_type.value)
                    continue
                
                # Pick recipe
                result = self._pick_recipe_for_slot(
                    recipes_with_nutrition,
                    household,
                    present_members,
                    meal_type,
                    used_slugs,
                    day_date,
                )
                
                if result is None:
                    logger.warning("Could not find suitable recipe for %s %s", day_date, meal_type.value)
                    continue
                
                recipe, composite_score, breakdown = result
                
                slug = recipe.get("slug", "")
                name = recipe.get("name", slug)
                recipe_id = recipe.get("id")
                used_slugs.add(slug)
                
                # Get nutrition per serving
                from ..planner.scorer import _parse_mealie_nutrition
                nutrition = _parse_mealie_nutrition(recipe)
                
                servings_raw = recipe.get("recipeServings") or 1
                try:
                    servings = max(int(float(servings_raw)), 1)
                except (ValueError, TypeError):
                    servings = 1
                
                per_serving = nutrition.scale(1.0 / servings)
                
                # Create slot
                slot = DraftSlot(
                    meal_type=meal_type,
                    recipe_slug=slug,
                    recipe_name=name,
                    recipe_id=recipe_id,
                    servings=len(present_members),
                    score=composite_score,
                    score_breakdown=breakdown,
                    nutrition_per_serving=per_serving,
                )
                
                day_slots.slots.append(slot)
            
            draft.days.append(day_slots)
        
        # Compute nutrition summary
        target_calories = sum(m.target_calories() for m in household.members)
        draft.compute_nutrition_summary(target_calories)
        
        # Calculate overall score
        if draft.days:
            scores = [s.score for d in draft.days for s in d.slots if s.score > 0]
            draft.overall_score = round(sum(scores) / len(scores), 3) if scores else 0.0
        
        # Save draft
        self._save_draft(draft)
        
        logger.info("Draft generated: %s with %d days", draft.draft_id, len(draft.days))
        return draft
    
    def get_draft(self, draft_id: str) -> Optional[MenuDraft]:
        """Get a draft by ID."""
        return self._load_draft(draft_id)
    
    def list_drafts(self) -> list[dict]:
        """List all drafts with basic info."""
        drafts = []
        for path in DRAFTS_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                drafts.append({
                    "draft_id": data.get("draft_id"),
                    "week_label": data.get("week_label"),
                    "status": data.get("status"),
                    "generated_at": data.get("generated_at"),
                    "overall_score": data.get("overall_score"),
                    "member_names": data.get("member_names"),
                    "num_slots": sum(len(d.get("slots", [])) for d in data.get("days", [])),
                })
            except Exception as exc:
                logger.warning("Failed to list draft %s: %s", path, exc)
        
        # Sort by generation date descending
        drafts.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        return drafts
    
    def update_slot(
        self,
        draft_id: str,
        day_date: date,
        meal_type: MealType,
        new_slot: DraftSlot,
    ) -> Optional[MenuDraft]:
        """Update a specific slot in a draft.
        
        Args:
            draft_id: Draft ID
            day_date: Date of the slot
            meal_type: Meal type to update
            new_slot: New slot data
            
        Returns:
            Updated MenuDraft or None if not found.
        """
        draft = self._load_draft(draft_id)
        if not draft:
            return None
        
        # Find and update slot
        for day in draft.days:
            if day.date == day_date:
                for i, slot in enumerate(day.slots):
                    if slot.meal_type == meal_type:
                        day.slots[i] = new_slot
                        # Recompute nutrition summary
                        target_calories = draft.nutrition_summary.target_calories
                        draft.compute_nutrition_summary(target_calories)
                        # Save
                        self._save_draft(draft)
                        return draft
        
        return None
    
    def validate_draft(self, draft_id: str) -> Optional[MenuDraft]:
        """Mark a draft as validated.
        
        Args:
            draft_id: Draft ID to validate
            
        Returns:
            Updated MenuDraft or None if not found.
        """
        draft = self._load_draft(draft_id)
        if not draft:
            return None
        
        draft.status = DraftStatus.validated
        draft.validated_at = datetime.now()
        
        self._save_draft(draft)
        logger.info("Draft validated: %s", draft_id)
        
        return draft
    
    def cancel_draft(self, draft_id: str) -> bool:
        """Cancel/delete a draft.
        
        Args:
            draft_id: Draft ID to cancel
            
        Returns:
            True if cancelled, False if not found.
        """
        draft = self._load_draft(draft_id)
        if not draft:
            return False
        
        draft.status = DraftStatus.cancelled
        self._save_draft(draft)
        self._delete_draft_file(draft_id)
        
        logger.info("Draft cancelled: %s", draft_id)
        return True
    
    def push_to_mealie(self, draft_id: str) -> tuple[bool, int, str]:
        """Push a validated draft to Mealie mealplan.
        
        Args:
            draft_id: Draft ID to push
            
        Returns:
            Tuple of (success, count_pushed, message)
        """
        draft = self._load_draft(draft_id)
        if not draft:
            return False, 0, "Draft not found"
        
        if draft.status != DraftStatus.validated:
            # Auto-validate if in draft status
            if draft.status == DraftStatus.draft:
                draft = self.validate_draft(draft_id)
            else:
                return False, 0, f"Cannot push draft with status: {draft.status}"
        
        entries = draft.to_mealie_mealplan_entries()
        
        if not entries:
            return False, 0, "No entries to push"
        
        success_count = 0
        for entry in entries:
            if self.client.create_mealplan(entry):
                success_count += 1
        
        # Update draft status
        if success_count == len(entries):
            draft.pushed_to_mealie_at = datetime.now()
            self._save_draft(draft)
            self.variety_scorer.history.invalidate_cache()  # Invalidate cache after push
            
            msg = f"Successfully pushed {success_count} entries to Mealie"
            logger.info(msg)
            return True, success_count, msg
        else:
            msg = f"Partially pushed: {success_count}/{len(entries)} entries"
            logger.warning(msg)
            return False, success_count, msg
    
    def close(self) -> None:
        """Close resources."""
        self.client.close()
        self.variety_scorer.close()
    
    def __enter__(self) -> "DraftManager":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
