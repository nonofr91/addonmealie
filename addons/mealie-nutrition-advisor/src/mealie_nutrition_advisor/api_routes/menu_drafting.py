"""API routes for menu drafting functionality."""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Security, status
from pydantic import BaseModel, Field

from ..config import NutritionConfig
from ..mealie_sync import MealieClient
from ..menu_drafting.alternatives_finder import AlternativesFinder
from ..menu_drafting.draft_manager import DraftManager
from ..models.menu import MealType
from ..models.menu_draft import DraftSlot, MenuDraft, DraftStatus, AlternativeRecipe
from ..models.seasonality import IngredientSeason, get_current_season

router = APIRouter(prefix="/drafts", tags=["menu_drafting"])

# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

_config: Optional[NutritionConfig] = None
_draft_manager: Optional[DraftManager] = None
_alternatives_finder: Optional[AlternativesFinder] = None
_mealie_client: Optional[MealieClient] = None


def _get_config() -> NutritionConfig:
    global _config
    if _config is None:
        _config = NutritionConfig()
    return _config


def _get_draft_manager() -> DraftManager:
    global _draft_manager
    if _draft_manager is None:
        _draft_manager = DraftManager()
    return _draft_manager


def _get_alternatives_finder() -> AlternativesFinder:
    global _alternatives_finder
    if _alternatives_finder is None:
        _alternatives_finder = AlternativesFinder()
    return _alternatives_finder


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class GenerateDraftRequest(BaseModel):
    week_label: str = Field(..., description="Week label in format YYYY-Www (e.g., 2026-W16)")


class GenerateDraftResponse(BaseModel):
    success: bool
    draft_id: Optional[str] = None
    draft: Optional[dict] = None
    message: str


class DraftResponse(BaseModel):
    success: bool
    draft: Optional[dict] = None
    message: Optional[str] = None


class DraftsListResponse(BaseModel):
    success: bool
    drafts: list[dict]


class AlternativesResponse(BaseModel):
    success: bool
    alternatives: list[dict]
    message: Optional[str] = None


class SwapRequest(BaseModel):
    new_recipe_slug: str = Field(..., description="Slug of the new recipe to use")


class SwapResponse(BaseModel):
    success: bool
    draft: Optional[dict] = None
    message: str


class ValidateResponse(BaseModel):
    success: bool
    draft: Optional[dict] = None
    message: str


class PushResponse(BaseModel):
    success: bool
    pushed_count: int = 0
    message: str


class SeasonalityResponse(BaseModel):
    success: bool
    current_season: str
    calendar_version: str
    calendar_ingredients_count: int


class IngredientSeasonalityResponse(BaseModel):
    success: bool
    ingredient: str
    score: float
    is_peak: bool
    is_available: bool
    current_season: str
    peak_seasons: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=GenerateDraftResponse)
def generate_draft(req: GenerateDraftRequest) -> GenerateDraftResponse:
    """Generate a new menu draft for the given week."""
    config = _get_config()
    if not config.enable_menu_planner:
        raise HTTPException(
            status_code=503,
            detail="Menu planner feature is disabled"
        )
    
    try:
        dm = _get_draft_manager()
        draft = dm.generate_draft(req.week_label)
        
        return GenerateDraftResponse(
            success=True,
            draft_id=draft.draft_id,
            draft=draft.model_dump(),
            message=f"Draft generated for week {req.week_label}"
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate draft: {str(exc)}"
        )


@router.get("/list", response_model=DraftsListResponse)
def list_drafts() -> DraftsListResponse:
    """List all menu drafts."""
    config = _get_config()
    if not config.enable_menu_planner:
        raise HTTPException(
            status_code=503,
            detail="Menu planner feature is disabled"
        )
    
    try:
        dm = _get_draft_manager()
        drafts = dm.list_drafts()
        
        return DraftsListResponse(success=True, drafts=drafts)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list drafts: {str(exc)}"
        )


@router.get("/{draft_id}", response_model=DraftResponse)
def get_draft(draft_id: str) -> DraftResponse:
    """Get a specific menu draft by ID."""
    config = _get_config()
    if not config.enable_menu_planner:
        raise HTTPException(
            status_code=503,
            detail="Menu planner feature is disabled"
        )
    
    try:
        dm = _get_draft_manager()
        draft = dm.get_draft(draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=404,
                detail=f"Draft {draft_id} not found"
            )
        
        return DraftResponse(
            success=True,
            draft=draft.model_dump(),
            message="Draft retrieved"
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get draft: {str(exc)}"
        )


@router.get("/{draft_id}/alternatives", response_model=AlternativesResponse)
def get_alternatives(
    draft_id: str,
    day: str,  # ISO format date
    meal_type: str,  # breakfast, lunch, dinner
) -> AlternativesResponse:
    """Get alternative recipes for a specific slot in a draft."""
    config = _get_config()
    if not config.enable_menu_planner:
        raise HTTPException(
            status_code=503,
            detail="Menu planner feature is disabled"
        )
    
    try:
        # Parse parameters
        try:
            day_date = date.fromisoformat(day)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {day}. Use ISO format (YYYY-MM-DD)."
            )
        
        try:
            mt = MealType(meal_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid meal_type: {meal_type}. Use breakfast, lunch, or dinner."
            )
        
        # Get draft
        dm = _get_draft_manager()
        draft = dm.get_draft(draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=404,
                detail=f"Draft {draft_id} not found"
            )
        
        # Find the slot
        slot = None
        for d in draft.days:
            if d.date == day_date:
                for s in d.slots:
                    if s.meal_type == mt:
                        slot = s
                        break
        
        if not slot:
            raise HTTPException(
                status_code=404,
                detail=f"Slot not found for {day} {meal_type}"
            )
        
        # Get household members present at this meal
        from ..profiles.manager import ProfileManager
        pm = ProfileManager()
        household = pm.household
        
        # Determine present members
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
        day_of_week = day_map.get(day_date.weekday(), DayOfWeek.monday)
        
        present_members = [
            m for m in household.members
            if m.weekly_presence.is_present(day_of_week, mt.value)
        ]
        
        if not present_members:
            return AlternativesResponse(
                success=True,
                alternatives=[],
                message="No members present for this meal"
            )
        
        # Get current draft slugs to exclude
        used_slugs = {s.recipe_slug for d in draft.days for s in d.slots}
        
        # Find alternatives
        af = _get_alternatives_finder()
        alternatives = af.find_alternatives(
            current_recipe_slug=slot.recipe_slug,
            members=present_members,
            meal_type=mt,
            reference_date=day_date,
            exclude_slugs=used_slugs,
            min_score=0.5,
        )
        
        return AlternativesResponse(
            success=True,
            alternatives=[alt.model_dump() for alt in alternatives],
            message=f"Found {len(alternatives)} alternatives"
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alternatives: {str(exc)}"
        )


@router.post("/{draft_id}/swap", response_model=SwapResponse)
def swap_recipe(
    draft_id: str,
    day: str,
    meal_type: str,
    req: SwapRequest,
) -> SwapResponse:
    """Swap a recipe in a draft slot."""
    config = _get_config()
    if not config.enable_menu_planner:
        raise HTTPException(
            status_code=503,
            detail="Menu planner feature is disabled"
        )
    
    try:
        # Parse parameters
        try:
            day_date = date.fromisoformat(day)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format: {day}"
            )
        
        try:
            mt = MealType(meal_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid meal_type: {meal_type}"
            )
        
        # Get draft
        dm = _get_draft_manager()
        draft = dm.get_draft(draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=404,
                detail=f"Draft {draft_id} not found"
            )
        
        # Find current slot
        current_slot = None
        for d in draft.days:
            if d.date == day_date:
                for s in d.slots:
                    if s.meal_type == mt:
                        current_slot = s
                        break
        
        if not current_slot:
            raise HTTPException(
                status_code=404,
                detail=f"Slot not found for {day} {meal_type}"
            )
        
        # Get household members
        from ..profiles.manager import ProfileManager
        pm = ProfileManager()
        household = pm.household
        
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
        day_of_week = day_map.get(day_date.weekday(), DayOfWeek.monday)
        
        present_members = [
            m for m in household.members
            if m.weekly_presence.is_present(day_of_week, mt.value)
        ]
        
        # Perform swap
        af = _get_alternatives_finder()
        new_slot = af.swap_recipe(
            current_slot=current_slot,
            new_recipe_slug=req.new_recipe_slug,
            members=present_members,
            meal_type=mt,
            reference_date=day_date,
        )
        
        if not new_slot:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to swap recipe. Check if {req.new_recipe_slug} exists."
            )
        
        # Update draft
        updated_draft = dm.update_slot(draft_id, day_date, mt, new_slot)
        
        if not updated_draft:
            raise HTTPException(
                status_code=500,
                detail="Failed to update draft"
            )
        
        return SwapResponse(
            success=True,
            draft=updated_draft.model_dump(),
            message=f"Swapped recipe to {new_slot.recipe_name}"
        )
        
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to swap recipe: {str(exc)}"
        )


@router.post("/{draft_id}/validate", response_model=ValidateResponse)
def validate_draft(draft_id: str) -> ValidateResponse:
    """Validate a menu draft."""
    config = _get_config()
    if not config.enable_menu_planner:
        raise HTTPException(
            status_code=503,
            detail="Menu planner feature is disabled"
        )
    
    try:
        dm = _get_draft_manager()
        draft = dm.validate_draft(draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=404,
                detail=f"Draft {draft_id} not found"
            )
        
        return ValidateResponse(
            success=True,
            draft=draft.model_dump(),
            message="Draft validated and ready to push"
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate draft: {str(exc)}"
        )


@router.post("/{draft_id}/push", response_model=PushResponse)
def push_draft(
    draft_id: str,
    auto_validate: bool = True,
) -> PushResponse:
    """Push a validated draft to Mealie mealplan."""
    config = _get_config()
    if not config.enable_menu_planner:
        raise HTTPException(
            status_code=503,
            detail="Menu planner feature is disabled"
        )
    
    try:
        dm = _get_draft_manager()
        
        # Auto-validate if requested
        if auto_validate:
            draft = dm.get_draft(draft_id)
            if draft and draft.status == DraftStatus.draft:
                dm.validate_draft(draft_id)
        
        # Push
        success, count, message = dm.push_to_mealie(draft_id)
        
        return PushResponse(
            success=success,
            pushed_count=count,
            message=message
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to push draft: {str(exc)}"
        )


@router.delete("/{draft_id}")
def delete_draft(draft_id: str) -> dict:
    """Delete/cancel a menu draft."""
    config = _get_config()
    if not config.enable_menu_planner:
        raise HTTPException(
            status_code=503,
            detail="Menu planner feature is disabled"
        )
    
    try:
        dm = _get_draft_manager()
        cancelled = dm.cancel_draft(draft_id)
        
        if not cancelled:
            raise HTTPException(
                status_code=404,
                detail=f"Draft {draft_id} not found"
            )
        
        return {
            "success": True,
            "deleted": draft_id,
            "message": f"Draft {draft_id} cancelled and deleted"
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete draft: {str(exc)}"
        )


# ---------------------------------------------------------------------------
# Seasonality endpoints
# ---------------------------------------------------------------------------

@router.get("/seasonality/current", response_model=SeasonalityResponse)
def get_current_season_info() -> SeasonalityResponse:
    """Get current season information."""
    config = _get_config()
    if not config.enable_seasonality:
        raise HTTPException(
            status_code=503,
            detail="Seasonality feature is disabled"
        )
    
    try:
        from ..planner.variety_scorer import VarietyScorer
        vs = VarietyScorer()
        info = vs.get_season_info()
        vs.close()
        
        return SeasonalityResponse(
            success=True,
            current_season=info["current_season"],
            calendar_version=info["calendar_version"],
            calendar_ingredients_count=info["calendar_ingredients_count"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get season info: {str(exc)}"
        )


@router.get("/seasonality/ingredient/{ingredient}", response_model=IngredientSeasonalityResponse)
def get_ingredient_seasonality(ingredient: str) -> IngredientSeasonalityResponse:
    """Get seasonality information for a specific ingredient."""
    config = _get_config()
    if not config.enable_seasonality:
        raise HTTPException(
            status_code=503,
            detail="Seasonality feature is disabled"
        )
    
    try:
        from ..planner.variety_scorer import VarietyScorer
        vs = VarietyScorer()
        score_info = vs.calendar.get_score(ingredient)
        vs.close()
        
        return IngredientSeasonalityResponse(
            success=True,
            ingredient=score_info.ingredient,
            score=round(score_info.score, 2),
            is_peak=score_info.is_peak,
            is_available=score_info.is_available,
            current_season=score_info.current_season.value,
            peak_seasons=[s.value for s in score_info.ingredient_peak_seasons],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get ingredient seasonality: {str(exc)}"
        )
